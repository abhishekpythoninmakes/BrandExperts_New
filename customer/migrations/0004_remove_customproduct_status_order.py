# Generated by Django 4.2.19 on 2025-02-12 04:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0003_alter_customproduct_design_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customproduct',
            name='status',
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ordered', 'Ordered'), ('shipped', 'Shipped'), ('arrived', 'Arrived'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='ordered', max_length=15)),
                ('ordered_date', models.DateTimeField(auto_now_add=True)),
                ('payment_method', models.CharField(choices=[('cod', 'Cash on Delivery'), ('card', 'Credit/Debit Card'), ('upi', 'UPI Payment')], default='cod', max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='customer.customer_address')),
                ('cart', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='customer.cart')),
                ('cart_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_item', to='customer.cartitem')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='customer.customer')),
            ],
        ),
    ]
