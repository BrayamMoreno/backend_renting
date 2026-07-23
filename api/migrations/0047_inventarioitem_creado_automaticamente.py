from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0046_remove_configuracionemailbaja_tipo_producto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventarioitem',
            name='creado_automaticamente',
            field=models.BooleanField(
                default=False,
                help_text='Indica si el equipo fue creado automáticamente durante un flujo de ingreso (cambio/asociación) y sus datos están pendientes de completar.'
            ),
        ),
    ]
