# Generated by Django 5.1.4 on 2025-03-04 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0027_site_visit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='size',
            field=models.CharField(choices=[('centimeter', 'Centimeter')], default='centimeter', help_text='🛠 Select the measurement unit', max_length=100),
        ),
    ]
