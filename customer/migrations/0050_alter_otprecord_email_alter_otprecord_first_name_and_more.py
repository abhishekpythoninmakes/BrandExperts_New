# Generated by Django 5.1.4 on 2025-03-17 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0049_alter_client_user_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otprecord',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='otprecord',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='otprecord',
            name='last_name',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='otprecord',
            name='mobile',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='otprecord',
            name='otp',
            field=models.CharField(max_length=6),
        ),
        migrations.AlterField(
            model_name='otprecord',
            name='password',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
