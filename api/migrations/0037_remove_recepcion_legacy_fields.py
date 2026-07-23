from django.db import migrations


class Migration(migrations.Migration):
    """
    Elimina los campos legacy del entregador de la tabla Recepcion.
    Todos los datos ya fueron migrados al modelo Entregador en 0036.
    """

    dependencies = [
        ('api', '0036_entregador_and_recepcion_fk'),
    ]

    operations = [
        migrations.RemoveField(model_name='recepcion', name='entregador_nombre'),
        migrations.RemoveField(model_name='recepcion', name='entregador_cedula'),
        migrations.RemoveField(model_name='recepcion', name='entregador_empresa'),
        migrations.RemoveField(model_name='recepcion', name='entregador_foto'),
        migrations.RemoveField(model_name='recepcion', name='entregador_firma'),
    ]
