from django.core.management.base import BaseCommand
from api import backup_service

class Command(BaseCommand):
    help = 'Genera una copia de seguridad de la base de datos de forma condicional o forzada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación del respaldo aunque no se hayan registrado cambios',
        )

    def handle(self, *args, **options):
        modo = 'manual' if options['force'] else 'condicional'
        self.stdout.write(f'Iniciando copia de seguridad (Modo: {modo})...')
        
        res = backup_service.create_backup(modo=modo)
        
        if res['status'] == 'created':
            self.stdout.write(self.style.SUCCESS(res['message']))
        else:
            self.stdout.write(self.style.WARNING(res['message']))
