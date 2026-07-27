from django.core.management.base import BaseCommand
from django.db.models import Q
from api.models import InventarioItem

class Command(BaseCommand):
    help = 'Repara asociaciones en equipos principales y sincroniza responsable_devolucion en periféricos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando limpieza y reparación de periféricos y equipos en la base de datos...')

        # 1. Limpiar equipo_asociado = None en todos los equipos principales (no periféricos)
        non_periphs = InventarioItem.objects.filter(
            tipo_producto__es_periferico=False,
            equipo_asociado__isnull=False
        )
        count_cleared = 0
        for item in non_periphs:
            old_eq = item.equipo_asociado
            item.equipo_asociado = None
            item.save(update_fields=['equipo_asociado'])
            count_cleared += 1
            self.stdout.write(self.style.SUCCESS(f'Limpiado equipo_asociado ({old_eq}) de equipo principal #{item.item} ({item.serial})'))

        # 2. Restaurar equipo_asociado en periféricos en devolución que fueron reasociados erróneamente al equipo de reemplazo
        pending_periphs = InventarioItem.objects.filter(
            tipo_producto__es_periferico=True,
            estado__nombre__in=['EN_ESPERA_DEVOLUCION', 'PENDIENTE_DEVOLUCION'],
            equipo_asociado__isnull=False
        )
        count_reverted = 0
        for periph in pending_periphs:
            # Buscar si el equipo al que está actualmente asociado es un reemplazo (es_cambio=True)
            current_target = InventarioItem.objects.filter(
                Q(id=periph.equipo_asociado) | Q(item=periph.equipo_asociado)
            ).first()

            if current_target and current_target.es_cambio and current_target.cambio_por:
                # Buscar el equipo original reemplazado
                cambio_val = str(current_target.cambio_por).strip()
                replaced = None
                if cambio_val.isdigit():
                    replaced = InventarioItem.objects.filter(item=int(cambio_val)).first()
                else:
                    replaced = InventarioItem.objects.filter(serial__iexact=cambio_val).first()

                if replaced and periph.equipo_asociado != (replaced.item or replaced.id):
                    old_target_item = current_target.item
                    periph.equipo_asociado = replaced.item or replaced.id
                    periph.save(update_fields=['equipo_asociado'])
                    count_reverted += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'Revertida asociación de periférico #{periph.item} ({periph.serial}) del nuevo equipo #{old_target_item} al equipo original #{replaced.item}'
                    ))

        # 3. Propagar responsable_devolucion de los equipos principales en devolución hacia sus periféricos vinculados
        main_equip_in_dev = InventarioItem.objects.filter(
            tipo_producto__es_periferico=False,
            responsable_devolucion__isnull=False
        )
        count_resp_synced = 0
        for main_eq in main_equip_in_dev:
            q_filter = Q(equipo_asociado=main_eq.id)
            if main_eq.item is not None:
                q_filter |= Q(equipo_asociado=main_eq.item)

            periphs = InventarioItem.objects.filter(
                Q(tipo_producto__es_periferico=True) & q_filter
            ).exclude(estado__nombre='DEVUELTO')

            for periph in periphs:
                if periph.responsable_devolucion != main_eq.responsable_devolucion:
                    periph.responsable_devolucion = main_eq.responsable_devolucion
                    periph.save(update_fields=['responsable_devolucion'])
                    count_resp_synced += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'Sincronizado responsable_devolucion ({main_eq.responsable_devolucion.username}) en periférico #{periph.item} ({periph.serial})'
                    ))

        self.stdout.write(self.style.SUCCESS(
            f'Finalizado: {count_cleared} equipos principales limpiados, {count_reverted} periféricos revertidos, {count_resp_synced} responsables sincronizados.'
        ))
