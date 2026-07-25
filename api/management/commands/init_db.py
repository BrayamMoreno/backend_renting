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
                self.stdout.write(self.style.SUCCESS(f'[OK] Estado creado: {nombre}'))
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

        user.set_password(admin_password)
        user.email = admin_email
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f'[OK] Contraseña asignada/actualizada para Usuario Administrador "{admin_username}".'))

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
            self.stdout.write(self.style.SUCCESS('[OK] Catálogo de Procesadores Intel poblado.'))
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

        # Puntos de Alistamiento (Checklist)
        puntos_alistamiento = [
            {'nombre': 'Inspección física y limpieza del equipo', 'requiere_evidencia': False, 'orden': 1},
            {'nombre': 'Verificación de encendido y puertos (USB, HDMI, etc.)', 'requiere_evidencia': False, 'orden': 2},
            {'nombre': 'Prueba de batería y cargador', 'requiere_evidencia': False, 'orden': 3},
            {'nombre': 'Instalación y configuración del Sistema Operativo', 'requiere_evidencia': False, 'orden': 4},
            {'nombre': 'Instalación de controladores (Drivers)', 'requiere_evidencia': False, 'orden': 5},
            {'nombre': 'Instalación de software base y antivirus', 'requiere_evidencia': False, 'orden': 6},
            {'nombre': 'Prueba de pantalla, teclado y mouse/touchpad', 'requiere_evidencia': False, 'orden': 7},
            {'nombre': 'Prueba de conectividad (Wi-Fi y Ethernet)', 'requiere_evidencia': False, 'orden': 8},
            {'nombre': 'Prueba de audio, micrófono y cámara web', 'requiere_evidencia': False, 'orden': 9},
            {'nombre': 'Verificación de especificaciones (CPU, RAM, Disco)', 'requiere_evidencia': True, 'orden': 10},
            {'nombre': 'Etiquetado de inventario / Placa de activo', 'requiere_evidencia': True, 'orden': 11},
        ]
        for p in puntos_alistamiento:
            PuntoAlistamiento.objects.get_or_create(
                nombre=p['nombre'],
                defaults={
                    'requiere_evidencia': p['requiere_evidencia'],
                    'orden': p['orden'],
                    'activo': True
                }
            )

        # Ubicaciones por defecto (Jerárquicas Multinivel: Padre -> Hijo -> Nieto)
        def crear_ubicaciones_rec(nodos, padre=None):
            for node in nodos:
                if isinstance(node, str):
                    Ubicacion.objects.get_or_create(nombre=node, padre=padre)
                elif isinstance(node, dict):
                    nombre = node.get('nombre')
                    hijos = node.get('hijos', [])
                    obj, _ = Ubicacion.objects.get_or_create(nombre=nombre, padre=padre)
                    if hijos:
                        crear_ubicaciones_rec(hijos, padre=obj)

        ubicaciones_def = [
            {
                'nombre': 'Bogota',
                'hijos': [
                    {
                        'nombre': 'Soluciones',
                        'hijos': ['Piso 4', 'Piso 5']
                    },
                    'Bodega Principal',
                    'Taller de Servicio Técnico'
                ]
            },
            {
                'nombre': 'Sede Operativa',
                'hijos': ['Bodega de Recepción', 'Zona de Alistamiento']
            }
        ]
        crear_ubicaciones_rec(ubicaciones_def)

        self.stdout.write(self.style.SUCCESS('[OK] Catálogos de Marcas, Tipos, Discos, RAM, Ubicaciones y Puntos de Alistamiento poblados.'))

        self.stdout.write(self.style.SUCCESS('\n==================================================='))
        self.stdout.write(self.style.SUCCESS('  Base de Datos Inicializada Correctamente para Despliegue  '))
        self.stdout.write(self.style.SUCCESS(f'  Admin Username: {admin_username}'))
        self.stdout.write(self.style.SUCCESS(f'  Admin Email   : {admin_email}'))
        self.stdout.write(self.style.SUCCESS('===================================================\n'))
