# Generated by Django 5.1.4 on 2025-03-17 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0054_customer_verified_email_customer_verified_mobile'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='country_code',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]
