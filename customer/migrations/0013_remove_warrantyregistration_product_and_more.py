# Generated by Django 4.2.19 on 2025-02-12 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0012_warrantyregistration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='warrantyregistration',
            name='product',
        ),
        migrations.AddField(
            model_name='warrantyregistration',
            name='product_name',
            field=models.CharField(blank=True, max_length=900, null=True),
        ),
    ]
