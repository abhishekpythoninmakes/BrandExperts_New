from django.db import models
from products_app .models import CustomUser , Product ,Warranty_plan,Designer_rate
import random
import string

# Create your models here.
customer_status = (('lead','LEAD'),('client','CLIENT'))

# Customer Registration

class Customer(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    mobile = models.CharField(max_length=20,null=True,blank=True)
    status = models.CharField(max_length=300,null=True,blank=True,choices=customer_status,default='lead')

    def __str__(self):
        return self.user.username if self.user else "Unknown Customer"



class WarrantyRegistration(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    invoice_number = models.CharField(max_length=900, null=True, blank=True)
    invoice_date = models.DateField()
    invoice_value = models.ForeignKey(Warranty_plan,on_delete=models.CASCADE,null=True,blank=True)
    invoice_file = models.URLField(blank=True, null=True)
    warranty_plan_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True,default='0.00')
    warranty_number = models.CharField(max_length=8, unique=True,null=True,blank=True)  # Unique warranty number
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
        warranty_plan = self.invoice_value.price_range if self.invoice_value else "No Warranty Plan"
        return f"{self.full_name} - {self.invoice_number} ({warranty_plan})"


class ClaimWarranty(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    warranty_number = models.CharField(max_length=8)  # Must match WarrantyRegistration number
    description = models.TextField()  # User's claim message
    claimed_at = models.DateTimeField(auto_now_add=True)  # Automatically stores the claim date
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Default to Pending
    response = models.TextField(blank=True, null=True)  # Admin response (optional)

    def __str__(self):
        return f"Claim for Warranty {self.warranty_number} - {self.status}"


countrys = (
    ('UAE', 'UAE'),
    ('Oman', 'OMAN'),
    ('Bahrain', 'BAHRAIN'),
    ('Qatar','QATAR'),
    ('Saudi Arabia','SAUDI ARABIA'),
    ('Kuwait', 'KUWAIT')
)


class Customer_Address(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,blank=True)
    company_name = models.CharField(max_length=500, null=True, blank=True)
    ext = models.CharField(max_length=500, null=True, blank=True)
    address_line1 = models.CharField(max_length=900, null=True, blank=True)
    address_line2 = models.CharField(max_length=900, null=True, blank=True)
    country = models.CharField(max_length=500,null=True,blank=True,choices=countrys)
    city = models.CharField(max_length=900, null=True, blank=True)
    state = models.CharField(max_length=900, null=True, blank=True)
    zip_code = models.CharField(max_length=50,null=True,blank=True)

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
    higher_designer = models.BooleanField(default=False, null=True, blank=True)
    site_visit = models.BooleanField(default=False, null=True, blank=True)

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
    hire_designer = models.ForeignKey(Designer_rate,on_delete=models.CASCADE,null=True,blank=True)
    design_description = models.TextField(null=True,blank=True)

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
    payment_status = models.CharField(max_length=100,null=True,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivered_date = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    transaction_id = models.CharField(max_length=100,null=True,blank=True)
    higher_designer = models.BooleanField(default=False, null=True, blank=True)
    site_visit = models.BooleanField(default=False, null=True, blank=True)
    site_visit_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f"Order {self.id} - {self.customer.user.first_name} ({self.status})"




# OTP RECORDS
class OTPRecord(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=20)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"OTP for {self.email}"






# Test Model

# class TestModel(models.Model):
#     text = models.TextField(null=True,blank=True)
#     response = models.TextField(null=True, blank=True)
#     image = models.URLField(null=True,blank=True)
#     download_image = models.ImageField(upload_to='test_images',null=True,blank=True)
#     camera = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     longitude = models.CharField(max_length=100,null=True,blank=True)
#     lattitude = models.CharField(max_length=100,null=True,blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return self.text









