from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_inventarioitem_cambio_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertaCritica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=50, choices=[('REEMPLAZO_SIN_ACTA', 'Reemplazo sin Acta de Devolución')], default='REEMPLAZO_SIN_ACTA')),
                ('mensaje', models.TextField()),
                ('serial_equipo', models.CharField(max_length=100)),
                ('dias_transcurridos', models.IntegerField(default=0)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('leida', models.BooleanField(default=False)),
                ('fecha_lectura', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]
