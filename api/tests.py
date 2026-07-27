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

    def test_peripheral_pending_return_not_reassigned_on_alistamiento(self):
        from .models import TipoProducto, InventarioItem, Marca, EquipoEstado
        from django.contrib.auth.models import User
        from rest_framework.test import APIRequestFactory
        from .views import AlistamientoViewSet

        pc_type, _ = TipoProducto.objects.get_or_create(nombre="LAPTOP", defaults={"es_periferico": False})
        periph_type, _ = TipoProducto.objects.get_or_create(nombre="MOUSE", defaults={"es_periferico": True})
        marca, _ = Marca.objects.get_or_create(nombre="DELL")
        
        est_entregado, _ = EquipoEstado.objects.get_or_create(nombre="ENTREGADO")
        est_espera, _ = EquipoEstado.objects.get_or_create(nombre="EN_ESPERA_DEVOLUCION")
        est_recibido, _ = EquipoEstado.objects.get_or_create(nombre="RECIBIDO")

        tecnico_old = User.objects.create_user(username="tecnico_old", password="pass")
        tecnico_new = User.objects.create_user(username="tecnico_new", password="pass")

        # Create old laptop (Item #100)
        old_laptop = InventarioItem.objects.create(
            item=100,
            serial="LAPTOP-OLD-100",
            tipo_producto=pc_type,
            marca=marca,
            modelo="Latitude",
            estado=est_entregado
        )

        # Create peripheral in EN_ESPERA_DEVOLUCION associated to old_laptop
        periph_pending = InventarioItem.objects.create(
            item=101,
            serial="MOUSE-PENDING-101",
            tipo_producto=periph_type,
            marca=marca,
            modelo="Wireless",
            equipo_asociado=100,
            estado=est_espera,
            responsable_devolucion=tecnico_old
        )

        # Create peripheral ACTIVE (ENTREGADO) associated to old_laptop
        periph_active = InventarioItem.objects.create(
            item=102,
            serial="MOUSE-ACTIVE-102",
            tipo_producto=periph_type,
            marca=marca,
            modelo="USB",
            equipo_asociado=100,
            estado=est_entregado,
            responsable_devolucion=None
        )

        # Create new replacement laptop (Item #200)
        new_laptop = InventarioItem.objects.create(
            item=200,
            serial="LAPTOP-NEW-200",
            tipo_producto=pc_type,
            marca=marca,
            modelo="Latitude New",
            estado=est_recibido,
            es_cambio=True,
            cambio_por="100"
        )

        # Perform Alistamiento on new_laptop with tecnico_new
        alistamiento_data = {
            "inventario_item": new_laptop.id,
            "tecnico": tecnico_new.id,
            "foto_tecnico": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "respuestas": {}
        }
        
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.post('/api/alistamientos/', alistamiento_data, format='json')
        force_authenticate(request, user=tecnico_new)
        view = AlistamientoViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        # Refresh from DB
        periph_pending.refresh_from_db()
        periph_active.refresh_from_db()

        # Check pending peripheral: equipo_asociado should remain 100, responsable_devolucion should remain tecnico_old
        self.assertEqual(periph_pending.equipo_asociado, 100)
        self.assertEqual(periph_pending.responsable_devolucion, tecnico_old)

        # Check active peripheral: equipo_asociado should be updated to 200, responsable_devolucion should be tecnico_new
        self.assertEqual(periph_active.equipo_asociado, 200)
        self.assertEqual(periph_active.responsable_devolucion, tecnico_new)

    def test_update_peripheral_whose_equipment_is_pending_devolucion(self):
        from .models import TipoProducto, Marca, EquipoEstado, InventarioItem, Devolucion
        from rest_framework.test import APIRequestFactory, force_authenticate
        from .views import InventarioItemViewSet

        pc_type, _ = TipoProducto.objects.get_or_create(nombre="PORTATIL", defaults={"es_periferico": False})
        periph_type, _ = TipoProducto.objects.get_or_create(nombre="MOUSE", defaults={"es_periferico": True})
        marca, _ = Marca.objects.get_or_create(nombre="DELL")
        est_pending, _ = EquipoEstado.objects.get_or_create(nombre="PENDIENTE_DEVOLUCION")

        dev = Devolucion.objects.create(estado="PENDIENTE")

        laptop = InventarioItem.objects.create(
            item=500,
            serial="LAPTOP-500",
            tipo_producto=pc_type,
            marca=marca,
            modelo="Latitude 500",
            estado=est_pending
        )

        peripheral = InventarioItem.objects.create(
            item=501,
            serial="MOUSE-501",
            tipo_producto=periph_type,
            marca=marca,
            modelo="Mouse 501",
            equipo_asociado=500,
            estado=est_pending
        )

        user = User.objects.create_user(username="test_dev_user", password="pass")
        factory = APIRequestFactory()
        request = factory.patch(f'/api/inventario/{peripheral.id}/', {
            'estado': 'PENDIENTE_DEVOLUCION',
            'comentario_devolucion': 'Devolucion de mouse',
            'devolucion': dev.id
        }, format='json')
        force_authenticate(request, user=user)
        view = InventarioItemViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=peripheral.id)
        self.assertEqual(response.status_code, 200)


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


