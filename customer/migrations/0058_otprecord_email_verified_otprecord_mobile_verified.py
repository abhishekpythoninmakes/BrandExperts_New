# Generated by Django 5.1.7 on 2025-03-24 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0057_testmodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='otprecord',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='otprecord',
            name='mobile_verified',
            field=models.BooleanField(default=False),
        ),
    ]
