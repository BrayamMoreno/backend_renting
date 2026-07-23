from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from .utils import normalize_email, find_user_by_email
from .auth_serializers import RegisterSerializer, UserProfileSerializer
from .models import Profile

class GmailAuthTestCase(TestCase):
    def test_normalize_email(self):
        # Test case insensitivity
        self.assertEqual(normalize_email("Test.User@gmail.com"), "testuser@gmail.com")
        self.assertEqual(normalize_email("  TEST.user@GOOGLEMAIL.COM  "), "testuser@gmail.com")
        
        # Test Gmail specific dots and subaddressing
        self.assertEqual(normalize_email("john.doe+tag@gmail.com"), "johndoe@gmail.com")
        self.assertEqual(normalize_email("j.o.h.n.d.o.e+abc+def@googlemail.com"), "johndoe@gmail.com")
        
        # Test non-Gmail domains (should keep dots and subaddressing, only case/whitespace normalized)
        self.assertEqual(normalize_email("john.doe+tag@cdaautomas.com.co"), "john.doe+tag@cdaautomas.com.co")
        self.assertEqual(normalize_email("  A.B+C@example.com "), "a.b+c@example.com")
        
        # Test empty/None values
        self.assertEqual(normalize_email(None), "")
        self.assertEqual(normalize_email(""), "")

    def test_find_user_by_email(self):
        # Create a test user with a specific casing and dots
        user1 = User.objects.create_user(
            username="john_doe",
            email="John.Doe+testing@gmail.com",
            password="password123"
        )
        
        # 1. Exact match
        self.assertEqual(find_user_by_email("John.Doe+testing@gmail.com"), user1)
        
        # 2. Case mismatch
        self.assertEqual(find_user_by_email("john.doe+testing@gmail.com"), user1)
        
        # 3. Dots mismatch (Gmail canonical match)
        self.assertEqual(find_user_by_email("johndoe@gmail.com"), user1)
        self.assertEqual(find_user_by_email("j.o.h.n.d.o.e@googlemail.com"), user1)
        self.assertEqual(find_user_by_email("JohnDoe+other@gmail.com"), user1)
        
        # 4. Search for non-existent user
        self.assertIsNone(find_user_by_email("different@gmail.com"))
        
        # 5. Search with non-gmail email that has similar letters but dots are significant
        user2 = User.objects.create_user(
            username="company_user",
            email="john.doe@cdaautomas.com.co",
            password="password123"
        )
        # Search for johndoe@cdaautomas.com.co should NOT return user2 since dots are significant for non-gmail domains
        self.assertIsNone(find_user_by_email("johndoe@cdaautomas.com.co"))
        # Search for exact or case-insensitive should return it
        self.assertEqual(find_user_by_email("JOHN.DOE@cdaautomas.com.co"), user2)

    def test_serializers_validation(self):
        # Create an initial user
        User.objects.create_user(
            username="existing_user",
            email="existing.user@gmail.com",
            password="password123"
        )
        
        # Test RegisterSerializer prevents duplicate email (case-insensitive and Gmail canonical)
        # Case mismatch
        serializer1 = RegisterSerializer(data={
            "username": "new_user1",
            "email": "Existing.User@gmail.com",
            "password": "password123"
        })
        self.assertFalse(serializer1.is_valid())
        self.assertIn("email", serializer1.errors)
        
        # Gmail canonical mismatch (dots and tags)
        serializer2 = RegisterSerializer(data={
            "username": "new_user2",
            "email": "existinguser+new@googlemail.com",
            "password": "password123"
        })
        self.assertFalse(serializer2.is_valid())
        self.assertIn("email", serializer2.errors)
        
        # Valid user
        serializer3 = RegisterSerializer(data={
            "username": "new_user3",
            "email": "other.user@gmail.com",
            "password": "password123"
        })
        self.assertTrue(serializer3.is_valid())
        
        # Test UserProfileSerializer prevents duplicate email on update
        user = User.objects.create_user(
            username="profile_user",
            email="profile.user@gmail.com",
            password="password123"
        )
        
        # Valid update (updating own email to same normalized form)
        profile_serializer = UserProfileSerializer(instance=user, data={
            "email": "profileuser@gmail.com"  # Same normalized email
        }, partial=True)
        self.assertTrue(profile_serializer.is_valid())
        
        # Invalid update (updating to someone else's email)
        profile_serializer2 = UserProfileSerializer(instance=user, data={
            "email": "existinguser@gmail.com"  # Belongs to "existing_user"
        }, partial=True)
        self.assertFalse(profile_serializer2.is_valid())
        self.assertIn("email", profile_serializer2.errors)

    def test_replacement_rules(self):
        from .serializers import InventarioItemSerializer
        from .models import TipoProducto, InventarioItem, Marca, EquipoEstado

        # Create TipoProductos (one computer, one peripheral)
        pc_type, _ = TipoProducto.objects.get_or_create(nombre="LAPTOP", defaults={"es_periferico": False})
        periph_type, _ = TipoProducto.objects.get_or_create(nombre="MOUSE", defaults={"es_periferico": True})

        marca, _ = Marca.objects.get_or_create(nombre="HP")
        estado, _ = EquipoEstado.objects.get_or_create(nombre="RECIBIDO")

        # Create an existing peripheral item in DB
        old_periph = InventarioItem.objects.create(
            serial="OLDMOUSE123",
            tipo_producto=periph_type,
            marca=marca,
            modelo="Classic",
            estado=estado
        )

        # Create an existing laptop item in DB
        old_laptop = InventarioItem.objects.create(
            serial="OLDLAPTOP123",
            tipo_producto=pc_type,
            marca=marca,
            modelo="EliteBook",
            estado=estado
        )

        # 1. Mismatch: Computer trying to replace a Peripheral
        serializer1 = InventarioItemSerializer(data={
            "serial": "NEWLAPTOP123",
            "tipo_producto": pc_type.id,
            "marca": marca.id,
            "modelo": "Spectre",
            "estado": estado.nombre,
            "es_cambio": True,
            "cambio_por": "OLDMOUSE123"
        })
        self.assertFalse(serializer1.is_valid())
        self.assertIn("cambio_por", serializer1.errors)

        # 2. Mismatch: Peripheral trying to replace a Computer
        serializer2 = InventarioItemSerializer(data={
            "serial": "NEWMOUSE123",
            "tipo_producto": periph_type.id,
            "marca": marca.id,
            "modelo": "Wireless",
            "estado": estado.nombre,
            "es_cambio": True,
            "cambio_por": "OLDLAPTOP123"
        })
        self.assertFalse(serializer2.is_valid())
        self.assertIn("cambio_por", serializer2.errors)

        # 3. Valid: Computer replacing a Computer
        serializer3 = InventarioItemSerializer(data={
            "serial": "NEWLAPTOP456",
            "tipo_producto": pc_type.id,
            "marca": marca.id,
            "modelo": "Spectre",
            "estado": estado.nombre,
            "es_cambio": True,
            "cambio_por": "OLDLAPTOP123"
        })
        self.assertTrue(serializer3.is_valid())

        # 4. Valid: Peripheral replacing a Peripheral
        serializer4 = InventarioItemSerializer(data={
            "serial": "NEWMOUSE456",
            "tipo_producto": periph_type.id,
            "marca": marca.id,
            "modelo": "Wireless",
            "estado": estado.nombre,
            "es_cambio": True,
            "cambio_por": "OLDMOUSE123"
        })
        self.assertTrue(serializer4.is_valid())


class BackupTestCase(TestCase):
    def test_conditional_backup_service(self):
        from . import backup_service
        # Generate initial backup
        res1 = backup_service.create_backup(modo='condicional')
        self.assertEqual(res1['status'], 'created')
        
        # Second call without changes should return no_changes
        res2 = backup_service.create_backup(modo='condicional')
        self.assertEqual(res2['status'], 'no_changes')

        # Forced backup should create even without changes
        res3 = backup_service.create_backup(modo='manual')
        self.assertEqual(res3['status'], 'created')

        # List backups should return backups
        backups = backup_service.list_backups()
        self.assertGreaterEqual(len(backups), 2)


