# Generated by Django 5.1.4 on 2025-03-20 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0039_alter_product_installation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='disable_customization',
            field=models.BooleanField(blank=True, default=False, help_text='Disable Customization', null=True),
        ),
    ]
