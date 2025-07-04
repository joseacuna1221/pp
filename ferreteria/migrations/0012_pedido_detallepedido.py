# Generated by Django 5.0.6 on 2025-05-17 01:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ferreteria', '0011_producto_stock'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id_pedido', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_compra', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('creado', 'Creado'), ('pagado', 'Pagado'), ('rechazado', 'Pago Rechazado'), ('preparando', 'Preparando orden'), ('despachado', 'Despachado'), ('entregado', 'Entregado')], default='creado', max_length=20)),
                ('tipo_envio', models.CharField(choices=[('retiro', 'Retiro en tienda ($0)'), ('domicilio', 'Despacho a domicilio ($5.000)')], default='retiro', max_length=20)),
                ('total', models.BigIntegerField()),
                ('user', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DetallePedido',
            fields=[
                ('id_detalle_pedido', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('subtotal', models.BigIntegerField()),
                ('id_producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ferreteria.producto')),
                ('id_pedido', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='ferreteria.pedido')),
            ],
        ),
    ]
