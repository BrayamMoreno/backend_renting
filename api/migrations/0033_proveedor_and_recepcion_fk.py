"""
Migración 0033: Crea la tabla Proveedor y agrega FK en Recepcion.
Data migration: convierte valores únicos de entregador_empresa en registros Proveedor
y vincula cada recepción a su proveedor correspondiente.
"""
import django.db.models.deletion
from django.db import migrations, models


def migrar_empresas_a_proveedores(apps, schema_editor):
    """
    Para cada valor único de entregador_empresa en Recepcion,
    crea un Proveedor y actualiza la FK de cada recepción.
    """
    Recepcion = apps.get_model('api', 'Recepcion')
    Proveedor = apps.get_model('api', 'Proveedor')

    # Recoger empresas únicas (normalizadas)
    empresas_vistas = {}
    for recepcion in Recepcion.objects.exclude(entregador_empresa='').exclude(entregador_empresa__isnull=True):
        nombre_normalizado = recepcion.entregador_empresa.strip()
        if not nombre_normalizado:
            continue
        if nombre_normalizado not in empresas_vistas:
            proveedor, _ = Proveedor.objects.get_or_create(nombre=nombre_normalizado)
            empresas_vistas[nombre_normalizado] = proveedor
        recepcion.proveedor = empresas_vistas[nombre_normalizado]
        recepcion.save(update_fields=['proveedor'])


def revertir_migracion(apps, schema_editor):
    """Reversa: copiar el nombre del proveedor de vuelta al campo legacy."""
    Recepcion = apps.get_model('api', 'Recepcion')
    for recepcion in Recepcion.objects.select_related('proveedor').filter(proveedor__isnull=False):
        recepcion.entregador_empresa = recepcion.proveedor.nombre
        recepcion.save(update_fields=['entregador_empresa'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0032_disco_ram'),
    ]

    operations = [
        # 1. Crear tabla Proveedor
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True)),
                ('nit', models.CharField(blank=True, help_text='NIT o número de identificación tributaria', max_length=50, null=True)),
                ('contacto', models.CharField(blank=True, help_text='Nombre del contacto principal', max_length=255, null=True)),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),
        # 2. Cambiar entregador_empresa a blank=True (campo legacy)
        migrations.AlterField(
            model_name='recepcion',
            name='entregador_empresa',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        # 3. Agregar FK proveedor en Recepcion (null por defecto hasta data migration)
        migrations.AddField(
            model_name='recepcion',
            name='proveedor',
            field=models.ForeignKey(
                blank=True,
                help_text='Proveedor/empresa que entrega los equipos',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recepciones',
                to='api.proveedor',
            ),
        ),
        # 4. Data migration: poblar tabla Proveedor con datos históricos
        migrations.RunPython(
            migrar_empresas_a_proveedores,
            reverse_code=revertir_migracion,
        ),
    ]
