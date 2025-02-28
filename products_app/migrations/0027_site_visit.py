# Generated by Django 5.1.4 on 2025-02-28 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0026_alter_product_max_height_alter_product_max_width_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='site_visit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
