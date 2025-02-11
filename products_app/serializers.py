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


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
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
            "price",
            "standard_size",
            "width",
            "height"
        ]


class DetailedProductSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    overview = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    installation_steps = serializers.SerializerMethodField()

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
            "price",
            "standard_size",
            "width",
            "height",
            "category",
            "subcategory",
            "overview",
            "specifications",
            "installation_steps",
        ]

    def get_category(self, obj):
        if obj.subcategory and obj.subcategory.category:
            return {
                "id": obj.subcategory.category.id,
                "name": obj.subcategory.category.category_name,
                "description": obj.subcategory.category.description,
            }
        return None

    def get_subcategory(self, obj):
        if obj.subcategory:
            return {
                "id": obj.subcategory.id,
                "name": obj.subcategory.subcategory_name,
                "description": obj.subcategory.description,
            }
        return None

    def get_overview(self, obj):
        overviews = obj.overview.all()
        return [{"heading": o.heading, "description": o.description} for o in overviews]

    def get_specifications(self, obj):
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
        installation = Product_installation.objects.filter(product=obj).first()
        if installation:
            steps = Installation_steps.objects.filter(installation=installation)
            return [{"step": s.steps} for s in steps]
        return []

