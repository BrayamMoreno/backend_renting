from rest_framework import serializers
from .models import Recepcion, InventarioItem, Marca, TipoProducto, TipoDisco, Procesador, Ram, Disco, Ubicacion, PuntoAlistamiento, Devolucion, Permiso, Rol, Alistamiento, AlertaCritica, Proveedor, EquipoEstado, Entregador, ItemHistorial, ConfiguracionEmailBaja

class UbicacionSerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()

    class Meta:
        model = Ubicacion
        fields = ['id', 'nombre', 'padre', 'path']

    def get_path(self, obj):
        return obj.path()

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'

class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProducto
        fields = '__all__'

class TipoDiscoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDisco
        fields = '__all__'

class ProcesadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procesador
        fields = '__all__'

class RamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ram
        fields = '__all__'

class DiscoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disco
        fields = '__all__'

from django.contrib.auth.models import User

class CatalogField(serializers.PrimaryKeyRelatedField):
    def __init__(self, model_class, **kwargs):
        self.model_class = model_class
        super().__init__(queryset=model_class.objects.all(), **kwargs)

    def to_representation(self, value):
        if not value:
            return None
        # value may be a PKOnlyObject; fetch the real instance if needed
        if not hasattr(value, 'nombre'):
            try:
                value = self.model_class.objects.get(pk=value.pk)
            except self.model_class.DoesNotExist:
                return None
        return value.nombre

    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        if isinstance(data, int):
            return super().to_internal_value(data)
        if isinstance(data, dict) and 'id' in data:
            return super().to_internal_value(data['id'])
        if isinstance(data, str):
            data_str = data.strip()
            if not data_str:
                return None
            if data_str.isdigit():
                return super().to_internal_value(int(data_str))
            obj = self.model_class.objects.filter(nombre__iexact=data_str).first()
            if not obj:
                obj = self.model_class.objects.create(nombre=data_str)
            return obj
        return super().to_internal_value(data)

class UbicacionCatalogField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(queryset=Ubicacion.objects.all(), **kwargs)

    def to_representation(self, value):
        if not value:
            return None
        # value may be a PKOnlyObject; fetch the real instance if needed
        if not hasattr(value, 'path'):
            try:
                value = Ubicacion.objects.get(pk=value.pk)
            except Ubicacion.DoesNotExist:
                return None
        return value.path()

    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        if isinstance(data, int):
            return super().to_internal_value(data)
        if isinstance(data, dict) and 'id' in data:
            return super().to_internal_value(data['id'])
        if isinstance(data, str):
            data_str = data.strip()
            if not data_str:
                return None
            if data_str.isdigit():
                return super().to_internal_value(int(data_str))
            
            for obj in Ubicacion.objects.all():
                if obj.path().lower() == data_str.lower() or obj.nombre.lower() == data_str.lower():
                    return obj
            
            parts = [p.strip() for p in data_str.split('>')]
            parent = None
            for part in parts:
                if part:
                    parent, _ = Ubicacion.objects.get_or_create(nombre=part, padre=parent)
            return parent
        return super().to_internal_value(data)

class ResponsableDevolucionField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(queryset=User.objects.all(), **kwargs)

    def to_representation(self, value):
        if not value:
            return None
        # value may be a PKOnlyObject; fetch the real User if needed
        if not hasattr(value, 'username'):
            try:
                value = User.objects.get(pk=value.pk)
            except User.DoesNotExist:
                return None
        return value.username

    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        if isinstance(data, int):
            return super().to_internal_value(data)
        if isinstance(data, dict) and 'id' in data:
            return super().to_internal_value(data['id'])
        if isinstance(data, str):
            data_str = data.strip()
            if not data_str:
                return None
            if data_str.isdigit():
                return super().to_internal_value(int(data_str))
            
            # Try exact username match
            user = User.objects.filter(username__iexact=data_str).first()
            
            # Try full name match (first_name + last_name)
            if not user:
                for u in User.objects.all():
                    full_name = f"{u.first_name} {u.last_name}".strip()
                    if full_name.lower() == data_str.lower():
                        user = u
                        break
            
            # Try first_name match
            if not user:
                user = User.objects.filter(first_name__iexact=data_str).first()
                
            # Fallback to creation only if not found by any matching
            if not user:
                safe_username = data_str.replace(' ', '_').lower()[:150]
                user, _ = User.objects.get_or_create(username=safe_username, defaults={'first_name': data_str})
            return user
        return super().to_internal_value(data)

class InventarioItemSerializer(serializers.ModelSerializer):
    tecnico_asignado_nombre = serializers.ReadOnlyField(source='tecnico_asignado.username')
    estado = serializers.SlugRelatedField(slug_field='nombre', queryset=EquipoEstado.objects.all())
    tipo_producto = CatalogField(model_class=TipoProducto, required=False, allow_null=True)
    marca = CatalogField(model_class=Marca, required=False, allow_null=True)
    procesador = CatalogField(model_class=Procesador, required=False, allow_null=True)
    disco = CatalogField(model_class=Disco, required=False, allow_null=True)
    tipo_disco = CatalogField(model_class=TipoDisco, required=False, allow_null=True)
    ram = CatalogField(model_class=Ram, required=False, allow_null=True)
    ubicacion = UbicacionCatalogField(required=False, allow_null=True)
    responsable_devolucion = ResponsableDevolucionField(required=False, allow_null=True)

    class Meta:
        model = InventarioItem
        fields = '__all__'

    def validate(self, attrs):
        item_val = attrs.get('item')
        tipo_producto_obj = attrs.get('tipo_producto')
        
        # During partial updates (PATCH), some fields might not be in attrs, get from instance if available.
        if self.instance:
            if 'item' not in attrs:
                item_val = self.instance.item
            if 'tipo_producto' not in attrs:
                tipo_producto_obj = self.instance.tipo_producto

        if item_val is not None and tipo_producto_obj:
            if tipo_producto_obj.item_unico:
                qs = InventarioItem.objects.filter(item=item_val)
                if self.instance:
                    qs = qs.exclude(id=self.instance.id)
                if qs.exists():
                    raise serializers.ValidationError({
                        'item': f"El número de ítem '{item_val}' ya existe y debe ser único para la categoría '{tipo_producto_obj.nombre}'."
                    })

        # Validar reglas de reemplazo
        es_cambio = attrs.get('es_cambio')
        cambio_por = attrs.get('cambio_por')
        
        if self.instance:
            if es_cambio is None:
                es_cambio = self.instance.es_cambio
            if cambio_por is None:
                cambio_por = self.instance.cambio_por
            if tipo_producto_obj is None:
                tipo_producto_obj = self.instance.tipo_producto

        if es_cambio and cambio_por and tipo_producto_obj:
            cambio_por_str = str(cambio_por).strip()
            # Buscar el equipo/periférico a reemplazar
            replaced = None
            if cambio_por_str.isdigit():
                replaced = InventarioItem.objects.filter(item=int(cambio_por_str)).first()
            else:
                replaced = InventarioItem.objects.filter(serial__iexact=cambio_por_str).first()

            if replaced and replaced.tipo_producto:
                current_is_peripheral = tipo_producto_obj.es_periferico
                replaced_is_peripheral = replaced.tipo_producto.es_periferico

                if not current_is_peripheral and replaced_is_peripheral:
                    raise serializers.ValidationError({
                        'cambio_por': "Un equipo no puede reemplazar a un periférico."
                    })
                elif current_is_peripheral and not replaced_is_peripheral:
                    raise serializers.ValidationError({
                        'cambio_por': "Un periférico no puede reemplazar a un equipo principal."
                    })

        return attrs

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'


class EntregadorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Entregador
        fields = ['id', 'nombre', 'cedula', 'proveedor', 'proveedor_nombre', 'foto', 'firma']

    def get_proveedor_nombre(self, obj):
        return obj.proveedor.nombre if obj.proveedor else None


class EntregadorResumenSerializer(serializers.ModelSerializer):
    """Versión compacta sin foto/firma para embeber en Recepcion."""
    proveedor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Entregador
        fields = ['id', 'nombre', 'cedula', 'proveedor', 'proveedor_nombre']

    def get_proveedor_nombre(self, obj):
        return obj.proveedor.nombre if obj.proveedor else None

class RecepcionSerializer(serializers.ModelSerializer):
    equipos = InventarioItemSerializer(many=True, read_only=True)
    # Datos del entregador expandidos (solo lectura)
    entregador_data = EntregadorResumenSerializer(source='entregador', read_only=True)
    # Campos de conveniencia para el frontend
    entregador_nombre = serializers.SerializerMethodField()
    entregador_cedula = serializers.SerializerMethodField()
    proveedor_nombre = serializers.SerializerMethodField()
    proveedor = serializers.SerializerMethodField()
    entregador_foto = serializers.SerializerMethodField()
    entregador_firma = serializers.SerializerMethodField()

    class Meta:
        model = Recepcion
        fields = '__all__'

    def get_entregador_nombre(self, obj):
        return obj.entregador.nombre if obj.entregador else None

    def get_entregador_cedula(self, obj):
        return obj.entregador.cedula if obj.entregador else None

    def get_proveedor_nombre(self, obj):
        if obj.entregador and obj.entregador.proveedor:
            return obj.entregador.proveedor.nombre
        return None

    def get_proveedor(self, obj):
        if obj.entregador and obj.entregador.proveedor:
            return obj.entregador.proveedor.id
        return None

    def get_entregador_foto(self, obj):
        # Solo retornar la foto capturada en esta recepción específica.
        # No hacer fallback a obj.entregador.foto porque esa se sobreescribe
        # en cada entrega y mostraría la misma foto para todas las recepciones.
        return obj.entregador_foto or None

    def get_entregador_firma(self, obj):
        # Solo retornar la firma capturada en esta recepción específica.
        # No hacer fallback a obj.entregador.firma porque esa se sobreescribe
        # en cada entrega y mostraría la misma firma para todas las recepciones.
        return obj.entregador_firma or None

class PuntoAlistamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntoAlistamiento
        fields = '__all__'

class DevolucionSerializer(serializers.ModelSerializer):
    items = InventarioItemSerializer(many=True, read_only=True)
    confirmado_por_nombre = serializers.ReadOnlyField(source='confirmado_por.username')

    class Meta:
        model = Devolucion
        fields = '__all__'

class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = '__all__'

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class AlistamientoSerializer(serializers.ModelSerializer):
    serial = serializers.CharField(source='inventario_item.serial', read_only=True)
    tecnico_nombre = serializers.ReadOnlyField()

    class Meta:
        model = Alistamiento
        fields = '__all__'


class AlertaCriticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaCritica
        fields = '__all__'


class ItemHistorialSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ItemHistorial
        fields = ['id', 'fecha', 'evento', 'estado_anterior', 'estado_nuevo', 'usuario_nombre', 'detalles']

    def get_usuario_nombre(self, obj):
        if not obj.usuario:
            return 'Sistema'
        return obj.usuario.get_full_name() or obj.usuario.username


class ConfiguracionEmailBajaSerializer(serializers.ModelSerializer):
    tipos_producto = serializers.PrimaryKeyRelatedField(many=True, queryset=TipoProducto.objects.all())
    tipos_producto_nombres = serializers.SerializerMethodField()

    class Meta:
        model = ConfiguracionEmailBaja
        fields = ['id', 'tipos_producto', 'tipos_producto_nombres', 'destinatario', 'asunto', 'cuerpo']

    def get_tipos_producto_nombres(self, obj):
        return [t.nombre for t in obj.tipos_producto.all()]
