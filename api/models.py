from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Permiso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class Rol(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    permisos = models.ManyToManyField(Permiso, blank=True, related_name='roles')

    def __str__(self):
        return self.nombre

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, default='BODEGA') # Mantener para compatibilidad simple
    rol_entidad = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True, related_name='perfiles')
    permisos = models.ManyToManyField(Permiso, blank=True, related_name='perfiles_extra')
    is_approved = models.BooleanField(default=True)  # True por defecto para no afectar usuarios existentes
    google_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    avatar_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"



class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True, help_text='Número de teléfono del proveedor')
    contacto = models.CharField(max_length=255, blank=True, null=True, help_text='Nombre del contacto principal')

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Entregador(models.Model):
    """Persona física que entrega equipos. Identificada de forma única por cédula."""
    nombre = models.CharField(max_length=255)
    cedula = models.CharField(max_length=50, unique=True, help_text='Número de identificación único del entregador')
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregadores',
        help_text='Empresa/proveedor al que pertenece el entregador'
    )
    foto = models.TextField(blank=True, null=True, help_text='Foto biométrica en base64 (se actualiza en cada entrega)')
    firma = models.TextField(blank=True, null=True, help_text='Firma en base64 (se actualiza en cada entrega)')

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        proveedor_str = self.proveedor.nombre if self.proveedor else 'Sin empresa'
        return f"{self.nombre} ({self.cedula}) — {proveedor_str}"


class Recepcion(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)

    # FK normalizada al entregador
    entregador = models.ForeignKey(
        'Entregador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recepciones',
        help_text='Persona que entrega los equipos'
    )

    # Receptor
    receptor_nombre = models.CharField(max_length=255)
    receptor_firma = models.TextField(blank=True, null=True) # base64
    receptor_foto = models.TextField(blank=True, null=True) # base64

    # Entregador en el momento de la entrega
    entregador_foto = models.TextField(blank=True, null=True, help_text='Foto biométrica del entregador en esta entrega específica')
    entregador_firma = models.TextField(blank=True, null=True, help_text='Firma del entregador en esta entrega específica')

    def __str__(self):
        if self.entregador:
            return f"Recepción {self.id} - {self.entregador} - {self.fecha}"
        return f"Recepción {self.id} - {self.fecha}"

class EquipoEstado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado de Equipo"
        verbose_name_plural = "Estados de Equipo"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


def get_default_estado():
    try:
        return EquipoEstado.objects.get_or_create(nombre='RECIBIDO')[0].pk
    except Exception:
        return 1


class InventarioItem(models.Model):
    STATUS_CHOICES = [
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

    item = models.IntegerField(null=True, blank=True)
    es_propio = models.BooleanField(default=False, help_text='Indica si el equipo es propio (no alquilado)')
    tipo_producto = models.ForeignKey('TipoProducto', on_delete=models.SET_NULL, null=True, blank=True)
    marca = models.ForeignKey('Marca', on_delete=models.SET_NULL, null=True, blank=True)
    modelo = models.CharField(max_length=100)
    procesador = models.ForeignKey('Procesador', on_delete=models.SET_NULL, null=True, blank=True)
    disco = models.ForeignKey('Disco', on_delete=models.SET_NULL, null=True, blank=True)
    tipo_disco = models.ForeignKey('TipoDisco', on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey('Ram', on_delete=models.SET_NULL, null=True, blank=True)
    serial = models.CharField(max_length=100, unique=True)
    es_cambio = models.BooleanField(default=False)
    cambio_por = models.CharField(max_length=100, null=True, blank=True)
    ubicacion = models.ForeignKey('Ubicacion', on_delete=models.SET_NULL, null=True, blank=True)
    comentarios = models.TextField(null=True, blank=True)
    comentario_devolucion = models.TextField(null=True, blank=True)
    creado_automaticamente = models.BooleanField(
        default=False,
        help_text='Indica si el equipo fue creado automáticamente durante un flujo de ingreso (cambio/asociación) y sus datos están pendientes de completar.'
    )
    
    estado = models.ForeignKey(EquipoEstado, on_delete=models.PROTECT, related_name='inventario_items', default=get_default_estado)
    recepcion = models.ForeignKey(Recepcion, related_name='equipos', on_delete=models.CASCADE, null=True, blank=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    metadata_ocr = models.JSONField(null=True, blank=True)
    devolucion = models.ForeignKey('Devolucion', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    # Campos de reemplazo
    fecha_inicio_reemplazo = models.DateTimeField(null=True, blank=True, help_text='Timestamp when replacement was registered')
    equipo_reemplazante_serial = models.CharField(max_length=100, null=True, blank=True, help_text='Serial of the new equipment replacing this one')
    
    # Asignación de Alistamiento
    tecnico_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alistamientos_asignados')
    fecha_asignacion_alistamiento = models.DateTimeField(null=True, blank=True)

    # Baja del equipo
    fecha_baja = models.DateTimeField(null=True, blank=True, help_text='Fecha en que el equipo fue dado de baja (confirmado por proveedor o manualmente)')

    responsable_devolucion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='items_responsables_devolucion', help_text='Usuario que colocó el equipo en devolución')
    solicitante_cambio = models.CharField(max_length=255, null=True, blank=True, help_text='Nombre de la persona que solicitó el cambio')
    equipo_asociado = models.IntegerField(null=True, blank=True, help_text='Item number del equipo al que está asociado')

    def save(self, *args, **kwargs):
        # Convertir seriales a mayúsculas
        if self.serial:
            self.serial = self.serial.upper().strip()
        if self.equipo_reemplazante_serial:
            self.equipo_reemplazante_serial = self.equipo_reemplazante_serial.upper().strip()
        if self.cambio_por and not self.cambio_por.isdigit():
            self.cambio_por = self.cambio_por.upper().strip()

        es_nuevo = self.pk is None
        anterior_estado = None
        if not es_nuevo:
            try:
                anterior = InventarioItem.objects.get(pk=self.pk)
                anterior_estado = anterior.estado.nombre if anterior.estado else None
            except InventarioItem.DoesNotExist:
                pass

        if self.estado and self.estado.nombre in ['RECIBIDO', 'ALMACENADO', 'EN_ESPERA_DEVOLUCION', 'DEVUELTO', 'PENDIENTE_DEVOLUCION', 'DADO_DE_BAJA']:
            self.tecnico_asignado = None
            self.fecha_asignacion_alistamiento = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.serial}"

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class TipoProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    requiere_alistamiento = models.BooleanField(default=True)
    item_unico = models.BooleanField(default=False)
    es_periferico = models.BooleanField(default=False, help_text='Indica si este tipo corresponde a un periférico (mouse, teclado, cable, etc.) en lugar de un equipo de cómputo principal')
    def __str__(self):
        return self.nombre

class TipoDisco(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class Procesador(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class Ram(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class Disco(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_ubicaciones')

    def path(self):
        if self.padre:
            return f"{self.padre.path()} > {self.nombre}"
        return self.nombre

    def __str__(self):
        return self.path()

    class Meta:
        unique_together = ('nombre', 'padre')

class PuntoAlistamiento(models.Model):
    nombre = models.CharField(max_length=200)
    requiere_evidencia = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

class Devolucion(models.Model):
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('CONFIRMADA', 'Confirmada'),
    ]
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    confirmado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devoluciones_confirmadas')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE')
    comentarios = models.TextField(null=True, blank=True)
    # Evidencias fotográficas de los responsables
    foto_receptor = models.TextField(blank=True, null=True)   # base64 - quien recibe el equipo
    foto_entregador = models.TextField(blank=True, null=True) # base64 - quien entrega el equipo
    foto_alistador = models.TextField(blank=True, null=True)  # base64 - quien alista el equipo
    comentario_confirmacion = models.TextField(null=True, blank=True)
    
    # Campos para devolución con novedades
    tiene_novedad = models.BooleanField(default=False)
    documento_novedad = models.TextField(blank=True, null=True) # base64
    mensaje_novedad = models.TextField(blank=True, null=True)

    # Nuevos campos del flujo de devoluciones
    foto_persona_devolucion = models.TextField(blank=True, null=True) # base64
    firma_persona_devolucion = models.TextField(blank=True, null=True) # base64
    nombre_persona_devolucion = models.CharField(max_length=255, blank=True, null=True)
    cedula_persona_devolucion = models.CharField(max_length=50, blank=True, null=True)
    aprobado_por_nombre = models.CharField(max_length=255, blank=True, null=True)
    firma_aprobador = models.TextField(blank=True, null=True) # base64

    def __str__(self):
        return f"Devolución {self.id} - {self.estado}"


class Alistamiento(models.Model):
    inventario_item = models.ForeignKey(InventarioItem, on_delete=models.CASCADE, related_name='alistamientos')
    fecha = models.DateTimeField(auto_now_add=True)
    tecnico = models.ForeignKey(User, on_delete=models.PROTECT, related_name='alistamientos_realizados')
    foto_tecnico = models.TextField(blank=True, null=True)  # base64
    respuestas = models.JSONField(default=dict)

    class Meta:
        ordering = ['-fecha']

    @property
    def serial(self):
        return self.inventario_item.serial if self.inventario_item else ""

    @property
    def tecnico_nombre(self):
        if self.tecnico:
            full_name = f"{self.tecnico.first_name} {self.tecnico.last_name}".strip()
            return full_name if full_name else self.tecnico.username
        return ""

    def __str__(self):
        return f"Alistamiento {self.serial} - {self.fecha}"


class AlertaCritica(models.Model):
    TIPO_CHOICES = [
        ('REEMPLAZO_SIN_ACTA', 'Reemplazo sin Acta de Devolución'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='REEMPLAZO_SIN_ACTA')
    mensaje = models.TextField()
    serial_equipo = models.CharField(max_length=100)
    dias_transcurridos = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Alerta [{self.tipo}] {self.serial_equipo} - {self.dias_transcurridos} días"


class ItemHistorial(models.Model):
    inventario_item = models.ForeignKey(
        'InventarioItem',
        on_delete=models.CASCADE,
        related_name='historial_eventos'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    evento = models.CharField(max_length=100) # CREACION, ALISTAMIENTO, CAMBIO_ESTADO, BAJA, etc.
    estado_anterior = models.CharField(max_length=50, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=50)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acciones_historial'
    )
    detalles = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.inventario_item.serial} - {self.evento} - {self.fecha}"


def registrar_historial(item, evento, estado_anterior, estado_nuevo, usuario=None, detalles=None):
    return ItemHistorial.objects.create(
        inventario_item=item,
        evento=evento,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario=usuario,
        detalles=detalles
    )


class ConfiguracionEmailBaja(models.Model):
    tipos_producto = models.ManyToManyField(
        'TipoProducto',
        related_name='configuraciones_email_baja',
        help_text='Tipos de producto a los que aplica esta configuración de correo'
    )
    destinatario = models.EmailField(
        help_text='Correo electrónico del destinatario principal'
    )
    asunto = models.CharField(
        max_length=255,
        default='Baja de Equipo del Proveedor: {serial}',
        help_text='Asunto del correo. Puede usar {serial}, {marca}, {modelo}.'
    )
    cuerpo = models.TextField(
        help_text='Cuerpo del mensaje. Puede usar {serial}, {marca}, {modelo}, {tipo_producto}, {proveedor}, {fecha_baja}.'
    )

    class Meta:
        verbose_name = "Configuración Email de Baja"
        verbose_name_plural = "Configuraciones Email de Baja"

    def __str__(self):
        if self.pk:
            tipos = ", ".join([t.nombre for t in self.tipos_producto.all()])
            return f"Configuración Email - [{tipos}]"
        return "Nueva Configuración de Email"
