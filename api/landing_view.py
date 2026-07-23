import sys
import django
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.db import connection

def landing_view(request):
    """
    Vista principal que sirve la Landing Page interactiva en la raíz (/) del Backend API.
    """
    db_connected = True
    db_engine = connection.vendor
    try:
        connection.ensure_connection()
    except Exception:
        db_connected = False

    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    django_ver = django.get_version()
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Renting Manager - Backend API</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col justify-between selection:bg-orange-500 selection:text-white">

    <!-- Header / Navbar -->
    <header class="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-white shadow-lg shadow-orange-500/30">
                    <span class="material-icons">memory</span>
                </div>
                <div>
                    <h1 class="text-lg font-black tracking-tight text-white">Renting Manager API</h1>
                    <p class="text-[10px] text-orange-400 font-bold uppercase tracking-widest leading-none">Servicio Backend Operacional</p>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <span class="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    API Online
                </span>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto px-6 py-12 flex-1 w-full space-y-10">

        <!-- Hero Banner -->
        <div class="relative overflow-hidden rounded-3xl p-8 md:p-12 border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 shadow-2xl">
            <div class="absolute -right-20 -bottom-20 w-80 h-80 bg-orange-500/10 rounded-full blur-3xl pointer-events-none"></div>
            
            <div class="relative z-10 max-w-2xl space-y-4">
                <span class="px-3 py-1 rounded-lg text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30 inline-block uppercase tracking-wider">
                    Plataforma de Trazabilidad IT
                </span>
                <h2 class="text-3xl md:text-5xl font-black text-white leading-tight">
                    API Rest & Gestión de Inventarios
                </h2>
                <p class="text-slate-400 text-sm md:text-base leading-relaxed">
                    El servicio backend se encuentra desplegado y procesando solicitudes. Accede a la documentación interactiva OpenAPI/Swagger o al panel de administración del sistema.
                </p>
            </div>
        </div>

        <!-- Quick Access Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <!-- Swagger UI Card -->
            <a href="/api/docs/" class="group p-6 rounded-3xl bg-slate-950 border border-slate-800 hover:border-orange-500/50 transition-all duration-300 shadow-xl hover:-translate-y-1">
                <div class="w-12 h-12 rounded-2xl bg-orange-500/10 text-orange-400 flex items-center justify-center mb-4 group-hover:bg-orange-500 group-hover:text-white transition-colors shadow-lg">
                    <span class="material-icons">auto_stories</span>
                </div>
                <h3 class="text-lg font-black text-white mb-1 group-hover:text-orange-400 transition-colors">Documentación Swagger</h3>
                <p class="text-xs text-slate-400 leading-relaxed mb-4">Explora todos los endpoints REST, esquemas de solicitud y payloads interactivos.</p>
                <span class="text-xs font-bold text-orange-400 flex items-center gap-1">
                    Ver OpenAPI Docs <span class="material-icons text-sm">arrow_forward</span>
                </span>
            </a>

            <!-- Django Admin Card -->
            <a href="/admin/" class="group p-6 rounded-3xl bg-slate-950 border border-slate-800 hover:border-amber-500/50 transition-all duration-300 shadow-xl hover:-translate-y-1">
                <div class="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-4 group-hover:bg-amber-500 group-hover:text-white transition-colors shadow-lg">
                    <span class="material-icons">admin_panel_settings</span>
                </div>
                <h3 class="text-lg font-black text-white mb-1 group-hover:text-amber-400 transition-colors">Panel Django Admin</h3>
                <p class="text-xs text-slate-400 leading-relaxed mb-4">Administración directa de modelos, usuarios, permisos y configuración de BD.</p>
                <span class="text-xs font-bold text-amber-400 flex items-center gap-1">
                    Acceder a Django Admin <span class="material-icons text-sm">arrow_forward</span>
                </span>
            </a>

            <!-- Health Check Card -->
            <a href="/api/health/" class="group p-6 rounded-3xl bg-slate-950 border border-slate-800 hover:border-emerald-500/50 transition-all duration-300 shadow-xl hover:-translate-y-1">
                <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4 group-hover:bg-emerald-500 group-hover:text-white transition-colors shadow-lg">
                    <span class="material-icons">health_and_safety</span>
                </div>
                <h3 class="text-lg font-black text-white mb-1 group-hover:text-emerald-400 transition-colors">Chequeo de Salud (Health)</h3>
                <p class="text-xs text-slate-400 leading-relaxed mb-4">Monitoreo de estado de conexión con la base de datos y respuesta JSON.</p>
                <span class="text-xs font-bold text-emerald-400 flex items-center gap-1">
                    Ver JSON Health <span class="material-icons text-sm">arrow_forward</span>
                </span>
            </a>

        </div>

        <!-- System Stats / Environment Status -->
        <div class="p-6 md:p-8 rounded-3xl bg-slate-950/60 border border-slate-800/80">
            <h4 class="text-xs font-black text-slate-500 uppercase tracking-widest mb-6">Métricas de Entorno & Servidor</h4>
            
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                    <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Base de Datos</span>
                    <span class="text-sm font-bold flex items-center gap-1.5 {'text-emerald-400' if db_connected else 'text-red-400'}">
                        <span class="w-2 h-2 rounded-full {'bg-emerald-400' if db_connected else 'bg-red-400'}"></span>
                        {db_engine.upper() if db_connected else 'Desconectada'}
                    </span>
                </div>

                <div>
                    <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Versión Django</span>
                    <span class="text-sm font-bold text-slate-200">v{django_ver}</span>
                </div>

                <div>
                    <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Versión Python</span>
                    <span class="text-sm font-bold text-slate-200">v{python_ver}</span>
                </div>

                <div>
                    <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Hora del Servidor</span>
                    <span class="text-sm font-mono font-bold text-orange-400">{server_time}</span>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        <p>Renting Manager &bull; Sistema de Trazabilidad de Activos IT &bull; {datetime.now().year}</p>
    </footer>

</body>
</html>"""
    return HttpResponse(html_content)


def health_check_view(request):
    """
    Endpoint JSON de chequeo de salud para sistemas de monitoreo y balanceadores.
    """
    db_connected = True
    try:
        connection.ensure_connection()
    except Exception as e:
        db_connected = False

    status_code = 200 if db_connected else 500
    return JsonResponse({
        'status': 'healthy' if db_connected else 'unhealthy',
        'database': {
            'connected': db_connected,
            'vendor': connection.vendor
        },
        'system': {
            'django_version': django.get_version(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'server_time': datetime.now().isoformat()
        }
    }, status=status_code)
