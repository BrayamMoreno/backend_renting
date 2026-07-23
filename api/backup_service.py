import os
import json
import gzip
from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from io import StringIO
from django.db.models import Max
from django.contrib.auth.models import User
from .models import (
    ItemHistorial, InventarioItem, Recepcion, Devolucion,
    Marca, TipoProducto, Procesador, Ram, Disco, TipoDisco, Ubicacion, Proveedor, Rol, Permiso
)

BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

def get_last_db_change_info():
    """
    Obtiene la fecha más reciente de modificación o registro en la base de datos
    y el conteo total de registros clave (inventario, usuarios, roles y catálogos)
    para determinar si la BD ha cambiado o requiere backup.
    """
    max_historial = ItemHistorial.objects.aggregate(Max('fecha'))['fecha__max']
    max_inventario = InventarioItem.objects.aggregate(Max('fecha_ingreso'))['fecha_ingreso__max']
    max_recepcion = Recepcion.objects.aggregate(Max('fecha'))['fecha__max']
    max_devolucion = Devolucion.objects.aggregate(Max('fecha_creacion'))['fecha_creacion__max']
    max_user = User.objects.aggregate(Max('date_joined'))['date_joined__max']

    fechas = [f for f in [max_historial, max_inventario, max_recepcion, max_devolucion, max_user] if f is not None]
    
    ultima_fecha_iso = max(fechas).isoformat() if fechas else None
    
    # Conteos de inventario e historial
    count_items = InventarioItem.objects.count()
    count_historial = ItemHistorial.objects.count()
    count_recepciones = Recepcion.objects.count()
    count_devoluciones = Devolucion.objects.count()

    # Conteos de Usuarios, Roles y Permisos
    count_users = User.objects.count()
    count_roles = Rol.objects.count()
    count_permisos = Permiso.objects.count()

    # Conteos de Catálogos
    count_marcas = Marca.objects.count()
    count_tipos = TipoProducto.objects.count()
    count_procesadores = Procesador.objects.count()
    count_ram = Ram.objects.count()
    count_discos = Disco.objects.count()
    count_tipos_disco = TipoDisco.objects.count()
    count_ubicaciones = Ubicacion.objects.count()
    count_proveedores = Proveedor.objects.count()

    catalog_hash = (
        f"U{count_users}_R{count_roles}_P{count_permisos}_"
        f"M{count_marcas}_T{count_tipos}_PR{count_procesadores}_"
        f"RM{count_ram}_D{count_discos}_TD{count_tipos_disco}_"
        f"UB{count_ubicaciones}_PV{count_proveedores}"
    )

    change_key = f"{ultima_fecha_iso}_{count_items}_{count_historial}_{count_recepciones}_{count_devoluciones}_{catalog_hash}"

    return {
        'ultima_fecha': ultima_fecha_iso,
        'count_items': count_items,
        'count_historial': count_historial,
        'count_users': count_users,
        'count_roles': count_roles,
        'catalog_hash': catalog_hash,
        'change_key': change_key
    }

def get_latest_backup_metadata():
    """Retorna los metadatos del backup más reciente si existe."""
    ensure_backup_dir()
    backups = list_backups()
    return backups[0] if backups else None

def is_backup_done_today():
    """
    Retorna True si existe al menos una copia de seguridad generada en la fecha actual (el día de hoy).
    """
    latest = get_latest_backup_metadata()
    if not latest or not latest.get('fecha_creacion'):
        return False
    try:
        latest_dt = datetime.fromisoformat(latest['fecha_creacion'])
        return latest_dt.date() == datetime.now().date()
    except Exception:
        return False


def has_changes_since_last_backup():
    """Retorna True si hay cambios en la base de datos (inventario, usuarios, roles o catálogos) desde la última copia realizada."""
    current_info = get_last_db_change_info()
    latest = get_latest_backup_metadata()
    if not latest:
        return True  # No hay backups previos
    
    last_change_key = latest.get('change_key')
    if current_info['change_key'] != last_change_key:
        return True

    # Verificar si el backup existente se realizó en un día anterior a la fecha de hoy
    # o si el último cambio fue registrado hoy y no hay backup de hoy.
    latest_date_str = latest.get('fecha_creacion', '')
    if latest_date_str:
        try:
            latest_dt = datetime.fromisoformat(latest_date_str)
            now = datetime.now()
            # Si el último backup no es del día de hoy y ocurrieron cambios o actividad
            if latest_dt.date() < now.date() and current_info['ultima_fecha']:
                last_change_dt = datetime.fromisoformat(current_info['ultima_fecha'])
                if last_change_dt.date() == now.date():
                    return True
        except Exception:
            pass

    return False

def create_backup(modo='condicional', usuario=None):
    """
    Genera un respaldo comprimido .json.gz de la base de datos.
    Si modo == 'condicional', solo genera el archivo si se detectan cambios.
    """
    ensure_backup_dir()
    current_change = get_last_db_change_info()
    
    if modo == 'condicional' and not has_changes_since_last_backup():
        latest = get_latest_backup_metadata()
        return {
            'status': 'no_changes',
            'message': 'No se generó respaldo: La base de datos no registra modificaciones desde la última copia de seguridad.',
            'ultimo_backup': latest
        }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{timestamp}_{modo}.json.gz"
    filepath = os.path.join(BACKUP_DIR, filename)

    # Exportar datos usando dumpdata
    buffer = StringIO()
    call_command('dumpdata', 'api', 'auth.user', 'auth.group', indent=2, stdout=buffer)
    raw_data = buffer.getvalue()

    metadata = {
        'filename': filename,
        'fecha_creacion': datetime.now().isoformat(),
        'modo': modo,
        'usuario': usuario.username if usuario and not usuario.is_anonymous else 'Sistema',
        'change_key': current_change['change_key'],
        'ultima_fecha_db': current_change['ultima_fecha'],
        'total_items': current_change['count_items'],
        'total_historial': current_change['count_historial'],
    }

    backup_content = {
        'metadata': metadata,
        'data': json.loads(raw_data)
    }

    with gzip.open(filepath, 'wt', encoding='utf-8') as f:
        json.dump(backup_content, f, ensure_ascii=False)

    file_size_bytes = os.path.getsize(filepath)
    metadata['size_bytes'] = file_size_bytes
    metadata['size_human'] = format_file_size(file_size_bytes)

    # Guardar metadatos en un archivo secundario para lectura rápida
    meta_path = filepath + '.meta'
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        'status': 'created',
        'message': f'Copia de seguridad "{filename}" creada exitosamente.',
        'backup': metadata
    }

def format_file_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def list_backups():
    ensure_backup_dir()
    files = os.listdir(BACKUP_DIR)
    gz_files = [f for f in files if f.endswith('.json.gz')]
    
    result = []
    for gz in gz_files:
        filepath = os.path.join(BACKUP_DIR, gz)
        meta_path = filepath + '.meta'
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    result.append(meta)
                    continue
            except Exception:
                pass
        
        # Fallback si no hay .meta file
        mtime = os.path.getmtime(filepath)
        size = os.path.getsize(filepath)
        result.append({
            'filename': gz,
            'fecha_creacion': datetime.fromtimestamp(mtime).isoformat(),
            'modo': 'manual' if 'manual' in gz else 'condicional',
            'usuario': 'Desconocido',
            'size_bytes': size,
            'size_human': format_file_size(size),
            'change_key': ''
        })

    # Ordenar del más reciente al más antiguo
    result.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)
    return result

def get_backup_file_path(filename):
    ensure_backup_dir()
    # Prevenir path traversal
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(BACKUP_DIR, safe_filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return filepath
    return None

def delete_backup(filename):
    filepath = get_backup_file_path(filename)
    if not filepath:
        return False
    
    os.remove(filepath)
    meta_path = filepath + '.meta'
    if os.path.exists(meta_path):
        os.remove(meta_path)
    return True
