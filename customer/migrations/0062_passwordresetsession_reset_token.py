# Generated by Django 5.1.7 on 2025-03-26 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0061_alter_otprecord_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='passwordresetsession',
            name='reset_token',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
