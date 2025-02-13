# Generated by Django 4.2.19 on 2025-02-13 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products_app', '0006_subcategory_status_subcategory_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Warranty_plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_price_range', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('end_price_range', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('price_range', models.CharField(blank=True, editable=False, max_length=500, null=True)),
                ('year1', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('year2', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('year5', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
            ],
        ),
        migrations.RenameModel(
            old_name='Subcategory_status',
            new_name='Product_status',
        ),
        migrations.RemoveField(
            model_name='product',
            name='subcategory',
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products_app.category'),
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products_app.product_status'),
        ),
        migrations.DeleteModel(
            name='Subcategory',
        ),
    ]
