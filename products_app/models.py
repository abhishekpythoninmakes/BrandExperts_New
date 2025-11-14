from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
# Create your models here.

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True,null=True,blank=True)
    is_admin = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)
    otp = models.CharField(max_length=6,null=True,blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username'], name='unique_username')
        ]

    def __str__(self):
        return self.username


sizes_available =  [
    ('cm', 'Centimeter'),
    ('inches', 'Inches'),
    ('feet', 'Feet'),
    ('yard', 'Yard'),
    ('meter', 'Meter'),
    ('mm', 'Millimeter'),
]


class ParentCategory(models.Model):
    name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    parent_categories = models.ManyToManyField(ParentCategory, blank=True, related_name="child_categories")
    category_name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category_image = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.category_name

class Product_status(models.Model):
    status = models.CharField(max_length=500,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status if self.status else "No Status"




class GlobalThickness(models.Model):
    """Global thickness options that can be used as defaults"""
    size = models.CharField(max_length=50, help_text="Example: 12mm, 1.5cm, etc.")
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=16, decimal_places=6, help_text="Price per unit")
    is_active = models.BooleanField(default=True, help_text="Whether this option is active")

    class Meta:
        verbose_name_plural = "Global Thickness Options"
        ordering = ['price']

    def __str__(self):
        return f"{self.size} - {self.price}"

class GlobalTurnaroundTime(models.Model):
    """Global turnaround time options"""
    name = models.CharField(max_length=50, help_text="Example: Standard, Express, FastTrack")
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Global Turnaround Time Options"
        ordering = ['price_decimal']

    def __str__(self):
        return f"{self.name} - {self.price_percentage}% / {self.price_decimal}"

class GlobalDelivery(models.Model):
    """Global delivery options"""
    name = models.CharField(max_length=50, help_text="Example: Pickup, FastTrack, Express, Standard")
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Global Delivery Options"
        ordering = ['price_decimal']

    def __str__(self):
        return f"{self.name} - {self.price_percentage}% / {self.price_decimal}"

class GlobalInstallationType(models.Model):
    """Global installation options"""
    name = models.CharField(max_length=50, help_text="Example: 5 business days, 8 business days")
    days = models.IntegerField(help_text="Number of business days for installation")
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Global Installation Options"
        ordering = ['days']

    def __str__(self):
        return f"{self.name} ({self.days} days) - {self.price_percentage}% / {self.price_decimal}"

class GlobalDistance(models.Model):
    """Global distance options"""
    km = models.CharField(max_length=50, help_text="Example: 20 km, 50 km, Below 100 km")
    unit = models.CharField(max_length=20, choices=[('km', 'Kilometers'), ('miles', 'Miles')], default='km')
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Global Distance Options"
        ordering = ['price_decimal']

    def __str__(self):
        return f"{self.km} - {self.price_percentage}% / {self.price_decimal}"








class Product(models.Model):
    categories = models.ManyToManyField(Category, blank=True, related_name="products")
    name = models.CharField(max_length=900, null=True, blank=True)
    alternate_names = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    product_overview = RichTextUploadingField(null=True, blank=True)
    product_specifications = RichTextUploadingField(null=True,blank=True)
    installation = RichTextUploadingField(null=True, blank=True)
    image1 = models.URLField(null=True, blank=True)
    image2 = models.URLField(null=True, blank=True)
    image3 = models.URLField(null=True, blank=True)
    image4 = models.URLField(null=True, blank=True)
    min_width = models.DecimalField(max_digits=6, decimal_places=2, default=5.00, help_text="📏 Minimum width")
    min_height = models.DecimalField(max_digits=6, decimal_places=2, default=5.00,help_text="📐 Minimum height")
    max_width = models.DecimalField(max_digits=6, decimal_places=2, default=5.00, help_text="📏 Maximum width")
    max_height = models.DecimalField(max_digits=6, decimal_places=2, default=5.00,help_text="📐 Maximum height")
    size = models.CharField(max_length=100, choices=sizes_available, default='cm',help_text="🛠 Select the measurement unit")
    price = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="💰 This is the variable price based on size and customization."
    )
    fixed_price = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        blank=True
    )
    status = models.ForeignKey(Product_status, on_delete=models.CASCADE, null=True, blank=True)
    amazon_url = models.URLField(null=True, blank=True)
    # New Checkbox Field
    allow_direct_add_to_cart = models.BooleanField(
        default=False,null=True,blank=True,help_text="Allow Direct Add to Cart (Without Customization)")

    stock = models.PositiveIntegerField(null=True,blank=True)

    disable_customization = models.BooleanField(default=False,null=True,blank=True,help_text="Disable Customization")

    def __str__(self):
        return self.name if self.name else "Unnamed Product"

    def clean(self):
        if self.min_width > self.max_width:
            raise ValidationError("Minimum width cannot be greater than maximum width.")
        if self.min_height > self.max_height:
            raise ValidationError("Minimum height cannot be greater than maximum height.")

    def get_available_thicknesses(self):
        """Return product-specific thicknesses or global ones if none exist"""
        if self.thicknesses.exists():
            return self.thicknesses.all()
        return GlobalThickness.objects.filter(is_active=True)

    def get_available_turnaround_times(self):
        """Return product-specific turnaround times or global ones if none exist"""
        if self.turnaround_times.exists():
            return self.turnaround_times.all()
        return GlobalTurnaroundTime.objects.filter(is_active=True)

    def get_available_deliveries(self):
        """Return product-specific deliveries or global ones if none exist"""
        if self.deliveries.exists():
            return self.deliveries.all()
        return GlobalDelivery.objects.filter(is_active=True)

    def get_available_installation_types(self):
        """Return product-specific installation types or global ones if none exist"""
        if self.installation_types.exists():
            return self.installation_types.all()
        return GlobalInstallationType.objects.filter(is_active=True)

    def get_available_distances(self):
        """Return product-specific distances or global ones if none exist"""
        if self.distances.exists():
            return self.distances.all()
        return GlobalDistance.objects.filter(is_active=True)

    def copy_global_options(self):
        """Copy global options to this product if it doesn't have any"""
        if not self.thicknesses.exists():
            for global_thickness in GlobalThickness.objects.filter(is_active=True):
                Thickness.objects.create(
                    product=self,
                    size=global_thickness.size,
                    price=global_thickness.price
                )

        if not self.turnaround_times.exists():
            for global_turnaround in GlobalTurnaroundTime.objects.filter(is_active=True):
                TurnaroundTime.objects.create(
                    product=self,
                    name=global_turnaround.name,
                    description=global_turnaround.description,
                    price_percentage=global_turnaround.price_percentage,
                    price_decimal=global_turnaround.price_decimal
                )

        if not self.deliveries.exists():
            for global_delivery in GlobalDelivery.objects.filter(is_active=True):
                Delivery.objects.create(
                    product=self,
                    name=global_delivery.name,
                    description=global_delivery.description,
                    price_percentage=global_delivery.price_percentage,
                    price_decimal=global_delivery.price_decimal
                )

        if not self.installation_types.exists():
            for global_installation in GlobalInstallationType.objects.filter(is_active=True):
                InstallationType.objects.create(
                    product=self,
                    name=global_installation.name,
                    days=global_installation.days,
                    description=global_installation.description,
                    price_percentage=global_installation.price_percentage,
                    price_decimal=global_installation.price_decimal
                )

        if not self.distances.exists():
            for global_distance in GlobalDistance.objects.filter(is_active=True):
                Distance.objects.create(
                    product=self,
                    km=global_distance.km,
                    unit=global_distance.unit,
                    description=global_distance.description,
                    price_percentage=global_distance.price_percentage,
                    price_decimal=global_distance.price_decimal
                )
                from django.db.models.signals import post_save, post_migrate
                from django.dispatch import receiver
                from django.db import transaction
                @receiver(post_save, sender=Product)
                def create_inventory_stock(sender, instance, created, **kwargs):
                    """
                    Automatically create InventoryStock when a new Product is created
                    """
                    if created:
                        InventoryStock.objects.get_or_create(
                            product=instance,
                            defaults={
                                'current_stock': instance.stock if instance.stock else 0,
                                'low_stock_threshold': 10
                            }
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

                @receiver(post_migrate)
                def create_inventory_stock_for_existing_products(sender, **kwargs):
                    """
                    Create InventoryStock records for existing products after migrations
                    """
                    from products_app.models import Product, InventoryStock

                    # Only run for the products_app
                    if sender.name == 'products_app':
                        with transaction.atomic():
                            # Get products that don't have inventory_stock
                            products_without_inventory = Product.objects.filter(
                                inventory_stock__isnull=True
                            )

                            for product in products_without_inventory:
                                InventoryStock.objects.get_or_create(
                                    product=product,
                                    defaults={
                                        'current_stock': product.stock if product.stock else 0,
                                        'low_stock_threshold': 1
                                    }
                                )
                            print(f"Created InventoryStock for {products_without_inventory.count()} existing products")


class Standard_sizes(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,related_name="standard_sizes",verbose_name="Product")
    standard_sizes = models.CharField(max_length=200, null=True, blank=True,editable=False)
    width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=100, choices=sizes_available, default='cm', help_text="🛠 Select the measurement unit")

    def save(self, *args, **kwargs):
        if self.width is not None and self.height is not None:
            self.standard_sizes = f"{self.width} x {self.height}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.standard_sizes}"



class Thickness(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="thicknesses")
    size = models.CharField(max_length=50, help_text="Example: 12mm, 1.5cm, etc.")
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=16, decimal_places=6, help_text="Price per unit")

    class Meta:
        verbose_name_plural = "Product Thickness Options"
        ordering = ['price']

    def __str__(self):
        return f"{self.size} - {self.price}"

class TurnaroundTime(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="turnaround_times")
    name = models.CharField(max_length=50, help_text="Example: Standard, Express, FastTrack")
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Product Turnaround Time Options"
        ordering = ['price_decimal']

    def __str__(self):
        return f"{self.name} - {self.price_percentage}% / {self.price_decimal}"

class Delivery(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="deliveries")
    name = models.CharField(max_length=50, help_text="Example: Pickup, FastTrack, Express, Standard")
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Product Delivery Options"
        ordering = ['price_decimal']

    def __str__(self):
        return f"{self.name} - {self.price_percentage}% / {self.price_decimal}"

class InstallationType(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="installation_types")
    name = models.CharField(max_length=50, help_text="Example: 5 business days, 8 business days")
    days = models.IntegerField(help_text="Number of business days for installation")
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Product Installation Options"
        ordering = ['days']

    def __str__(self):
        return f"{self.name} ({self.days} days) - {self.price_percentage}% / {self.price_decimal}"

class Distance(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="distances")
    km = models.CharField(max_length=50, help_text="Example: 20 km, 50 km, Below 100 km")
    unit = models.CharField(max_length=20, choices=[('km', 'Kilometers'), ('miles', 'Miles')], default='km')
    description = models.TextField(null=True, blank=True)
    price_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_decimal = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Product Distance Options"
        ordering = ['price_decimal']

    def __str__(self):
        return f"{self.km} - {self.price_percentage}% / {self.price_decimal}"
























# Warranty Plan

class Warranty_plan(models.Model):
    start_price_range = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    end_price_range = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_range = models.CharField(max_length=500, null=True, blank=True,editable=False)
    year1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year5 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def format_price(self, price):
        """Formats price to include 'K' for thousands and 'M' for millions."""
        if price >= 1_000_000:
            return f"{price / 1_000_000:.0f}M"
        elif price >= 1_000:
            return f"{price / 1_000:.0f}K"
        return str(int(price))  # No suffix for values below 1000

    def save(self, *args, **kwargs):
        if self.start_price_range is not None and self.end_price_range is not None:
            start_formatted = self.format_price(self.start_price_range)
            end_formatted = self.format_price(self.end_price_range)
            self.price_range = f"{start_formatted} - {end_formatted}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.price_range if self.price_range else "No Price Range"



class VAT(models.Model):
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # Standard VAT %
    is_inclusive = models.BooleanField(default=False)  # True = VAT included in product price, False = VAT added separately

    def __str__(self):
        return f"VAT {self.percentage}% ({'Inclusive' if self.is_inclusive else 'Exclusive'})"


class Higher_designer(models.Model):
    designer_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)



class Product_Offer_slider(models.Model):

     offer_details = models.CharField(max_length=500, null=True, blank=True)
     date = models.DateTimeField(auto_now_add=True)

     def short_offer_details(self):
         return " ".join(self.offer_details.split()[:10]) + ("..." if len(self.offer_details.split()) > 10 else "")

     short_offer_details.short_description = "Offer Details"  # Custom column name in admin

     def __str__(self):
         return self.short_offer_details()


class Designer_rate(models.Model):
    RATE_TYPE_CHOICES = [
        ('hour', 'Per Hour'),
        ('day', 'Per Day'),
        ('week', 'Per Week'),
        ('month', 'Per Month'),
    ]

    rate_type = models.CharField(max_length=10, choices=RATE_TYPE_CHOICES, default='hour')
    hours = models.PositiveIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Designer Rate: {self.hours} {self.get_rate_type_display()} - {self.amount}"



class Banner_Image(models.Model):
    name = models.CharField(max_length=500,null=True,blank=True)
    image = models.URLField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner Image {self.name} {self.created_at}"


class Testimonials(models.Model):
    name = models.CharField(max_length=500,null=True,blank=True)
    occupation = models.CharField(max_length=500,null=True,blank=True)
    image = models.URLField(null=True,blank=True)
    description = models.TextField(null=True,blank=True)
    rating = models.PositiveIntegerField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial {self.name} {self.created_at}"


class site_visit(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.amount}'



# Inventory Stock Management

class InventoryStock(models.Model):
    """
    Inventory stock management for products
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_stock'
    )
    current_stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    last_restocked = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Track stock movements
    total_restocked = models.PositiveIntegerField(default=0)
    total_sold = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Inventory Stocks"
        ordering = ['current_stock']  # Default order by lowest stock first

    def __str__(self):
        return f"{self.product.name} - Stock: {self.current_stock}"

    @property
    def is_low_stock(self):
        """Check if stock is below threshold"""
        return self.current_stock <= self.low_stock_threshold

    @property
    def stock_status(self):
        """Get stock status"""
        if self.current_stock == 0:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        else:
            return 'in_stock'

    def reduce_stock(self, quantity):
        """Reduce stock by given quantity"""
        if self.current_stock >= quantity:
            self.current_stock -= quantity
            self.total_sold += quantity
            self.save()
            return True
        return False

    def restore_stock(self, quantity):
        """Restore/Add stock by given quantity"""
        self.current_stock += quantity
        self.total_restocked += quantity
        self.save()
        return True