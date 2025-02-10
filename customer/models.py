from django.db import models
from products_app .models import CustomUser , Product

# Create your models here.


# Customer Registration

class Customer(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    dob = models.DateField(null=True,blank=True)
    mobile = models.CharField(max_length=20,null=True,blank=True)

    def __str__(self):
        return self.user.username if self.user else "Unknown Customer"

class Customer_Address(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,blank=True)
    building_name = models.CharField(max_length=500, null=True, blank=True)
    street_address = models.CharField(max_length=900,null=True,blank=True)
    landmark = models.CharField(max_length=900,null=True,blank=True)
    city = models.CharField(max_length=500,null=True,blank=True)
    district = models.CharField(max_length=500,null=True,blank=True)
    delivery_instructions = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.customer.user.first_name if self.customer.user else "Unknown Customer"


# Choices for sizes
SIZE_CHOICES = [
    ('inches', 'Inches'),
    ('feet', 'Feet'),
]

# Order Status Choices
ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]



class CustomProduct(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="custom_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="custom_orders")

    # Customization Fields
    custom_width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    custom_height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    size_unit = models.CharField(max_length=10, choices=SIZE_CHOICES, default='inches')
    design_image = models.ImageField(upload_to="customer_designs/", null=True, blank=True)

    # Order Status
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Custom {self.product.name} by {self.customer.user.first_name}"



# Cart Status Choices
CART_STATUS_CHOICES = [
    ('active', 'Active'),
    ('checked_out', 'Checked Out'),
    ('abandoned', 'Abandoned'),
]

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="cart")
    status = models.CharField(max_length=15, choices=CART_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Cart for {self.customer.user.first_name} ({self.status})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    custom_product = models.ForeignKey(CustomProduct, on_delete=models.CASCADE, null=True, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        product_name = self.custom_product.product.name if self.custom_product else self.product.name
        return f"{product_name} (x{self.quantity}) - {self.cart.customer.user.first_name}'s Cart"






