# Generated by Django 4.2.19 on 2025-02-12 12:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0015_claimwarranty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customproduct',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='custom_products', to='customer.customer'),
        ),
    ]
