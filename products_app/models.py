from django.db import models
from django.contrib.auth.models import AbstractUser

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


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="subcategories")
    subcategory_name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    subcategory_image = models.ImageField(upload_to='subcategory_images', null=True, blank=True)

    def __str__(self):
        return self.subcategory_name


class Product(models.Model):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="products")
    name = models.CharField(max_length=900, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image1 = models.URLField(null=True, blank=True)
    image2 = models.URLField(null=True, blank=True)
    image3 = models.URLField(null=True, blank=True)
    image4 = models.URLField(null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True, choices=sizes_available, default='inches')
    standard_size = models.CharField(max_length=500, null=True, blank=True)

    # Dimensions
    width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Product"


class Product_overview(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True,related_name="overview")
    heading = models.CharField(max_length=900,null=True,blank=True)
    description = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.heading}" if self.product else "No Overview"

class Product_specifications(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True,related_name="specifications")
    title = models.CharField(max_length=900,null=True,blank=True)
    description = models.CharField(max_length=900,null=True,blank=True)
    thickness = models.CharField(max_length=900,null=True,blank=True)
    material = models.CharField(max_length=900,null=True,blank=True)
    weight = models.CharField(max_length=900,null=True,blank=True)
    drilled_holes = models.CharField(max_length=900,null=True,blank=True)
    min_size = models.CharField(max_length=900,null=True,blank=True)
    max_size = models.CharField(max_length=900,null=True,blank=True)
    printing_options = models.CharField(max_length=900,null=True,blank=True)
    cutting_options = models.CharField(max_length=900,null=True,blank=True)
    common_sizes = models.CharField(max_length=900,null=True,blank=True)
    installation = models.CharField(max_length=900,null=True,blank=True)
    shape = models.CharField(max_length=900,null=True,blank=True)
    life_span = models.CharField(max_length=900,null=True,blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.title}" if self.product else "No Specifications"

class Product_installation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=900,null=True,blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.title}" if self.product else "No installation"

class Installation_steps(models.Model):
    installation = models.ForeignKey(Product_installation,on_delete=models.CASCADE,null=True,blank=True)
    steps = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.installation.title} - {self.steps[:50]}" if self.installation else "No installation steps"







