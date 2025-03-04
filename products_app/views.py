from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.exceptions import NotFound
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


    response_data = {
        "category_id": category_id,
        "category_name": category.category_name,
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
        # Get the ParentCategory instance, return 404 if not found
        parent_category = get_object_or_404(ParentCategory, id=parent_category_id)

        # Fetch categories that have this parent_category as part of the parent_categories ManyToManyField
        categories = parent_category.child_categories.all()

        # If no categories are found, you might want to handle that gracefully
        if not categories:
            raise NotFound(detail="No categories found for this parent category.")

        # Serialize the categories
        serializer = CategorySerializer(categories, many=True, context={'request': request})

        # Return the response with the parent category details and the associated categories
        return Response({
            "parent_category_id": parent_category.id,
            "parent_category_name": parent_category.name,
            "total_categories": categories.count(),
            "categories": serializer.data
        })




# Product filtered based on parent category id

class ProductListByParentCategory(APIView):
    permission_classes = [AllowAny]  # Public access

    def get(self, request):
        parent_category_id = request.query_params.get('parent_category_id')

        if not parent_category_id:
            return Response({"error": "parent_category_id is required"}, status=400)

        # Fetch the ParentCategory instance, return 404 if not found
        parent_category = get_object_or_404(ParentCategory, id=parent_category_id)

        # Get all categories under this parent category (with the Many-to-Many relationship)
        categories = parent_category.child_categories.all()

        # If no categories exist for the given parent category, return a 404 response
        if not categories:
            raise NotFound(detail="No categories found for this parent category.")

        # Get all products under these categories (products can belong to multiple categories)
        products = Product.objects.filter(categories__in=categories).distinct()

        # Serialize the products
        serializer = ProductSerializer(products, many=True)

        # Return the response with product details
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

        # Fetch the Category instance, return 404 if not found
        category = get_object_or_404(Category, id=category_id)

        # Get all products under this category (products can belong to multiple categories)
        products = Product.objects.filter(categories=category)

        # If no products are found, return a 404 response
        if not products:
            raise NotFound(detail="No products found for this category.")

        # Serialize the products
        serializer = ProductSerializer(products, many=True)

        # Return the response with product details
        return Response({
            "total_products": products.count(),
            "products": serializer.data
        })



# Category and Sub Category list using parent category id

@api_view(['GET'])
def get_categories_and_products_by_parent(request, parent_category_id):
    try:
        # Fetch the ParentCategory by ID, including handling the case when it doesn't exist
        parent_category = ParentCategory.objects.get(id=parent_category_id)

        # Get categories that are associated with the parent category (ManyToMany relationship)
        categories = Category.objects.filter(parent_categories=parent_category)

        category_list = []
        for category in categories:
            # Get all products related to this category
            products = category.products.all()

            # Create a list of product dictionaries
            product_list = [
                {
                    "product_id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "status": product.status.status if product.status else None,
                    "size": product.size,
                    "price": product.price,
                    "image1": product.image1,
                    "image2": product.image2,
                    "image3": product.image3,
                    "image4": product.image4,
                }
                for product in products
            ]

            # Append category and its products to the category list
            category_list.append({
                "category_id": category.id,
                "category_name": category.category_name,
                "description": category.description,
                "category_image": category.category_image,
                "products": product_list
            })

        # Return the response with parent category and related categories/products
        return Response({
            "parent_category_id": parent_category.id,
            "parent_category_name": parent_category.name,
            "description": parent_category.description,
            "parent_category_image":  parent_category.image,
            "categories": category_list
        })

    except ParentCategory.DoesNotExist:
        return Response({"error": "Parent category not found"}, status=404)


@api_view(["GET"])
def search_products(request):
    search_keyword = request.query_params.get("q", "").strip()

    query = Q()
    if search_keyword:
        query |= Q(name__icontains=search_keyword)
        query |= Q(description__icontains=search_keyword)
        query |= Q(size__icontains=search_keyword)
        query |= Q(categories__category_name__icontains=search_keyword)
        query |= Q(categories__parent_categories__name__icontains=search_keyword)

        try:
            price = float(search_keyword)
            query |= Q(price=price)
        except ValueError:
            pass

    products = Product.objects.filter(query).distinct()

    serializer = ProductSearchSerializer(products, many=True)
    return Response(serializer.data)



# Warranty Plans fileterd based on price range

@csrf_exempt
def get_warranty_by_price_range(request, price_range):
    if request.method == "GET":
        try:
            # Try to find the Warranty_plan with the given price_range
            warranty_plan = get_object_or_404(Warranty_plan, price_range=price_range)

            # Prepare response data
            response_data = {
                "year1": float(warranty_plan.year1) if warranty_plan.year1 is not None else None,
                "year2": float(warranty_plan.year2) if warranty_plan.year2 is not None else None,
                "year5": float(warranty_plan.year5) if warranty_plan.year5 is not None else None,
            }

            return JsonResponse(response_data, status=200)

        except Warranty_plan.DoesNotExist:
            return JsonResponse({"error": "No warranty plan found for the given price range."}, status=404)

    return JsonResponse({"error": "Invalid request method. Use GET instead."}, status=405)



class PriceRangeListAPIView(APIView):
    """
    API to return all price ranges from Warranty_plan model.
    """
    def get(self, request):
        # Fetch all warranty plans and return only price_range field
        warranty_plans = Warranty_plan.objects.all().values("price_range")

        return Response({"price_ranges": list(warranty_plans)}, status=status.HTTP_200_OK)


@api_view(['GET'])
def offer_list(request):
    offers = Product_Offer_slider.objects.all().order_by('-date')  # Fetch all offers, latest first
    serializer = ProductOfferSerializer(offers, many=True)
    return Response(serializer.data)


class DesignerRateAPIView(APIView):
    def get(self, request, *args, **kwargs):
        rates = Designer_rate.objects.all()
        serializer = DesignerRateSerializer(rates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



# Banner Images

class BannerImageListView(APIView):
    def get(self, request):
        banners = Banner_Image.objects.all()
        data = [
            {
                'id': banner.id,
                'image_url': banner.image
            }
            for banner in banners
        ]
        return Response(data, status=status.HTTP_200_OK)

# Testimonial

@api_view(['GET'])
def get_all_testimonials(request):
    testimonials = Testimonials.objects.all().order_by('-created_at')  # Fetch all testimonials
    serializer = TestimonialSerializer(testimonials, many=True)  # Serialize data
    return Response(serializer.data)


@api_view(['GET'])
def get_site_visit_amount(request):
    """Returns the amount from the single site_visit record."""
    site_visit_obj = site_visit.objects.first()  # Get the only available site_visit record
    if site_visit_obj:
        return Response({'amount': site_visit_obj.amount})
    return Response({'error': 'No site visit record found'}, status=404)




class ProductPriceView(APIView):
    def post(self, request):
        serializer = ProductPriceSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            width = serializer.validated_data['width']
            height = serializer.validated_data['height']
            unit = serializer.validated_data['unit']
            quantity = serializer.validated_data['quantity']

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            # Unit conversion factors
            unit_conversion = {
                'cm': 1,
                'meter': 100,
                'feet': 30.48,
                'yard': 91.44,
                'inches': 2.54,
                'mm': 0.1
            }

            # Convert provided dimensions to the product's size unit
            if unit != product.size:
                conversion_factor = unit_conversion[unit] / unit_conversion[product.size]
                width_in_product_unit = width * conversion_factor
                height_in_product_unit = height * conversion_factor
            else:
                width_in_product_unit = width
                height_in_product_unit = height

            # Validate dimensions
            if width_in_product_unit < product.min_width:
                max_width_in_unit = product.min_width * (unit_conversion[unit] / unit_conversion[product.size])
                return Response({
                    "error": f"Width is below the minimum allowed value. Minimum width is {product.min_width} {product.size}. "
                             f"Maximum allowed width for this product is {max_width_in_unit:.2f} {unit}."
                }, status=status.HTTP_400_BAD_REQUEST)
            if width_in_product_unit > product.max_width:
                max_width_in_unit = product.max_width * (unit_conversion[unit] / unit_conversion[product.size])
                return Response({
                    "error": f"Width exceeds the maximum allowed value. Maximum width is {product.max_width} {product.size}. "
                             f"Maximum allowed width for this product is {max_width_in_unit:.2f} {unit}."
                }, status=status.HTTP_400_BAD_REQUEST)
            if height_in_product_unit < product.min_height:
                max_height_in_unit = product.min_height * (unit_conversion[unit] / unit_conversion[product.size])
                return Response({
                    "error": f"Height is below the minimum allowed value. Minimum height is {product.min_height} {product.size}. "
                             f"Maximum allowed height for this product is {max_height_in_unit:.2f} {unit}."
                }, status=status.HTTP_400_BAD_REQUEST)
            if height_in_product_unit > product.max_height:
                max_height_in_unit = product.max_height * (unit_conversion[unit] / unit_conversion[product.size])
                return Response({
                    "error": f"Height exceeds the maximum allowed value. Maximum height is {product.max_height} {product.size}. "
                             f"Maximum allowed height for this product is {max_height_in_unit:.2f} {unit}."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Calculate total price
            area_in_product_unit = width_in_product_unit * height_in_product_unit
            price_per_unit_area = product.price / (product.min_width * product.min_height)
            total_price_per_item = area_in_product_unit * price_per_unit_area
            total_price = total_price_per_item * quantity

            return Response({
                "product_id": product_id,
                "width": width,
                "height": height,
                "unit": unit,
                "quantity": quantity,
                "total_price": round(total_price, 2)
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# QUERY PRODUCTS
#
# import re
# from io import BytesIO
# from django.http import HttpResponse
# from openpyxl import Workbook
# from bs4 import BeautifulSoup
# from .models import Product
#
# def export_square_signs_products(request):
#     # Compile regex pattern to match variations of square signs
#     pattern = re.compile(r'square[-_\s]?signs', re.IGNORECASE)
#
#     # Create workbook and worksheet
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "Square Signs Products"
#     # Updated headers with new columns
#     ws.append(['ID', 'Product Name', 'Found Locations', 'Details', 'Frontend URL', 'Backend URL'])
#
#     # Analyze all products
#     for product in Product.objects.all().prefetch_related('categories'):
#         locations = []
#         details = []
#
#         # Check direct image URLs
#         for i in range(1, 5):
#             img_url = getattr(product, f'image{i}')
#             if img_url and pattern.search(img_url):
#                 locations.append(f'Image {i} URL')
#                 details.append(f'Found in Image {i} URL: {img_url}')
#
#         # Check rich text fields and their embedded images
#         rich_text_fields = [
#             ('product_overview', 'Product Overview'),
#             ('product_specifications', 'Product Specifications'),
#             ('installation', 'Installation'),
#         ]
#
#         for field, name in rich_text_fields:
#             content = getattr(product, field)
#             if content:
#                 soup = BeautifulSoup(content, 'html.parser')
#                 text_content = soup.get_text()
#
#                 # Check in text content
#                 for match in pattern.finditer(text_content):
#                     locations.append(f'{name} Text')
#                     start = max(0, match.start() - 50)
#                     end = min(len(text_content), match.end() + 50)
#                     snippet = text_content[start:end].replace('\n', ' ').strip()
#                     details.append(f'Found in {name} Text: "...{snippet}..."')
#
#                 # Check in embedded images
#                 for img in soup.find_all('img'):
#                     src = img.get('src', '')
#                     if src and pattern.search(src):
#                         locations.append(f'{name} Images')
#                         details.append(f'Found in {name} Image: {src}')
#
#         # Add to Excel if matches found
#         if locations:
#             # Generate URLs
#             frontend_url = f"https://www.brandexperts.ae/product/{product.id}/"
#             backend_url = f"https://dash.brandexperts.ae/admin/products_app/product/{product.id}/change/"
#
#             ws.append([
#                 product.id,
#                 product.name or "Unnamed Product",
#                 ', '.join(locations),
#                 '\n'.join(details),
#                 frontend_url,
#                 backend_url
#             ])
#
#     # Save workbook to an in-memory buffer
#     buffer = BytesIO()
#     wb.save(buffer)
#     buffer.seek(0)
#
#     # Create HTTP response
#     response = HttpResponse(
#         buffer.getvalue(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = 'attachment; filename="square_signs_products.xlsx"'
#     return response

from django.db.models import F
class UpdateProductDimensionsView(APIView):
    def post(self, request):
        # Update all products with the new values
        Product.objects.update(
            min_width=10.00,
            min_height=5.00,
            max_width=50.00,
            max_height=100.00
        )

        return Response({"message": "All product dimensions updated to 5.00"}, status=status.HTTP_200_OK)