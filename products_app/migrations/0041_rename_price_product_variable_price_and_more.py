# Generated by Django 5.1.7 on 2025-03-26 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0040_product_disable_customization'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='price',
            new_name='variable_price',
        ),
        migrations.AddField(
            model_name='product',
            name='fixed_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
