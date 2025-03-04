# Generated by Django 5.1.4 on 2025-03-04 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0043_alter_cartitem_size_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='size_unit',
            field=models.CharField(choices=[('cm', 'Centimeter'), ('inches', 'Inches'), ('feet', 'Feet'), ('yard', 'Yard'), ('meter', 'Meter'), ('mm', 'Millimeter')], default='cm', max_length=10),
        ),
    ]
