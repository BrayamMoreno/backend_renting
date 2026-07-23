from django.contrib import admin
from .models import (
    Recepcion, InventarioItem, Marca, TipoProducto, TipoDisco, Procesador,
    Ram, Disco, Ubicacion, PuntoAlistamiento, Devolucion, Alistamiento, AlertaCritica, Rol, Permiso, Proveedor, EquipoEstado, Entregador, ItemHistorial, ConfiguracionEmailBaja
)

@admin.register(Recepcion)
class RecepcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'get_entregador_nombre', 'get_proveedor', 'receptor_nombre')
    search_fields = ('entregador__nombre', 'entregador__cedula', 'receptor_nombre')
    list_select_related = ('entregador', 'entregador__proveedor')

    def get_entregador_nombre(self, obj):
        return obj.entregador.nombre if obj.entregador else obj.entregador_nombre
    get_entregador_nombre.short_description = 'Entregador'

    def get_proveedor(self, obj):
        if obj.entregador and obj.entregador.proveedor:
            return obj.entregador.proveedor.nombre
        return obj.entregador_empresa
    get_proveedor.short_description = 'Proveedor'

@admin.register(Entregador)
class EntregadorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'cedula', 'proveedor')
    search_fields = ('nombre', 'cedula')
    list_select_related = ('proveedor',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'telefono', 'contacto')
    search_fields = ('nombre', 'telefono')

@admin.register(InventarioItem)
class InventarioItemAdmin(admin.ModelAdmin):
    list_display = ('serial', 'marca', 'modelo', 'tipo_producto', 'ram', 'disco', 'estado')
    search_fields = ('serial', 'marca', 'modelo')

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(TipoProducto)
class TipoProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'requiere_alistamiento', 'item_unico')

@admin.register(TipoDisco)
class TipoDiscoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Procesador)
class ProcesadorAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Ram)
class RamAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Disco)
class DiscoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'padre')

@admin.register(PuntoAlistamiento)
class PuntoAlistamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'orden')

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('id', 'estado', 'fecha_creacion')

@admin.register(Alistamiento)
class AlistamientoAdmin(admin.ModelAdmin):
    list_display = ('get_serial', 'get_tecnico', 'fecha')
    list_select_related = ('inventario_item', 'tecnico')

    def get_serial(self, obj):
        return obj.inventario_item.serial if obj.inventario_item else "-"
    get_serial.short_description = 'Serial'

    def get_tecnico(self, obj):
        return obj.tecnico_nombre
    get_tecnico.short_description = 'Técnico'

@admin.register(AlertaCritica)
class AlertaCriticaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'serial_equipo', 'dias_transcurridos', 'leida')

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(EquipoEstado)
class EquipoEstadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


@admin.register(ItemHistorial)
class ItemHistorialAdmin(admin.ModelAdmin):
    list_display = ('id', 'inventario_item', 'evento', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha')
    list_filter = ('evento', 'estado_nuevo', 'fecha')
    search_fields = ('inventario_item__serial', 'detalles')
    list_select_related = ('inventario_item', 'usuario')


@admin.register(ConfiguracionEmailBaja)
class ConfiguracionEmailBajaAdmin(admin.ModelAdmin):
    list_display = ('get_tipos_producto', 'destinatario', 'asunto')
    search_fields = ('tipos_producto__nombre', 'destinatario', 'asunto')

    def get_tipos_producto(self, obj):
        return ", ".join([t.nombre for t in obj.tipos_producto.all()])
    get_tipos_producto.short_description = 'Tipos de Producto'

