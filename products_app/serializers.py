from rest_framework import serializers
from .models import *

class CategorySerializer(serializers.ModelSerializer):
    category_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id","category_name", "description", "category_image_url"]

    def get_category_image_url(self, obj):
        request = self.context.get("request")
        if obj.category_image:
            return request.build_absolute_uri(obj.category_image.url)
        return None



class SubcategorySerializer(serializers.ModelSerializer):
    subcategory_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Subcategory
        fields = ["id", "subcategory_name", "description", "subcategory_image_url"]

    def get_subcategory_image_url(self, obj):
        request = self.context.get("request")
        if obj.subcategory_image:
            return request.build_absolute_uri(obj.subcategory_image.url)
        return None


class StandardSizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Standard_sizes
        fields = ['standard_sizes', 'width', 'height']

# Product Serializer
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
            "standard_sizes",
            "price",
        ]


class DetailedProductSerializer(serializers.ModelSerializer):
    parent_category = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    overview = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    installation_steps = serializers.SerializerMethodField()
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
            "standard_sizes",
            "price",
            "parent_category",
            "category",
            "subcategory",
            "overview",
            "specifications",
            "installation_steps",

        ]

    def get_parent_category(self, obj):
        """Retrieve parent category details"""
        if obj.subcategory and obj.subcategory.category and obj.subcategory.category.parent_category:
            parent_category = obj.subcategory.category.parent_category
            return {
                "id": parent_category.id,
                "name": parent_category.name,
                "description": parent_category.description,
                "image": parent_category.image.url if parent_category.image else None
            }
        return None

    def get_category(self, obj):
        """Retrieve category details"""
        if obj.subcategory and obj.subcategory.category:
            category = obj.subcategory.category
            return {
                "id": category.id,
                "name": category.category_name,
                "description": category.description,
                "image": category.category_image.url if category.category_image else None
            }
        return None

    def get_subcategory(self, obj):
        """Retrieve subcategory details"""
        if obj.subcategory:
            return {
                "id": obj.subcategory.id,
                "name": obj.subcategory.subcategory_name,
                "description": obj.subcategory.description,
                "image": obj.subcategory.subcategory_image.url if obj.subcategory.subcategory_image else None
            }
        return None

    def get_overview(self, obj):
        """Retrieve product overviews"""
        overviews = obj.overview.all()
        return [{"heading": o.heading, "description": o.description} for o in overviews]

    def get_specifications(self, obj):
        """Retrieve product specifications"""
        specs = obj.specifications.all()
        return [
            {
                "title": s.title,
                "description": s.description,
                "thickness": s.thickness,
                "material": s.material,
                "weight": s.weight,
                "drilled_holes": s.drilled_holes,
                "min_size": s.min_size,
                "max_size": s.max_size,
                "printing_options": s.printing_options,
                "cutting_options": s.cutting_options,
                "common_sizes": s.common_sizes,
                "installation": s.installation,
                "shape": s.shape,
                "life_span": s.life_span,
            }
            for s in specs
        ]

    def get_installation_steps(self, obj):
        """Retrieve product installation steps with the installation title"""
        installation = Product_installation.objects.filter(product=obj).first()
        if installation:
            steps = Installation_steps.objects.filter(installation=installation)
            return {
                "installation_title": installation.title,
                "steps": [{"step": s.steps} for s in steps]
            }
        return None
    
class ParentCategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ParentCategory
        fields = ['id', 'name', 'description', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None



class CategorySerializer(serializers.ModelSerializer):
    category_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'category_name', 'description', 'category_image_url']

    def get_category_image_url(self, obj):
        request = self.context.get('request')
        if obj.category_image:
            return request.build_absolute_uri(obj.category_image.url) if request else obj.category_image.url
        return None


class SubcategorySerializer(serializers.ModelSerializer):
    subcategory_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Subcategory
        fields = ['id', 'subcategory_name', 'description', 'subcategory_image_url']

    def get_subcategory_image_url(self, obj):
        request = self.context.get('request')
        if obj.subcategory_image:
            return request.build_absolute_uri(obj.subcategory_image.url) if request else obj.subcategory_image.url
        return None


class ProductSerializer_parent_id(serializers.ModelSerializer):
    image1 = serializers.URLField(required=False, allow_null=True)
    image2 = serializers.URLField(required=False, allow_null=True)
    image3 = serializers.URLField(required=False, allow_null=True)
    image4 = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'image1', 'image2', 'image3', 'image4',
            'size', 'standard_size', 'width', 'height', 'price'
        ]