from django.db.models.signals import post_save
from django.dispatch import receiver

from products_app.models import Product, InventoryStock


@receiver(post_save, sender=Product)
def create_inventory_stock(sender, instance, created, **kwargs):
    """
    Automatically create InventoryStock when a new Product is created
    """
    if created:
        InventoryStock.objects.create(
            product=instance,
            current_stock=instance.stock if instance.stock else 0
        )

@receiver(post_save, sender=Product)
def update_inventory_stock(sender, instance, **kwargs):
    """
    Update InventoryStock when Product stock is updated
    """
    if hasattr(instance, 'inventory_stock'):
        # Only update if there's a difference to avoid infinite loops
        if instance.inventory_stock.current_stock != (instance.stock or 0):
            instance.inventory_stock.current_stock = instance.stock or 0
            instance.inventory_stock.save()