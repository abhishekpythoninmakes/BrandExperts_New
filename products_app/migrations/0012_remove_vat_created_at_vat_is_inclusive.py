# Generated by Django 4.2.19 on 2025-02-17 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0011_vat'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vat',
            name='created_at',
        ),
        migrations.AddField(
            model_name='vat',
            name='is_inclusive',
            field=models.BooleanField(default=False),
        ),
    ]
