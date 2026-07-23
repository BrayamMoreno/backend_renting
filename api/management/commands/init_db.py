import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from api.models import EquipoEstado, Rol, Profile

class Command(BaseCommand):
    help = 'Inicializa la base de datos para despliegue: estados por defecto, matriz de roles, catálogos y usuario administrador'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Iniciando Configuración de Despliegue de Base de Datos ==='))

        # 1. Crear Estados por defecto en EquipoEstado
        estados_def = [
            ('RECIBIDO', 'Recibido'),
            ('ALISTAMIENTO', 'Alistamiento'),
            ('DISPONIBLE', 'Disponible'),
            ('ENTREGADO', 'Entregado'),
            ('EN_ESPERA_DEVOLUCION', 'En Espera de Devolución'),
            ('PENDIENTE_DEVOLUCION', 'Pendiente Confirmación Proveedor'),
            ('DEVUELTO', 'Devuelto'),
            ('ALMACENADO', 'Almacenado'),
            ('DADO_DE_BAJA', 'Dado de Baja'),
        ]

        for nombre, desc in estados_def:
            estado, created = EquipoEstado.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Estado creado: {nombre}'))
            else:
                self.stdout.write(f'  Estado existente: {nombre}')

        # 2. Inicializar Roles y Permisos mediante setup_roles
        self.stdout.write('\nConfigurando Matriz de Roles y Permisos...')
        try:
            call_command('setup_roles')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Aviso ejecutando setup_roles: {e}'))

        # 3. Crear / Actualizar Usuario Administrador
        self.stdout.write('\nCreando Usuario Administrador por Defecto...')
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cdaautomas.com.co')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin123456!')

        rol_admin = Rol.objects.filter(nombre='administrador').first()

        user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'first_name': 'Administrador',
                'last_name': 'Principal',
                'is_staff': True,
                'is_superuser': True,
            }
        )

        if created:
            user.set_password(admin_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Usuario Administrador "{admin_username}" creado exitosamente.'))
        else:
            user.email = admin_email
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(f'  Usuario Administrador "{admin_username}" actualizado.')

        # Garantizar perfil y rol
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'ADMIN', 'is_approved': True}
        )
        profile.role = 'ADMIN'
        profile.is_approved = True
        if rol_admin:
            profile.rol_custom = rol_admin
        profile.save()

        # 4. Poblar Catálogo de Procesadores si la semilla existe
        try:
            call_command('seed_intel_processors')
            self.stdout.write(self.style.SUCCESS('✓ Catálogo de Procesadores Intel poblado.'))
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS('\n==================================================='))
        self.stdout.write(self.style.SUCCESS('  Base de Datos Inicializada Correctamente para Despliegue  '))
        self.stdout.write(self.style.SUCCESS(f'  Admin Username: {admin_username}'))
        self.stdout.write(self.style.SUCCESS(f'  Admin Email   : {admin_email}'))
        self.stdout.write(self.style.SUCCESS('===================================================\n'))
