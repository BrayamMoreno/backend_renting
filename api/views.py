from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Recepcion, InventarioItem, Marca, TipoProducto, TipoDisco, Procesador, Ram, Disco, Ubicacion,
    PuntoAlistamiento, Devolucion, Rol, Permiso, Alistamiento, AlertaCritica, Proveedor, EquipoEstado, Entregador,
    registrar_historial, ConfiguracionEmailBaja
)
from .serializers import (
    RecepcionSerializer, InventarioItemSerializer, MarcaSerializer,
    TipoProductoSerializer, TipoDiscoSerializer, ProcesadorSerializer, RamSerializer, DiscoSerializer, UbicacionSerializer, PuntoAlistamientoSerializer,
    DevolucionSerializer, RolSerializer, PermisoSerializer,
    AlistamientoSerializer, AlertaCriticaSerializer, ProveedorSerializer, EntregadorSerializer,
    ItemHistorialSerializer, ConfiguracionEmailBajaSerializer
)


class PuntoAlistamientoViewSet(viewsets.ModelViewSet):
    queryset = PuntoAlistamiento.objects.all()
    serializer_class = PuntoAlistamientoSerializer


class UbicacionViewSet(viewsets.ModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all().order_by('nombre')
    serializer_class = MarcaSerializer


class TipoProductoViewSet(viewsets.ModelViewSet):
    queryset = TipoProducto.objects.all().order_by('nombre')
    serializer_class = TipoProductoSerializer

    def perform_update(self, serializer):
        # Save the updated type
        instance = serializer.save()
        
        # If alistamiento is no longer required, automatically push pending items to DISPONIBLE
        if not instance.requiere_alistamiento:
            try:
                disponible_state = EquipoEstado.objects.get(nombre='DISPONIBLE')
                InventarioItem.objects.filter(
                    tipo_producto=instance,
                    estado__nombre__in=['RECIBIDO', 'ALISTAMIENTO']
                ).update(estado=disponible_state)
            except EquipoEstado.DoesNotExist:
                pass


class TipoDiscoViewSet(viewsets.ModelViewSet):
    queryset = TipoDisco.objects.all().order_by('nombre')
    serializer_class = TipoDiscoSerializer


class ProcesadorViewSet(viewsets.ModelViewSet):
    queryset = Procesador.objects.all().order_by('nombre')
    serializer_class = ProcesadorSerializer


class RamViewSet(viewsets.ModelViewSet):
    queryset = Ram.objects.all().order_by('nombre')
    serializer_class = RamSerializer


class DiscoViewSet(viewsets.ModelViewSet):
    queryset = Disco.objects.all().order_by('nombre')
    serializer_class = DiscoSerializer


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by('nombre')
    serializer_class = ProveedorSerializer


class EntregadorViewSet(viewsets.ModelViewSet):
    """
    CRUD de entregadores. Permite buscar por cédula para autocomplete.
    GET /entregadores/?cedula=12345678
    """
    queryset = Entregador.objects.all().order_by('nombre')
    serializer_class = EntregadorSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        cedula = self.request.query_params.get('cedula')
        if cedula:
            # Usar startswith para el autocomplete mientras el usuario escribe;
            # si la cédula está completa (≥10 dígitos) usar exacto para mayor precisión
            if len(cedula) >= 10:
                qs = qs.filter(cedula=cedula)
            else:
                qs = qs.filter(cedula__startswith=cedula)
        return qs

    def perform_create(self, serializer):
        """
        get_or_create por cédula: si ya existe, actualiza nombre, proveedor, foto y firma.
        """
        cedula = serializer.validated_data.get('cedula', '').strip()
        existing = Entregador.objects.filter(cedula=cedula).first()
        if existing:
            for field in ['nombre', 'proveedor', 'foto', 'firma']:
                val = serializer.validated_data.get(field)
                if val is not None:
                    setattr(existing, field, val)
            existing.save()
            # No creamos uno nuevo, devolvemos el existente
            # El serializador ya hizo save(), cancelamos con raise o simplemente devolvemos
            return
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class RecepcionViewSet(viewsets.ModelViewSet):
    queryset = Recepcion.objects.all().order_by('-fecha')
    serializer_class = RecepcionSerializer

    def perform_create(self, serializer):
        """
        Lógica de creación de recepción:
        1. Si viene `entregador` (ID), se usa directamente.
        2. Si vienen campos planos (entregador_nombre + entregador_cedula + proveedor),
           se crea/actualiza el Entregador normalizado y se vincula.
        Compatibilidad retroactiva con registros históricos mantenida.
        """
        data = self.request.data
        entregador_id = data.get('entregador')

        if entregador_id:
            # Caso normalizado: el frontend ya envía el ID del Entregador
            entregador_obj = Entregador.objects.filter(id=entregador_id).first()
            foto = data.get('entregador_foto')
            firma = data.get('entregador_firma')
            if entregador_obj:
                if foto:
                    entregador_obj.foto = foto
                if firma:
                    entregador_obj.firma = firma
                entregador_obj.save()
            serializer.save(
                entregador=entregador_obj,
                entregador_foto=foto,
                entregador_firma=firma
            )
            return

        # Caso con campos planos: crear/actualizar Entregador automáticamente
        cedula = (data.get('entregador_cedula') or '').strip()
        nombre = (data.get('entregador_nombre') or '').strip()
        proveedor_id = data.get('proveedor')
        foto = data.get('entregador_foto')
        firma = data.get('entregador_firma')

        entregador_obj = None
        if cedula:
            proveedor_obj = None
            if proveedor_id:
                proveedor_obj = Proveedor.objects.filter(id=proveedor_id).first()
            elif data.get('entregador_empresa'):
                nombre_empresa = data.get('entregador_empresa').strip()
                if nombre_empresa:
                    proveedor_obj, _ = Proveedor.objects.get_or_create(nombre=nombre_empresa)

            entregador_obj, created = Entregador.objects.get_or_create(
                cedula=cedula,
                defaults={
                    'nombre': nombre or 'Sin nombre',
                    'proveedor': proveedor_obj,
                    'foto': foto,
                    'firma': firma,
                }
            )
            if not created:
                # Actualizar campos al registro más reciente
                if nombre:
                    entregador_obj.nombre = nombre
                if proveedor_obj:
                    entregador_obj.proveedor = proveedor_obj
                if foto:
                    entregador_obj.foto = foto
                if firma:
                    entregador_obj.firma = firma
                entregador_obj.save()

        serializer.save(
            entregador=entregador_obj,
            entregador_foto=foto,
            entregador_firma=firma
        )


class InventarioItemViewSet(viewsets.ModelViewSet):
    queryset = InventarioItem.objects.all().order_by('-fecha_ingreso')
    serializer_class = InventarioItemSerializer

    def perform_create(self, serializer):
        """
        On creation: if es_cambio=True and cambio_por is provided,
        find the replaced equipment and set it to EN_ESPERA_DEVOLUCION.
        """
        instance = serializer.save()

        # Update estado based on requiere_alistamiento
        if instance.tipo_producto:
            tipo_obj = instance.tipo_producto
            if not tipo_obj.requiere_alistamiento:
                if instance.estado and instance.estado.nombre == 'RECIBIDO':
                    instance.estado = EquipoEstado.objects.get(nombre='DISPONIBLE')
                    instance.save(update_fields=['estado'])

        # Log creation history
        registrar_historial(
            item=instance,
            evento='CREACION',
            estado_anterior=None,
            estado_nuevo=instance.estado.nombre if instance.estado else 'RECIBIDO',
            usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
            detalles='Equipo creado/ingresado en el sistema.'
        )

        if instance.es_cambio and instance.cambio_por:
            replaced_serial = str(instance.cambio_por).strip()
            try:
                replaced = None
                if replaced_serial.isdigit():
                    replaced = InventarioItem.objects.filter(item=int(replaced_serial)).first()
                else:
                    replaced = InventarioItem.objects.filter(serial__iexact=replaced_serial).first()
                
                if replaced:
                    old_est = replaced.estado.nombre if replaced.estado else None
                    replaced.estado = EquipoEstado.objects.get(nombre='EN_ESPERA_DEVOLUCION')
                    replaced.fecha_inicio_reemplazo = timezone.now()
                    replaced.equipo_reemplazante_serial = instance.serial
                    replaced.save(update_fields=['estado', 'fecha_inicio_reemplazo', 'equipo_reemplazante_serial'])
                    # Reassociate any peripherals still linked to the old equipment (not returned)
                    if instance.item:
                        from django.db.models import Q
                        q_filter = Q(equipo_asociado=replaced.id)
                        if replaced.item is not None:
                            q_filter |= Q(equipo_asociado=replaced.item)
                        peripherals_qs = InventarioItem.objects.filter(
                            Q(tipo_producto__es_periferico=True) & q_filter
                        ).exclude(estado__nombre='DEVUELTO')
                        for peripheral in peripherals_qs:
                            old_eq = peripheral.equipo_asociado
                            peripheral.equipo_asociado = instance.item
                            peripheral.save(update_fields=['equipo_asociado'])
                            registrar_historial(
                                item=peripheral,
                                evento='ASOCIACION_PERIFERICO',
                                estado_anterior=str(old_eq),
                                estado_nuevo=str(instance.item),
                                usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                                detalles=f'Reasignado periférico {peripheral.serial} del equipo {old_eq} al nuevo equipo {instance.item}.'
                            )
                    
                    registrar_historial(
                        item=replaced,
                        evento='CAMBIO_ESTADO',
                        estado_anterior=old_est,
                        estado_nuevo='EN_ESPERA_DEVOLUCION',
                        usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                        detalles=f"Puesto en espera de devolución al registrar equipo de reemplazo con serial {instance.serial}."
                    )
            except Exception:
                pass

    def perform_update(self, serializer):
        """
        On update: if the status is manually changed to EN_ESPERA_DEVOLUCION
        and there's no fecha_inicio_reemplazo, set it to now.
        Also, if the status changes to DADO_DE_BAJA and fecha_baja is not set, record it now.
        """
        old_instance = self.get_object()
        old_estado = old_instance.estado.nombre if old_instance.estado else None

        instance = serializer.save()

        fields_to_save = []

        if instance.estado and instance.estado.nombre == 'EN_ESPERA_DEVOLUCION' and not instance.fecha_inicio_reemplazo:
            instance.fecha_inicio_reemplazo = timezone.now()
            fields_to_save.append('fecha_inicio_reemplazo')

        if instance.estado and instance.estado.nombre == 'DADO_DE_BAJA' and not instance.fecha_baja:
            instance.fecha_baja = timezone.now()
            fields_to_save.append('fecha_baja')

        if fields_to_save:
            instance.save(update_fields=fields_to_save)

        # Log state transition if changed
        new_estado = instance.estado.nombre if instance.estado else None
        if old_estado != new_estado:
            detalles = f"Estado cambiado de {old_estado} a {new_estado}."
            if new_estado == 'ENTREGADO':
                detalles = f"Equipo entregado. Asignado a técnico/punto: {instance.tecnico_asignado.username if instance.tecnico_asignado else 'Sin asignar'}. Ubicación: {instance.ubicacion.path() if instance.ubicacion else 'Sin ubicación'}."
            elif new_estado == 'EN_ESPERA_DEVOLUCION':
                detalles = f"Puesto en espera de devolución. Responsable devolución: {instance.responsable_devolucion.username if instance.responsable_devolucion else 'Sin responsable'}."
            elif new_estado == 'PENDIENTE_DEVOLUCION':
                detalles = f"Devolución en proceso. Lote devolución #{instance.devolucion.id if instance.devolucion else 'Sin lote'}."
            elif new_estado == 'DEVUELTO':
                detalles = f"Devolución confirmada por el proveedor. Custodia de devolución #{instance.devolucion.id if instance.devolucion else 'Sin lote'}."
            elif new_estado == 'DADO_DE_BAJA':
                detalles = f"Dado de baja del inventario activo."
            
            registrar_historial(
                item=instance,
                evento='CAMBIO_ESTADO',
                estado_anterior=old_estado,
                estado_nuevo=new_estado,
                usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                detalles=detalles
            )

        # Enviar correo de baja si aplica (equipos rentados que pasan a DADO_DE_BAJA)
        if new_estado == 'DADO_DE_BAJA' and old_estado != 'DADO_DE_BAJA' and not instance.es_propio:
            import threading
            import logging
            from .utils import enviar_correo_baja_equipo

            # Capturar el ID para recargar la instancia dentro del hilo
            item_id = instance.id

            def _send_email_background():
                try:
                    from .models import InventarioItem
                    item_fresco = InventarioItem.objects.select_related(
                        'tipo_producto', 'marca', 'recepcion__entregador__proveedor'
                    ).get(pk=item_id)
                    enviar_correo_baja_equipo(item_fresco)
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f"[BAJA EMAIL] Error en hilo de correo para id={item_id}: {type(e).__name__}: {e}",
                        exc_info=True
                    )

            t = threading.Thread(target=_send_email_background, daemon=True)
            t.start()

    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, pk=None):
        item = self.get_object()
        historial = item.historial_eventos.all().order_by('-fecha')
        serializer = ItemHistorialSerializer(historial, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='completar')
    def completar(self, request, pk=None):
        """
        Permite completar los datos de un equipo creado automáticamente.
        Solo opera sobre ítems donde creado_automaticamente=True.
        Al completar, limpia la marca y registra el evento en el historial.
        """
        item = self.get_object()

        if not item.creado_automaticamente:
            return Response(
                {'detail': 'Este equipo no está marcado como creado automáticamente.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Campos técnicos permitidos para actualizar
        campos_permitidos = [
            'item', 'serial', 'tipo_producto', 'marca', 'modelo',
            'procesador', 'ram', 'disco', 'tipo_disco',
            'ubicacion', 'comentarios', 'es_propio',
        ]
        data = {k: v for k, v in request.data.items() if k in campos_permitidos}

        serializer = self.get_serializer(item, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(creado_automaticamente=False)

        registrar_historial(
            item=instance,
            evento='COMPLETAR_DATOS',
            estado_anterior='INCOMPLETO',
            estado_nuevo=instance.estado.nombre if instance.estado else 'ENTREGADO',
            usuario=request.user if request.user and not request.user.is_anonymous else None,
            detalles='Datos del equipo completados por el usuario tras su creación automática.'
        )

        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['get'], url_path='en-espera-devolucion')
    def en_espera_devolucion(self, request):
        """Returns all items currently waiting for a return act."""
        queryset = InventarioItem.objects.filter(
            estado__nombre='EN_ESPERA_DEVOLUCION'
        ).order_by('fecha_inicio_reemplazo')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='verificar-alertas')
    def verificar_alertas(self, request):
        """
        Manual trigger / cron-compatible endpoint.
        Generates critical alerts for items that have been in EN_ESPERA_DEVOLUCION
        for more than 7 days without a return act.
        """
        umbral_dias = 7
        ahora = timezone.now()
        nuevas_alertas = 0

        items_en_espera = InventarioItem.objects.filter(
            estado__nombre='EN_ESPERA_DEVOLUCION',
            fecha_inicio_reemplazo__isnull=False,
            es_propio=False
        )

        for item in items_en_espera:
            dias = (ahora - item.fecha_inicio_reemplazo).days
            if dias >= umbral_dias:
                # Avoid duplicating alerts created today for the same serial
                ya_alertado_hoy = AlertaCritica.objects.filter(
                    serial_equipo=item.serial,
                    fecha_creacion__date=ahora.date()
                ).exists()

                if not ya_alertado_hoy:
                    AlertaCritica.objects.create(
                        tipo='REEMPLAZO_SIN_ACTA',
                        serial_equipo=item.serial,
                        dias_transcurridos=dias,
                        mensaje=(
                            f'El equipo [{item.serial}] (Ítem: {item.item or "N/A"}) - {item.marca} {item.modelo} '
                            f'ubicado en [{item.ubicacion or "Sin Ubicación"}] '
                            f'lleva {dias} día{"s" if dias != 1 else ""} sin acta de devolución generada.'
                        )
                    )
                    nuevas_alertas += 1

        return Response({
            'alertas_generadas': nuevas_alertas,
            'items_verificados': items_en_espera.count()
        })


class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all().order_by('-fecha_creacion')
    serializer_class = DevolucionSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.estado == 'CONFIRMADA':
            # Mark all linked items as DEVUELTO and record history
            try:
                devuelto_state = EquipoEstado.objects.get(nombre='DEVUELTO')
                for item in instance.items.all():
                    old_est = item.estado.nombre if item.estado else None
                    item.estado = devuelto_state
                    item.save()
                    
                    registrar_historial(
                        item=item,
                        evento='CAMBIO_ESTADO',
                        estado_anterior=old_est,
                        estado_nuevo='DEVUELTO',
                        usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                        detalles=f"Devolución confirmada por el proveedor. Custodia de devolución #{instance.id}."
                    )
            except EquipoEstado.DoesNotExist:
                pass
            if not instance.confirmado_por:
                instance.confirmado_por = self.request.user
                instance.save()


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all().order_by('nombre')
    serializer_class = RolSerializer


class PermisoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permiso.objects.all().order_by('nombre')
    serializer_class = PermisoSerializer


class AlistamientoViewSet(viewsets.ModelViewSet):
    queryset = Alistamiento.objects.all().order_by('-fecha')
    serializer_class = AlistamientoSerializer

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError
        item = serializer.validated_data.get('inventario_item')
        if item and (not item.estado or item.estado.nombre not in ['RECIBIDO', 'ALISTAMIENTO']):
            raise ValidationError("El alistamiento solo se puede realizar a equipos con estado Recibido o Alistamiento.")

        old_est_val = item.estado.nombre if item and item.estado else None
        alistamiento = serializer.save()

        # Log alistamiento event
        if item:
            registrar_historial(
                item=item,
                evento='ALISTAMIENTO',
                estado_anterior=old_est_val,
                estado_nuevo='DISPONIBLE',
                usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                detalles=f"Alistamiento Técnico completado. Técnico: {alistamiento.tecnico.get_full_name() or alistamiento.tecnico.username}."
            )

        if item and item.es_cambio and item.cambio_por:
            replaced_val = str(item.cambio_por).strip()
            try:
                # Find the old asset
                replaced = None
                if replaced_val.isdigit():
                    replaced = InventarioItem.objects.filter(item=int(replaced_val)).first()
                else:
                    replaced = InventarioItem.objects.filter(serial__iexact=replaced_val).first()
                
                # Find or create User object for responsable_devolucion
                tecnico_user = alistamiento.tecnico

                if replaced:
                    old_repl_est = replaced.estado.nombre if replaced.estado else None
                    replaced.estado = EquipoEstado.objects.get(nombre='EN_ESPERA_DEVOLUCION')
                    replaced.fecha_inicio_reemplazo = alistamiento.fecha
                    replaced.equipo_reemplazante_serial = item.serial
                    replaced.responsable_devolucion = tecnico_user
                    replaced.save(update_fields=['estado', 'fecha_inicio_reemplazo', 'equipo_reemplazante_serial', 'responsable_devolucion'])
                    # Reassociate peripherals still linked to the old equipment (not returned)
                    if item.item:
                        from django.db.models import Q
                        q_filter = Q(equipo_asociado=replaced.id)
                        if replaced.item is not None:
                            q_filter |= Q(equipo_asociado=replaced.item)
                        peripherals_qs = InventarioItem.objects.filter(
                            Q(tipo_producto__es_periferico=True) & q_filter
                        ).exclude(estado__nombre='DEVUELTO')
                        for peripheral in peripherals_qs:
                            old_eq = peripheral.equipo_asociado
                            peripheral.equipo_asociado = item.item
                            peripheral.save(update_fields=['equipo_asociado'])
                            registrar_historial(
                                item=peripheral,
                                evento='ASOCIACION_PERIFERICO',
                                estado_anterior=str(old_eq),
                                estado_nuevo=str(item.item),
                                usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                                detalles=f'Reasignado periférico {peripheral.serial} del equipo {old_eq} al nuevo equipo {item.item}.'
                            )
                    
                    registrar_historial(
                        item=replaced,
                        evento='CAMBIO_ESTADO',
                        estado_anterior=old_repl_est,
                        estado_nuevo='EN_ESPERA_DEVOLUCION',
                        usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                        detalles=f"Puesto en espera de devolución al realizar alistamiento del equipo reemplazante {item.serial}."
                    )
                else:
                    # Ghost item creation if it doesn't exist
                    ghost_serial = f"CAMBIO-{replaced_val}-{int(timezone.now().timestamp())}"
                    no_registrada_marca, _ = Marca.objects.get_or_create(nombre='NO REGISTRADA')
                    ghost_item = InventarioItem.objects.create(
                        item=int(replaced_val) if replaced_val.isdigit() else None,
                        serial=ghost_serial,
                        marca=no_registrada_marca,
                        modelo='NO REGISTRADO',
                        estado=EquipoEstado.objects.get(nombre='EN_ESPERA_DEVOLUCION'),
                        responsable_devolucion=tecnico_user,
                        fecha_inicio_reemplazo=alistamiento.fecha,
                        equipo_reemplazante_serial=item.serial,
                        comentarios=f"Creado automáticamente por alistamiento de equipo de cambio (Reemplazado por {item.serial})"
                    )
                    
                    registrar_historial(
                        item=ghost_item,
                        evento='CREACION',
                        estado_anterior=None,
                        estado_nuevo='EN_ESPERA_DEVOLUCION',
                        usuario=self.request.user if self.request.user and not self.request.user.is_anonymous else None,
                        detalles=f"Equipo fantasma creado automáticamente por alistamiento de equipo reemplazante {item.serial}."
                    )
            except Exception:
                pass


class AlertaCriticaViewSet(viewsets.ModelViewSet):
    queryset = AlertaCritica.objects.all()
    serializer_class = AlertaCriticaSerializer

    @action(detail=False, methods=['get'], url_path='no-leidas')
    def no_leidas(self, request):
        queryset = AlertaCritica.objects.filter(leida=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='marcar-leida')
    def marcar_leida(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.fecha_lectura = timezone.now()
        alerta.save()
        return Response({'status': 'ok'})

    @action(detail=False, methods=['patch'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        AlertaCritica.objects.filter(leida=False).update(
            leida=True,
            fecha_lectura=timezone.now()
        )
        return Response({'status': 'ok'})


class UserPendingView(APIView):
    """
    Returns per-user aggregated equipment stats.
    Accepts optional query params: start_date, end_date (YYYY-MM-DD).
    Only returns users that have at least one active (non-DEVUELTO) item.
    """

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        qs = InventarioItem.objects.exclude(estado__nombre__in=['DEVUELTO', 'DADO_DE_BAJA']).filter(
            tecnico_asignado__isnull=False
        )

        if start_date:
            qs = qs.filter(fecha_ingreso__date__gte=start_date)
        if end_date:
            qs = qs.filter(fecha_ingreso__date__lte=end_date)

        # Aggregate per user
        users_map = {}
        for item in qs.select_related('tecnico_asignado'):
            user = item.tecnico_asignado
            key = user.id
            if key not in users_map:
                users_map[key] = {
                    'id': user.id,
                    'nombre': user.get_full_name() or user.username,
                    'pending_alistamiento': 0,
                    'pending_devolucion': 0,
                    'recibidos': 0,
                    'total': 0,
                }
            entry = users_map[key]
            entry['total'] += 1
            if item.estado and item.estado.nombre == 'ALISTAMIENTO':
                entry['pending_alistamiento'] += 1
            elif item.estado and item.estado.nombre in ('EN_ESPERA_DEVOLUCION', 'PENDIENTE_DEVOLUCION'):
                entry['pending_devolucion'] += 1
            elif item.estado and item.estado.nombre == 'RECIBIDO':
                entry['recibidos'] += 1

        # Only include users with at least something pending
        result = [v for v in users_map.values() if v['total'] > 0]
        result.sort(key=lambda x: x['nombre'])

        return Response(result)


class ConfiguracionEmailBajaViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionEmailBaja.objects.all()
    serializer_class = ConfiguracionEmailBajaSerializer


class BackupViewSet(viewsets.ViewSet):
    """
    ViewSet para la administración de respaldos de la base de datos (Backups Condicionales y Manuales).
    """

    def list(self, request):
        from . import backup_service
        backups = backup_service.list_backups()
        hay_cambios = backup_service.has_changes_since_last_backup()
        last_change_info = backup_service.get_last_db_change_info()
        return Response({
            'backups': backups,
            'hay_cambios_pendientes': hay_cambios,
            'ultimo_cambio': last_change_info
        })

    @action(detail=False, methods=['post'], url_path='generar')
    def generar(self, request):
        from . import backup_service
        modo = request.data.get('modo', 'condicional')
        res = backup_service.create_backup(modo=modo, usuario=request.user)
        status_code = status.HTTP_200_OK if res['status'] != 'error' else status.HTTP_400_BAD_REQUEST
        return Response(res, status=status_code)

    @action(detail=False, methods=['get'], url_path='descargar')
    def descargar(self, request):
        from . import backup_service
        from django.http import FileResponse
        filename = request.query_params.get('filename')
        if not filename:
            return Response({'detail': 'Se requiere el nombre del archivo.'}, status=status.HTTP_400_BAD_REQUEST)
        
        filepath = backup_service.get_backup_file_path(filename)
        if not filepath:
            return Response({'detail': 'Archivo de respaldo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        file_handle = open(filepath, 'rb')
        return FileResponse(file_handle, as_attachment=True, filename=filename, content_type='application/gzip')

    @action(detail=False, methods=['delete'], url_path='eliminar')
    def eliminar(self, request):
        from . import backup_service
        filename = request.query_params.get('filename')
        if not filename:
            return Response({'detail': 'Se requiere el nombre del archivo.'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = backup_service.delete_backup(filename)
        if success:
            return Response({'status': 'deleted', 'message': f'Respaldo "{filename}" eliminado correctamente.'})
        return Response({'detail': 'No se pudo eliminar el archivo o no existe.'}, status=status.HTTP_404_NOT_FOUND)

