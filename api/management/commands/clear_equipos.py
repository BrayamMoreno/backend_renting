from django.core.management.base import BaseCommand
from api.models import (
    InventarioItem, Recepcion, Devolucion, Alistamiento,
    AlertaCritica, ItemHistorial, Entregador
)

class Command(BaseCommand):
    help = 'Elimina todos los equipos, recepciones, devoluciones, alistamientos e historiales de la base de datos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando limpieza de todos los equipos e historiales...')

        count_historial, _ = ItemHistorial.objects.all().delete()
        count_alistamiento, _ = Alistamiento.objects.all().delete()
        count_inventario, _ = InventarioItem.objects.all().delete()
        count_devoluciones, _ = Devolucion.objects.all().delete()
        count_recepciones, _ = Recepcion.objects.all().delete()
        count_alertas, _ = AlertaCritica.objects.all().delete()
        count_entregadores, _ = Entregador.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'Limpieza completada exitosamente:\n'
            f' - {count_inventario} ítems de inventario eliminados\n'
            f' - {count_recepciones} recepciones eliminadas\n'
            f' - {count_devoluciones} devoluciones eliminadas\n'
            f' - {count_alistamiento} alistamientos eliminados\n'
            f' - {count_historial} registros de historial eliminados\n'
            f' - {count_alertas} alertas eliminadas\n'
            f' - {count_entregadores} entregadores eliminados'
        ))
