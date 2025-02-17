from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


sizes_available =  (('inches','Inches'),('feet','Feet'))


class ParentCategory(models.Model):
    name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='parent_category_images', null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    parent_category = models.ForeignKey(ParentCategory, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name="categories")
    category_name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category_image = models.ImageField(upload_to='category_images', null=True, blank=True)

    def __str__(self):
        return self.category_name

class Product_status(models.Model):
    status = models.CharField(max_length=500,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status if self.status else "No Status"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="products")
    name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    product_overview = RichTextUploadingField(null=True, blank=True)
    product_specifications = RichTextUploadingField(null=True,blank=True)
    installation = RichTextUploadingField(null=True, blank=True)
    image1 = models.URLField(null=True, blank=True)
    image2 = models.URLField(null=True, blank=True)
    image3 = models.URLField(null=True, blank=True)
    image4 = models.URLField(null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True, choices=sizes_available, default='inches')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.ForeignKey(Product_status, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name if self.name else "Unnamed Product"


class Standard_sizes(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,related_name="standard_sizes")
    standard_sizes = models.CharField(max_length=200, null=True, blank=True,editable=False)
    width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.width is not None and self.height is not None:
            self.standard_sizes = f"{self.width} x {self.height}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.standard_sizes}"



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





