from django.db import migrations, models
import django.db.models.deletion


def migrar_entregadores(apps, schema_editor):
    """
    Data migration: crea un Entregador por cada cédula única en Recepcion,
    asigna el Proveedor si existe, y vincula la FK entregador en cada Recepcion.
    Se usa la foto/firma del registro más reciente para esa cédula.
    """
    Recepcion = apps.get_model('api', 'Recepcion')
    Entregador = apps.get_model('api', 'Entregador')

    # Agrupar recepciones por cédula (más reciente primero por id desc)
    cedulas_procesadas = {}
    recepciones = Recepcion.objects.filter(
        entregador_cedula__gt=''
    ).order_by('-id')

    for rec in recepciones:
        cedula = rec.entregador_cedula.strip()
        if not cedula:
            continue

        if cedula not in cedulas_procesadas:
            # Crear el Entregador usando los datos de la recepción más reciente
            entregador = Entregador.objects.create(
                nombre=rec.entregador_nombre.strip() or 'Sin nombre',
                cedula=cedula,
                proveedor=rec.proveedor,
                foto=rec.entregador_foto,
                firma=rec.entregador_firma,
            )
            cedulas_procesadas[cedula] = entregador
        
        # Vincular todas las recepciones de esta cédula al mismo Entregador
        rec.entregador = cedulas_procesadas[cedula]
        rec.save(update_fields=['entregador'])


def revertir_entregadores(apps, schema_editor):
    """
    Reversa: vuelca los datos del Entregador a los campos planos (para rollback).
    """
    Recepcion = apps.get_model('api', 'Recepcion')
    for rec in Recepcion.objects.filter(entregador__isnull=False):
        ent = rec.entregador
        rec.entregador_nombre = ent.nombre
        rec.entregador_cedula = ent.cedula
        rec.entregador_empresa = ent.proveedor.nombre if ent.proveedor else ''
        rec.entregador_foto = ent.foto
        rec.entregador_firma = ent.firma
        rec.save(update_fields=[
            'entregador_nombre', 'entregador_cedula',
            'entregador_empresa', 'entregador_foto', 'entregador_firma'
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0035_remove_inventarioitem_estado_fk_and_more'),
    ]

    operations = [
        # 1. Crear tabla Entregador
        migrations.CreateModel(
            name='Entregador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('cedula', models.CharField(
                    help_text='Número de identificación único del entregador',
                    max_length=50,
                    unique=True
                )),
                ('foto', models.TextField(blank=True, null=True, help_text='Foto biométrica en base64')),
                ('firma', models.TextField(blank=True, null=True, help_text='Firma en base64')),
                ('proveedor', models.ForeignKey(
                    blank=True,
                    help_text='Empresa/proveedor al que pertenece el entregador',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='entregadores',
                    to='api.proveedor'
                )),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),

        # 2. Agregar FK nullable en Recepcion
        migrations.AddField(
            model_name='recepcion',
            name='entregador',
            field=models.ForeignKey(
                blank=True,
                help_text='Persona que entrega los equipos',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recepciones',
                to='api.entregador'
            ),
        ),

        # 3. Data migration: poblar FK desde campos planos
        migrations.RunPython(migrar_entregadores, revertir_entregadores),

        # 4. Modificar campos legacy a blank=True (ya son null=True para foto/firma)
        migrations.AlterField(
            model_name='recepcion',
            name='entregador_nombre',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='recepcion',
            name='entregador_cedula',
            field=models.CharField(max_length=50, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='recepcion',
            name='entregador_empresa',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
    ]
