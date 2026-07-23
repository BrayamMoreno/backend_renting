import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def enviar_correo_baja_equipo(item):
    if not item.tipo_producto:
        logger.info(f"El equipo {item.serial} no tiene tipo de producto configurado. No se envía correo de baja.")
        return

    # Avoid circular import at module level
    from .models import ConfiguracionEmailBaja

    configs = ConfiguracionEmailBaja.objects.filter(tipos_producto=item.tipo_producto).distinct()
    if not configs.exists():
        logger.info(f"No hay configuración de correo de baja para el tipo de producto: {item.tipo_producto.nombre}")
        return

    logger.info(f"[BAJA EMAIL] Encontradas {configs.count()} configuraciones para tipo '{item.tipo_producto.nombre}'.")

    proveedor_nombre = "No especificado"
    if item.recepcion and item.recepcion.entregador and item.recepcion.entregador.proveedor:
        proveedor_nombre = item.recepcion.entregador.proveedor.nombre

    # Build dynamic placeholder context
    context = {
        'item': str(item.item) if item.item is not None else '',
        'serial': item.serial or '',
        'marca': item.marca.nombre if item.marca else '',
        'modelo': item.modelo or '',
        'tipo_producto': item.tipo_producto.nombre or '',
        'proveedor': proveedor_nombre,
        'fecha_baja': item.fecha_baja.strftime('%Y-%m-%d %H:%M:%S') if item.fecha_baja else '',
        'comentarios': item.comentarios or '',
        'comentario_devolucion': item.comentario_devolucion or ''
    }

    for config in configs:
        try:
            # Standard Python formatting using placeholders
            subject = config.asunto.format(**context)
            body = config.cuerpo.format(**context)
        except Exception as e:
            logger.warning(f"Error formateando la plantilla de correo de baja con .format(): {e}. Usando reemplazo simple fallback.")
            subject = config.asunto
            body = config.cuerpo
            # Simple replace fallback for standard placeholders
            for key, val in context.items():
                subject = subject.replace(f"{{{key}}}", str(val))
                body = body.replace(f"{{{key}}}", str(val))

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@inventario.com'),
                recipient_list=[config.destinatario],
                fail_silently=False,
            )
            logger.info(f"Correo de baja enviado exitosamente a {config.destinatario} para el serial {item.serial}")
        except Exception as e:
            logger.error(f"Error enviando correo de baja para el serial {item.serial} a {config.destinatario}: {e}")


def normalize_email(email):
    """
    Normaliza un correo electrónico:
    1. Convierte a minúsculas y elimina espacios iniciales/finales.
    2. Si es una dirección de Gmail (@gmail.com o @googlemail.com):
       - Convierte el dominio a gmail.com.
       - Elimina cualquier subdireccionamiento (ej: usuario+tag -> usuario).
       - Elimina todos los puntos (.) en la parte local del correo.
    """
    if not email:
        return ''
    email = email.strip().lower()
    if '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if domain in ['gmail.com', 'googlemail.com']:
        domain = 'gmail.com'
        local = local.split('+')[0].replace('.', '')
    return f"{local}@{domain}"


def find_user_by_email(email):
    """
    Busca un usuario en la base de datos de manera insensible a mayúsculas/minúsculas
    y aplicando la normalización de Gmail (puntos y subdireccionamientos) de ser necesario.
    """
    if not email:
        return None

    from django.contrib.auth.models import User

    # 1. Búsqueda exacta insensible a mayúsculas y minúsculas
    user = User.objects.filter(email__iexact=email).first()
    if user:
        return user

    # 2. Si es Gmail/Googlemail, buscar con normalización canónica
    email_lower = email.strip().lower()
    if '@gmail.com' in email_lower or '@googlemail.com' in email_lower:
        target_normalized = normalize_email(email_lower)
        # Buscar todos los usuarios con dominios de Gmail
        gmail_users = User.objects.filter(email__icontains='@gmail.com') | User.objects.filter(email__icontains='@googlemail.com')
        for u in gmail_users:
            if normalize_email(u.email) == target_normalized:
                return u

    return None

