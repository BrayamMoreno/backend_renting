import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from api.models import (
    EquipoEstado, Rol, Profile, Marca, TipoProducto,
    TipoDisco, Ram, Disco, Ubicacion, PuntoAlistamiento
)

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

        if created or not user.password or not user.has_usable_password():
            user.set_password(admin_password)
            user.email = admin_email
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Contraseña asignada/actualizada para Usuario Administrador "{admin_username}".'))
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

        # 5. Poblar otros Catálogos (Marcas, Tipos de Producto, Discos, RAM, Ubicaciones y Checklist)
        self.stdout.write('\nPre-poblando catálogos por defecto...')

        # Marcas
        marcas = ['Lenovo', 'HP', 'Dell', 'Apple', 'Asus', 'Acer', 'Samsung', 'Toshiba']
        for m in marcas:
            Marca.objects.get_or_create(nombre=m)

        # Tipos de Producto
        tipos_prod = [
            {'nombre': 'Portátil', 'requiere_alistamiento': True, 'es_periferico': False},
            {'nombre': 'Computador de Escritorio', 'requiere_alistamiento': True, 'es_periferico': False},
            {'nombre': 'Servidor', 'requiere_alistamiento': True, 'es_periferico': False},
            {'nombre': 'Monitor', 'requiere_alistamiento': False, 'es_periferico': True},
            {'nombre': 'Teclado', 'requiere_alistamiento': False, 'es_periferico': True},
            {'nombre': 'Mouse', 'requiere_alistamiento': False, 'es_periferico': True},
            {'nombre': 'Cargador', 'requiere_alistamiento': False, 'es_periferico': True},
        ]
        for tp in tipos_prod:
            TipoProducto.objects.get_or_create(
                nombre=tp['nombre'],
                defaults={
                    'requiere_alistamiento': tp['requiere_alistamiento'],
                    'es_periferico': tp['es_periferico']
                }
            )

        # Tipos de Disco
        tipos_disco = ['HDD', 'SSD (SATA)', 'SSD (NVMe / M.2)']
        for td in tipos_disco:
            TipoDisco.objects.get_or_create(nombre=td)

        # Disco (Capacidades)
        discos = ['128 GB', '240 GB', '256 GB', '480 GB', '512 GB', '1 TB', '2 TB']
        for d in discos:
            Disco.objects.get_or_create(nombre=d)

        # Ram (Capacidades)
        rams = ['4 GB', '8 GB', '12 GB', '16 GB', '32 GB', '64 GB']
        for r in rams:
            Ram.objects.get_or_create(nombre=r)

        # Ubicaciones
        ubicaciones = ['Bodega Principal', 'Bodega de Alistamiento', 'Oficina Central', 'Soporte Técnico', 'En Tránsito', 'Cliente / Rentado']
        for u in ubicaciones:
            Ubicacion.objects.get_or_create(nombre=u)

        # Puntos de Alistamiento
        puntos_checklist = [
            {'nombre': 'Limpieza física externa del equipo', 'orden': 1, 'requiere_evidencia': False},
            {'nombre': 'Verificación de encendido y BIOS', 'orden': 2, 'requiere_evidencia': False},
            {'nombre': 'Prueba de pantalla y teclado', 'orden': 3, 'requiere_evidencia': False},
            {'nombre': 'Diagnóstico de Disco Duro / SSD (Salud)', 'orden': 4, 'requiere_evidencia': True},
            {'nombre': 'Instalación de Sistema Operativo y Drivers', 'orden': 5, 'requiere_evidencia': False},
            {'nombre': 'Verificación de RAM y Procesador', 'orden': 6, 'requiere_evidencia': False},
            {'nombre': 'Prueba de batería y cargador', 'orden': 7, 'requiere_evidencia': False},
            {'nombre': 'Limpieza final y empaque', 'orden': 8, 'requiere_evidencia': True},
        ]
        for p in puntos_checklist:
            PuntoAlistamiento.objects.get_or_create(
                nombre=p['nombre'],
                defaults={
                    'orden': p['orden'],
                    'requiere_evidencia': p['requiere_evidencia']
                }
            )

        self.stdout.write(self.style.SUCCESS('✓ Catálogos de Marcas, Tipos, Discos, RAM, Ubicaciones y Checklist poblados.'))

        self.stdout.write(self.style.SUCCESS('\n==================================================='))
        self.stdout.write(self.style.SUCCESS('  Base de Datos Inicializada Correctamente para Despliegue  '))
        self.stdout.write(self.style.SUCCESS(f'  Admin Username: {admin_username}'))
        self.stdout.write(self.style.SUCCESS(f'  Admin Email   : {admin_email}'))
        self.stdout.write(self.style.SUCCESS('===================================================\n'))
