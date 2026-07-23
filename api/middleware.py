from django.http import JsonResponse
from .backup_service import is_backup_done_today

class DailyBackupRequiredMiddleware:
    """
    Middleware que requiere una copia de seguridad del día de hoy únicamente
    para modificar configuraciones del sistema (Usuarios, Roles y Catálogos).
    Las operaciones de Inventario (ingresos, alistamientos, devoluciones, bajas)
    pueden modificarse libremente sin requerir backup previo.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Permitir solicitudes de solo lectura
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return self.get_response(request)

        path = request.path_info.lower()

        # 2. Rutas exentas de la restricción de backup diario:
        # - Operaciones del inventario operativo
        # - Administración de backups
        # - Autenticación y sistema admin
        EXEMPT_PATHS = (
            '/api/inventario/',
            '/api/recepciones/',
            '/api/alistamientos/',
            '/api/devoluciones/',
            '/api/bajas/',
            '/api/entregadores/',
            '/api/alertas/',
            '/api/puntos-alistamiento/',
            '/api/backups/',
            '/api/auth/',
            '/api/login/',
            '/api/token/',
            '/admin/',
        )

        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        # 3. Para cualquier modificación en Usuarios, Roles o Catálogos, verificar backup diario
        if not is_backup_done_today():
            return JsonResponse(
                {
                    'detail': 'Acción bloqueada: Para modificar datos de la configuración del sistema (Usuarios, Roles o Catálogos), se requiere haber realizado una copia de seguridad para el día de hoy. Por favor diríjase al módulo "Copias de Seguridad" y genere el respaldo diario para continuar.',
                    'code': 'BACKUP_REQUIRED_TODAY'
                },
                status=403
            )

        return self.get_response(request)
