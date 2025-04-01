from rest_framework import serializers
from .models import *

class CategorySerializer(serializers.ModelSerializer):
    parent_category_names = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id","category_name", "description", "category_image","parent_category_names"]





class StandardSizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Standard_sizes
        fields = ['standard_sizes', 'width', 'height','unit']

# Product Serializer
from django.conf import settings
from rest_framework import serializers
from .models import Product, Category, ParentCategory
from .serializers import StandardSizesSerializer


class ProductSerializer(serializers.ModelSerializer):
    standard_sizes = StandardSizesSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "image1",
            "image2",
            "image3",
            "image4",
            "max_width",
            "max_height",
            "min_width",
            "min_height",
            "standard_sizes",
            "price",
            "allow_direct_add_to_cart",
            "disable_customization",
            "amazon_url",
        ]


class DetailedProductSerializer(serializers.ModelSerializer):
    parent_category = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    product_overview = serializers.SerializerMethodField()  # Convert relative image URLs
    product_specifications = serializers.SerializerMethodField()  # Convert relative image URLs
    installation = serializers.SerializerMethodField()  # Convert relative image URLs
    standard_sizes = StandardSizesSerializer(many=True, read_only=True)
    status = serializers.CharField(source="status.status", allow_null=True)  # Get status name
    amazon_url = serializers.SerializerMethodField()
    allow_direct_add_to_cart = serializers.BooleanField()
    disable_customization = serializers.BooleanField()
    
    # New fields for product options
    thickness_options = serializers.SerializerMethodField()
    turnaround_options = serializers.SerializerMethodField()
    delivery_options = serializers.SerializerMethodField()
    installation_options = serializers.SerializerMethodField()
    distance_options = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "product_overview",
            "product_specifications",
            "installation",
            "image1",
            "image2",
            "image3",
            "image4",
            "max_width",
            "max_height",
            "min_width",
            "min_height",
            "size",
            "amazon_url",
            "standard_sizes",
            "price",
            "fixed_price",
            "parent_category",
            "category",
            "status",
            "allow_direct_add_to_cart",
            "disable_customization",
            "thickness_options",
            "turnaround_options",
            "delivery_options",
            "installation_options",
            "distance_options",
        ]

    def get_absolute_html(self, content):
        """Convert relative media URLs to absolute URLs in HTML fields."""
        if content:
            request = self.context.get("request")
            domain = request.build_absolute_uri("/")[:-1] if request else settings.SITE_URL
            return content.replace('src="/media/', f'src="{domain}/media/')
        return None

    def get_product_overview(self, obj):
        return self.get_absolute_html(obj.product_overview)

    def get_product_specifications(self, obj):
        return self.get_absolute_html(obj.product_specifications)

    def get_installation(self, obj):
        return self.get_absolute_html(obj.installation)

    def get_parent_category(self, obj):
        """Retrieve parent category details"""
        parent_categories = []
        if obj.categories.exists():
            for category in obj.categories.all():
                if category.parent_categories.exists():
                    for parent_category in category.parent_categories.all():
                        parent_categories.append({
                            "id": parent_category.id,
                            "name": parent_category.name,
                            "description": parent_category.description,
                            "image": parent_category.image
                        })
        return parent_categories if parent_categories else None

    def get_category(self, obj):
        """Retrieve category details"""
        categories = []
        if obj.categories.exists():
            for category in obj.categories.all():
                categories.append({
                    "id": category.id,
                    "name": category.category_name,
                    "description": category.description,
                    "image": category.category_image
                })
        return categories if categories else None
    def get_amazon_url(self, obj):  # This method should exist
        return obj.amazon_url if obj.amazon_url else ""

    def get_thickness_options(self, obj):
        """Get product-specific thickness options or global ones if none exist"""
        thicknesses = obj.thicknesses.all() if obj.thicknesses.exists() else GlobalThickness.objects.filter(is_active=True)
        return [
            {
                "id": t.id,
                "size": t.size,
                "price": str(t.price)
            }
            for t in thicknesses
        ] if thicknesses.exists() else None

    def get_turnaround_options(self, obj):
        """Get product-specific turnaround options or global ones if none exist"""
        turnarounds = obj.turnaround_times.all() if obj.turnaround_times.exists() else GlobalTurnaroundTime.objects.filter(is_active=True)
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "price_percentage": str(t.price_percentage) if t.price_percentage else None,
                "price_decimal": str(t.price_decimal) if t.price_decimal else None
            }
            for t in turnarounds
        ] if turnarounds.exists() else None

    def get_delivery_options(self, obj):
        """Get product-specific delivery options or global ones if none exist"""
        deliveries = obj.deliveries.all() if obj.deliveries.exists() else GlobalDelivery.objects.filter(is_active=True)
        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "price_percentage": str(d.price_percentage) if d.price_percentage else None,
                "price_decimal": str(d.price_decimal) if d.price_decimal else None
            }
            for d in deliveries
        ] if deliveries.exists() else None

    def get_installation_options(self, obj):
        """Get product-specific installation options or global ones if none exist"""
        installations = obj.installation_types.all() if obj.installation_types.exists() else GlobalInstallationType.objects.filter(is_active=True)
        return [
            {
                "id": i.id,
                "name": i.name,
                "days": i.days,
                "description": i.description,
                "price_percentage": str(i.price_percentage) if i.price_percentage else None,
                "price_decimal": str(i.price_decimal) if i.price_decimal else None
            }
            for i in installations
        ] if installations.exists() else None

    def get_distance_options(self, obj):
        """Get product-specific distance options or global ones if none exist"""
        distances = obj.distances.all() if obj.distances.exists() else GlobalDistance.objects.filter(is_active=True)
        return [
            {
                "id": d.id,
                "km": d.km,
                "unit": d.unit,
                "description": d.description,
                "price_percentage": str(d.price_percentage) if d.price_percentage else None,
                "price_decimal": str(d.price_decimal) if d.price_decimal else None
            }
            for d in distances
        ] if distances.exists() else None


    
class ParentCategorySerializer(serializers.ModelSerializer):


    class Meta:
        model = ParentCategory
        fields = ['id', 'name', 'description', 'image']





class CategorySerializer(serializers.ModelSerializer):


    class Meta:
        model = Category
        fields = ['id', 'category_name', 'description', 'category_image']






class ProductSerializer_parent_id(serializers.ModelSerializer):
    image1 = serializers.URLField(required=False, allow_null=True)
    image2 = serializers.URLField(required=False, allow_null=True)
    image3 = serializers.URLField(required=False, allow_null=True)
    image4 = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'image1', 'image2', 'image3', 'image4',
            'size', 'standard_size', 'width', 'height', 'price','fixed_price',
        ]

class ProductSearchSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "image_url", "price","fixed_price","size", "description"]

    def get_image_url(self, obj):
        """Return the URL of the first image (image1)."""
        return obj.image1 if obj.image1 else None


class ProductOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_Offer_slider
        fields = ['id', 'offer_details', 'date']



class DesignerRateSerializer(serializers.ModelSerializer):
    rate_type_display = serializers.CharField(source='get_rate_type_display', read_only=True)
    rate_value = serializers.SerializerMethodField()

    class Meta:
        model = Designer_rate
        fields = ['id','rate_type', 'rate_type_display', 'hours', 'amount', 'rate_value']

    def get_rate_value(self, obj):
        """Calculate the rate based on rate type (hour, day, week, month)."""
        if not obj.amount or obj.amount <= 0:
            return 0

        conversion_factors = {
            'hour': obj.hours if obj.hours and obj.hours > 0 else 1,  # Avoid division by zero
            'day': 8,   # Assuming a day has 8 hours
            'week': 40,  # Assuming a week has 40 hours
            'month': 160 # Assuming a month has 160 hours
        }

        hours_per_unit = conversion_factors.get(obj.rate_type, 1)  # Default to 1 if invalid type

        return round(obj.amount / hours_per_unit, 2)


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonials
        fields = ['id', 'name', 'occupation', 'image', 'created_at', 'description', 'rating']


class ProductPriceSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    width = serializers.DecimalField(max_digits=6, decimal_places=2)
    height = serializers.DecimalField(max_digits=6, decimal_places=2)
    unit = serializers.CharField(max_length=10)
    quantity = serializers.IntegerField(min_value=1)

    def validate_unit(self, value):
        valid_units = ['cm', 'meter', 'feet', 'yard', 'inches', 'mm']
        if value not in valid_units:
            raise serializers.ValidationError(f"Invalid unit. Valid units are: {', '.join(valid_units)}")
        return value



class ProductBasicDetailSerializer(serializers.ModelSerializer):
    size = serializers.CharField(source='get_size_display')  # To get the display value of the choice field

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'size', 'max_width', 'max_height',
            'price','fixed_price', 'image1'
        ]