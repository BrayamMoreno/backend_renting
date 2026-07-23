"""
Management command: verificar_alertas_reemplazo
=================================================
Scheduled daily (via cron / Task Scheduler) to detect equipment items
that have been in EN_ESPERA_DEVOLUCION state for more than 5 days and
generate critical alerts for the admin dashboard.

Usage:
    python manage.py verificar_alertas_reemplazo

Windows Task Scheduler example (daily at 08:00):
    Action: python manage.py verificar_alertas_reemplazo
    Start in: C:\\monorepo\\backend
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import InventarioItem, AlertaCritica

UMBRAL_DIAS = 7


class Command(BaseCommand):
    help = 'Verifica equipos en espera de devolución y genera alertas críticas si superan 7 días.'

    def handle(self, *args, **options):
        ahora = timezone.now()
        nuevas_alertas = 0
        items_revisados = 0

        items_en_espera = InventarioItem.objects.filter(
            estado__nombre='EN_ESPERA_DEVOLUCION',
            fecha_inicio_reemplazo__isnull=False
        )

        self.stdout.write(f'[verificar_alertas] Revisando {items_en_espera.count()} equipo(s) en espera...')

        for item in items_en_espera:
            items_revisados += 1
            dias = (ahora - item.fecha_inicio_reemplazo).days

            if dias >= UMBRAL_DIAS:
                # Do not generate more than one alert per day for the same serial
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
                            f'lleva {dias} día{"s" if dias != 1 else ""} sin acta de devolución generada. '
                            f'Fecha de inicio: {item.fecha_inicio_reemplazo.strftime("%Y-%m-%d %H:%M")}.'
                        )
                    )
                    nuevas_alertas += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  ALERTA generada: [{item.serial}] lleva {dias} días sin acta.'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'[verificar_alertas] Listo. {items_revisados} revisados, {nuevas_alertas} alerta(s) nueva(s).'
            )
        )
