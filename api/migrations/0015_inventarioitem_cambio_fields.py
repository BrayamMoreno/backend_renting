from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_tipoproducto_requiere_alistamiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventarioitem',
            name='fecha_inicio_reemplazo',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp when the replacement was registered'),
        ),
        migrations.AddField(
            model_name='inventarioitem',
            name='equipo_reemplazante_serial',
            field=models.CharField(blank=True, max_length=100, null=True, help_text='Serial of the new equipment that replaces this one'),
        ),
        migrations.AlterField(
            model_name='inventarioitem',
            name='estado',
            field=models.CharField(
                choices=[
                    ('RECIBIDO', 'Recibido'),
                    ('ALISTAMIENTO', 'Alistamiento'),
                    ('DISPONIBLE', 'Disponible'),
                    ('ENTREGADO', 'Entregado'),
                    ('EN_ESPERA_DEVOLUCION', 'En Espera de Devolución'),
                    ('PENDIENTE_DEVOLUCION', 'Pendiente Confirmación Proveedor'),
                    ('DEVUELTO', 'Devuelto'),
                ],
                default='RECIBIDO',
                max_length=20,
            ),
        ),
    ]
