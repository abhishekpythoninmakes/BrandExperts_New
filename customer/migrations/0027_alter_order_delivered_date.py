# Generated by Django 4.2.19 on 2025-02-14 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0026_customer_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivered_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
