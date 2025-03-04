# Generated by Django 5.1.4 on 2025-03-04 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0029_alter_product_max_height_alter_product_max_width_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='size',
            field=models.CharField(choices=[('cm', 'Centimeter'), ('inches', 'Inches'), ('feet', 'Feet'), ('yard', 'Yard'), ('meter', 'Meter'), ('mm', 'Millimeter')], default='cm', help_text='🛠 Select the measurement unit', max_length=100),
        ),
    ]
