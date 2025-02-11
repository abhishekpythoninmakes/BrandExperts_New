from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .serializers import *
from .models import *
# Create your views here.

def dashboard(request):
    return render(request,'dashboard.html')

def category(request):
    cats = Category.objects.all().order_by('-id')
    return render(request,'category.html',{'cats':cats})

@csrf_exempt
def add_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category_name")
        description = request.POST.get("description")
        category_image = request.FILES.get("category_image", None)

        category = Category(category_name=category_name, description=description, category_image=category_image)
        category.save()

        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def update_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('id')
        category_name = request.POST.get('category_name')
        description = request.POST.get('description')
        category_image = request.FILES.get('category_image')

        try:
            category = Category.objects.get(id=category_id)
            category.category_name = category_name
            category.description = description
            if category_image:
                category.category_image = category_image
            category.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_category(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        category.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def subcategory(request):
    return render(request,'subcategory.html')

def products(request):
    return render(request,'products.html')




# CATEGORY API VIEW
@api_view(["GET"])
@permission_classes([AllowAny])  # This allows public access to the API
def list_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True, context={"request": request})

    response_data = {
        "total_categories": categories.count(),
        "categories": serializer.data
    }

    return Response(response_data)


# SUB CATEGORY LIST
@api_view(["GET"])
@permission_classes([AllowAny])
def list_subcategories(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)

    subcategories = Subcategory.objects.filter(category=category)
    serializer = SubcategorySerializer(subcategories, many=True, context={"request": request})

    response_data = {
        "category_id": category_id,
        "category_name": category.category_name,
        "total_subcategories": subcategories.count(),
        "subcategories": serializer.data
    }

    return Response(response_data)


# Product List

@api_view(["GET"])
@permission_classes([AllowAny])  # This makes the API publicly accessible
def list_products(request):
    products = Product.objects.all().order_by("-id")  # Latest first
    serializer = ProductSerializer(products, many=True)

    response_data = {
        "total_products": products.count(),
        "products": serializer.data
    }

    return Response(response_data)




@api_view(["GET"])
@permission_classes([AllowAny])  # Allow any user to access this endpoint
def get_product_details(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        serializer = DetailedProductSerializer(product, context={"request": request})
        return Response(serializer.data, status=200)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)



# Parent Category

class ParentCategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        parent_categories = ParentCategory.objects.all()
        serializer = ParentCategorySerializer(parent_categories, many=True, context={'request': request})
        return Response(serializer.data)


# Category by parent category id

class CategoryByParentView(APIView):
    permission_classes = [AllowAny]  # Allow public access

    def get(self, request, parent_category_id):
        parent_category = get_object_or_404(ParentCategory, id=parent_category_id)
        categories = parent_category.categories.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})

        return Response({
            "parent_category_id": parent_category.id,
            "parent_category_name": parent_category.name,
            "total_categories": categories.count(),
            "categories": serializer.data
        })


# Subcategory List using category id and parent category id

class SubcategoryListView(APIView):
    permission_classes = [AllowAny]  # Public access

    def get(self, request):
        parent_category_id = request.query_params.get('parent_category_id')
        category_id = request.query_params.get('category_id')

        if parent_category_id:
            parent_category = get_object_or_404(ParentCategory, id=parent_category_id)
            categories = parent_category.categories.all()
            subcategories = Subcategory.objects.filter(category__in=categories)
        elif category_id:
            category = get_object_or_404(Category, id=category_id)
            subcategories = category.subcategories.all()
        else:
            return Response({"error": "Please provide either parent_category_id or category_id."}, status=400)

        serializer = SubcategorySerializer(subcategories, many=True, context={'request': request})

        return Response({
            "total_subcategories": subcategories.count(),
            "subcategories": serializer.data
        })




# Product filtered based on parent category id

class ProductListByParentCategory(APIView):
    permission_classes = [AllowAny]  # Public access

    def get(self, request):
        parent_category_id = request.query_params.get('parent_category_id')

        if not parent_category_id:
            return Response({"error": "parent_category_id is required"}, status=400)

        parent_category = get_object_or_404(ParentCategory, id=parent_category_id)

        # Get all categories under this parent category
        categories = parent_category.categories.all()

        # Get all subcategories under these categories
        subcategories = [subcategory for category in categories for subcategory in category.subcategories.all()]

        # Get all products under these subcategories
        products = Product.objects.filter(subcategory__in=subcategories)

        serializer = ProductSerializer(products, many=True)

        return Response({
            "total_products": products.count(),
            "products": serializer.data
        })


# Product list based on category id

class ProductListByCategory(APIView):
    permission_classes = [AllowAny]  # Public access

    def get(self, request):
        category_id = request.query_params.get('category_id')

        if not category_id:
            return Response({"error": "category_id is required"}, status=400)

        category = get_object_or_404(Category, id=category_id)

        # Get all subcategories under this category
        subcategories = category.subcategories.all()

        # Get all products under these subcategories
        products = Product.objects.filter(subcategory__in=subcategories)

        serializer = ProductSerializer(products, many=True)

        return Response({
            "total_products": products.count(),
            "products": serializer.data
        })


#  Product list by Sub category id

class ProductListBySubcategory(APIView):
    permission_classes = [AllowAny]  # Public access

    def get(self, request):
        subcategory_id = request.query_params.get('subcategory_id')

        if not subcategory_id:
            return Response({"error": "subcategory_id is required"}, status=400)

        subcategory = get_object_or_404(Subcategory, id=subcategory_id)

        # Get all products under this subcategory
        products = Product.objects.filter(subcategory=subcategory)

        serializer = ProductSerializer(products, many=True)

        return Response({
            "total_products": products.count(),
            "products": serializer.data
        })