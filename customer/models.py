from django.db import models
from products_app .models import CustomUser , Product
import random
import string

# Create your models here.


# Customer Registration

class Customer(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    dob = models.DateField(null=True,blank=True)
    mobile = models.CharField(max_length=20,null=True,blank=True)

    def __str__(self):
        return self.user.username if self.user else "Unknown Customer"


# Warranty Plan Choices
WARRANTY_PLAN_CHOICES = [
    ('799_1yr', '799 AED - 1 year'),
    ('999_2yr', '999 AED - 2 years'),
    ('1799_5yr', '1799 AED - 5 years'),
]



class WarrantyRegistration(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    product_name = models.CharField(max_length=900, null=True, blank=True)
    invoice_date = models.DateField()
    invoice_value = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_file = models.URLField(blank=True, null=True)
    warranty_plan = models.CharField(max_length=20, choices=WARRANTY_PLAN_CHOICES)
    warranty_number = models.CharField(max_length=8, unique=True, editable=False,null=True,blank=True)  # Unique warranty number
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.warranty_number:
            self.warranty_number = self.generate_warranty_number()
        super().save(*args, **kwargs)

    def generate_warranty_number(self):
        """Generate a unique 8-character alphanumeric warranty number."""
        while True:
            warranty_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not WarrantyRegistration.objects.filter(warranty_number=warranty_number).exists():
                return warranty_number

    def __str__(self):
        return f"{self.full_name} - {self.product_name} ({self.get_warranty_plan_display()})"


class ClaimWarranty(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    warranty_number = models.CharField(max_length=8, unique=True)  # Must match WarrantyRegistration number
    description = models.TextField()  # User's claim message
    claimed_at = models.DateTimeField(auto_now_add=True)  # Automatically stores the claim date
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Default to Pending
    response = models.TextField(blank=True, null=True)  # Admin response (optional)

    def __str__(self):
        return f"Claim for Warranty {self.warranty_number} - {self.status}"



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



# Cart Status Choices
CART_STATUS_CHOICES = [
    ('active', 'Active'),
    ('checked_out', 'Checked Out'),
    ('abandoned', 'Abandoned'),
]

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="cart",null=True,blank=True)
    status = models.CharField(max_length=15, choices=CART_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.customer.user.first_name} ({self.status})"


class CartItem(models.Model):
    CART_ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ordered', 'Ordered'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items",null=True,blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    custom_width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    custom_height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    size_unit = models.CharField(max_length=10, choices=SIZE_CHOICES, default='inches')
    design_image = models.URLField(null=True, blank=True)
    # Order Status
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    status = models.CharField(max_length=15, choices=CART_ITEM_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name


ORDER_STATUS_CHOICES = [
    ('ordered', 'Ordered'),
    ('shipped', 'Shipped'),
    ('arrived', 'Arrived'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]

PAYMENT_METHOD_CHOICES = [
    ('cod', 'Cash on Delivery'),
    ('card', 'Credit/Debit Card'),
    ('upi', 'UPI Payment'),
]


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Customer_Address, on_delete=models.CASCADE, related_name="orders")
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='ordered')
    ordered_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivered_date = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.user.first_name} ({self.status})"







