import os
from django.core.management.base import BaseCommand
from api.models import Permiso, Rol

class Command(BaseCommand):
    help = 'Inicializa los permisos y roles por defecto del sistema'

    def handle(self, *args, **options):
        # Definición de todos los permisos requeridos
        permisos_def = {
            'ver_dashboard': 'Permite visualizar el panel de estadísticas y dashboard general.',
            'gestionar_inventario': 'Permite realizar ingresos y alistamientos de equipos.',
            'ver_inventario': 'Permite buscar y visualizar el listado general de equipos en inventario.',
            'generar_devolucion': 'Permite crear solicitudes de devoluciones de equipos.',
            'aprobar_devolucion': 'Permite realizar la aprobación interna de lotes pendientes.',
            'confirmar_devolucion': 'Permite al proveedor validar y confirmar la recepción de lotes aprobados.',
            'gestionar_catalogos': 'Permite configurar marcas, modelos, procesadores, etc.',
            'gestionar_usuarios': 'Permite administrar perfiles de usuario, roles y asignaciones.'
        }

        permisos_creados = {}
        for nombre, desc in permisos_def.items():
            permiso, created = Permiso.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Permiso creado: {nombre}'))
            else:
                # Actualizar descripción en caso de cambios
                permiso.descripcion = desc
                permiso.save()
            permisos_creados[nombre] = permiso

        # Roles y sus asignaciones
        # Matriz actualizada:
        # Administrador: Todos
        # Personal Automas: ver_dashboard, gestionar_inventario, ver_inventario, aprobar_devolucion
        # Personal D47G operador: ver_inventario, generar_devolucion (NO ver_dashboard)
        # D47G proveedor: confirmar_devolucion (NO ver_dashboard)
        roles_def = {
            'administrador': [
                'ver_dashboard', 'gestionar_inventario', 'ver_inventario',
                'generar_devolucion', 'aprobar_devolucion', 'confirmar_devolucion',
                'gestionar_catalogos', 'gestionar_usuarios'
            ],
            'Personal Automas': [
                'ver_dashboard', 'gestionar_inventario', 'ver_inventario', 'aprobar_devolucion'
            ],
            'Personal D47G operador': [
                'ver_inventario', 'generar_devolucion'
            ],
            'D47G proveedor': [
                'confirmar_devolucion'
            ]
        }

        for nombre_rol, lista_perms in roles_def.items():
            rol, created = Rol.objects.get_or_create(nombre=nombre_rol)
            
            # Asignar permisos
            rol_permisos = [permisos_creados[p] for p in lista_perms]
            rol.permisos.set(rol_permisos)
            rol.save()
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Rol creado: {nombre_rol}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Rol actualizado: {nombre_rol}'))
