from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
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


# Products Based on category

@api_view(["GET"])
@permission_classes([AllowAny])  # Public API
def filter_products_by_category(request, category_id):
    try:
        # Get all subcategories under the given category
        subcategories = Subcategory.objects.filter(category_id=category_id)

        # Get all products under the filtered subcategories
        products = Product.objects.filter(subcategory__in=subcategories).order_by("-id")  # Latest first

        # Serialize the products
        serializer = ProductSerializer(products, many=True)

        response_data = {
            "total_products": products.count(),
            "products": serializer.data
        }

        return Response(response_data)

    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)




@api_view(["GET"])
@permission_classes([AllowAny])  # Public API
def filter_products_by_subcategory(request, subcategory_id):
    try:
        # Get all products under the given subcategory
        products = Product.objects.filter(subcategory_id=subcategory_id).order_by("-id")  # Latest first

        # Serialize the products
        serializer = ProductSerializer(products, many=True)

        response_data = {
            "total_products": products.count(),
            "products": serializer.data
        }

        return Response(response_data)

    except Subcategory.DoesNotExist:
        return Response({"error": "Subcategory not found"}, status=404)


@api_view(["GET"])
@permission_classes([AllowAny])  # Allow any user to access this endpoint
def get_product_details(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        serializer = DetailedProductSerializer(product, context={"request": request})
        return Response(serializer.data, status=200)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

