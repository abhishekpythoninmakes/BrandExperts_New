from decimal import Decimal
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
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
        query |= Q(alternate_names__icontains=search_keyword)
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
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        width = serializer.validated_data['width']
        height = serializer.validated_data['height']
        unit = serializer.validated_data['unit']
        quantity = serializer.validated_data['quantity']
        thickness_id = serializer.validated_data.get('thickness_id')
        turnaround_id = serializer.validated_data.get('turnaround_id')
        delivery_id = serializer.validated_data.get('delivery_id')
        installation_type_id = serializer.validated_data.get('installation_type_id')
        distance_id = serializer.validated_data.get('distance_id')

        print(f"product id = {product_id}, width = {width}, height = {height}, unit = {unit}, quantity = {quantity}")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        unit_conversion = {
            'cm': Decimal('1'),
            'meter': Decimal('100'),
            'feet': Decimal('30.48'),
            'yard': Decimal('91.44'),
            'inches': Decimal('2.54'),
            'mm': Decimal('0.1')
        }

        product_unit = product.size
        if not product.disable_customization:
        # Validate dimensions against product's min/max (converted to user's unit)
            product_min_width_in_unit = product.min_width * (unit_conversion[product_unit] / unit_conversion[unit])
            product_max_width_in_unit = product.max_width * (unit_conversion[product_unit] / unit_conversion[unit])
            product_min_height_in_unit = product.min_height * (unit_conversion[product_unit] / unit_conversion[unit])
            product_max_height_in_unit = product.max_height * (unit_conversion[product_unit] / unit_conversion[unit])

            if width < product_min_width_in_unit:
                error_msg = f"Width is below the minimum allowed value. Minimum width is {product_min_width_in_unit:.2f} {unit}."
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            if width > product_max_width_in_unit:
                error_msg = f"Width exceeds the maximum allowed value. Maximum width is {product_max_width_in_unit:.2f} {unit}."
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            if height < product_min_height_in_unit:
                error_msg = f"Height is below the minimum allowed value. Minimum height is {product_min_height_in_unit:.2f} {unit}."
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            if height > product_max_height_in_unit:
                error_msg = f"Height exceeds the maximum allowed value. Maximum height is {product_max_height_in_unit:.2f} {unit}."
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        # Convert dimensions to product's unit for pricing calculation
        width_in_product_unit = width * (unit_conversion[unit] / unit_conversion[product_unit])
        height_in_product_unit = height * (unit_conversion[unit] / unit_conversion[product_unit])
        area_in_product_unit_sq = width_in_product_unit * height_in_product_unit

        # Calculate base price based on product's unit squared
        fixed_price = product.fixed_price if product.fixed_price else Decimal('0')
        pro_price = product.price if product.price else Decimal('0')
        base_price_per_item = (area_in_product_unit_sq * pro_price) + fixed_price
        base_total_price = base_price_per_item * quantity

        # Initialize response with breakdown
        price_breakdown = {
            "base_price": round(base_total_price, 2),
        }

        # Initialize additional cost
        additional_cost = Decimal('0')

        # Get thickness details if provided
        if thickness_id:
            try:
                # First check if product has specific thickness
                thickness_details = Thickness.objects.filter(product=product, id=thickness_id).first()

                # If not found, check global thickness
                if not thickness_details:
                    thickness_details = GlobalThickness.objects.get(id=thickness_id)

                # Calculate thickness price based on percentage or fixed price
                thickness_price = Decimal('0')

                # Commenting out thickness calculation for now as per request
                """
                if thickness_details.price_percentage and thickness_details.price_percentage != Decimal('0'):
                    # Calculate percentage of base price
                    thickness_price = (base_total_price * thickness_details.price_percentage) / Decimal('100')
                elif thickness_details.price and thickness_details.price != Decimal('0'):
                    # Use fixed price
                    thickness_price = thickness_details.price * area_in_product_unit_sq * quantity
                """

                additional_cost += thickness_price
                price_breakdown["thickness"] = {
                    "id": thickness_id,
                    "size": thickness_details.size,
                    "price": round(thickness_price, 2)
                }
            except (Thickness.DoesNotExist, GlobalThickness.DoesNotExist):
                return Response({"error": f"Thickness with ID {thickness_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Get turnaround time details if provided
        if turnaround_id:
            try:
                # Check product-specific first
                turnaround = TurnaroundTime.objects.filter(product=product, id=turnaround_id).first()

                # If not found, check global
                if not turnaround:
                    turnaround = GlobalTurnaroundTime.objects.get(id=turnaround_id)

                turnaround_price = Decimal('0')
                # Calculate based on percentage if available and not zero
                if turnaround.price_percentage and turnaround.price_percentage != Decimal('0'):
                    turnaround_price = (base_total_price * turnaround.price_percentage) / Decimal('100')
                # Add fixed price if available and not zero
                elif turnaround.price_decimal and turnaround.price_decimal != Decimal('0'):
                    turnaround_price = turnaround.price_decimal

                additional_cost += turnaround_price
                price_breakdown["turnaround_time"] = {
                    "id": turnaround_id,
                    "name": turnaround.name,
                    "price": round(turnaround_price, 2)
                }
            except (TurnaroundTime.DoesNotExist, GlobalTurnaroundTime.DoesNotExist):
                return Response({"error": f"Turnaround time with ID {turnaround_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Get delivery details if provided
        if delivery_id:
            try:
                # Check product-specific first
                delivery = Delivery.objects.filter(product=product, id=delivery_id).first()

                # If not found, check global
                if not delivery:
                    delivery = GlobalDelivery.objects.get(id=delivery_id)

                delivery_price = Decimal('0')
                # Calculate based on percentage if available and not zero
                if delivery.price_percentage and delivery.price_percentage != Decimal('0'):
                    delivery_price = (base_total_price * delivery.price_percentage) / Decimal('100')
                # Add fixed price if available and not zero
                elif delivery.price_decimal and delivery.price_decimal != Decimal('0'):
                    delivery_price = delivery.price_decimal

                additional_cost += delivery_price
                price_breakdown["delivery"] = {
                    "id": delivery_id,
                    "name": delivery.name,
                    "price": round(delivery_price, 2)
                }
            except (Delivery.DoesNotExist, GlobalDelivery.DoesNotExist):
                return Response({"error": f"Delivery with ID {delivery_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Get installation type details if provided
        if installation_type_id:
            try:
                # Check product-specific first
                installation = InstallationType.objects.filter(product=product, id=installation_type_id).first()

                # If not found, check global
                if not installation:
                    installation = GlobalInstallationType.objects.get(id=installation_type_id)

                installation_price = Decimal('0')
                # Calculate based on percentage if available and not zero
                if installation.price_percentage and installation.price_percentage != Decimal('0'):
                    installation_price = (base_total_price * installation.price_percentage) / Decimal('100')
                # Add fixed price if available and not zero
                elif installation.price_decimal and installation.price_decimal != Decimal('0'):
                    installation_price = installation.price_decimal

                additional_cost += installation_price
                price_breakdown["installation"] = {
                    "id": installation_type_id,
                    "name": installation.name,
                    "days": installation.days,
                    "price": round(installation_price, 2)
                }
            except (InstallationType.DoesNotExist, GlobalInstallationType.DoesNotExist):
                return Response({"error": f"Installation type with ID {installation_type_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Get distance details if provided
        if distance_id:
            try:
                # Check product-specific first
                distance = Distance.objects.filter(product=product, id=distance_id).first()

                # If not found, check global
                if not distance:
                    distance = GlobalDistance.objects.get(id=distance_id)

                distance_price = Decimal('0')
                # Calculate based on percentage if available and not zero
                if distance.price_percentage and distance.price_percentage != Decimal('0'):
                    distance_price = (base_total_price * distance.price_percentage) / Decimal('100')
                # Add fixed price if available and not zero
                elif distance.price_decimal and distance.price_decimal != Decimal('0'):
                    distance_price = distance.price_decimal

                additional_cost += distance_price
                price_breakdown["distance"] = {
                    "id": distance_id,
                    "km": distance.km,
                    "unit": distance.unit,
                    "price": round(distance_price, 2)
                }
            except (Distance.DoesNotExist, GlobalDistance.DoesNotExist):
                return Response({"error": f"Distance with ID {distance_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Calculate total price
        total_price = base_total_price + additional_cost

        return Response({
            "product_id": product_id,
            "width": width,
            "height": height,
            "unit": unit,
            "quantity": quantity,
            "area": round(area_in_product_unit_sq, 2),
            "price_breakdown": price_breakdown,
            "additional_cost": round(additional_cost, 2),
            "total_price_without_rounded": total_price,
            "total_price": round(total_price, 2)
        })

class ProductBasicDetailView(APIView):
    def get(self, request, *args, **kwargs):
        products = Product.objects.all().order_by('-id')
        serializer = ProductBasicDetailSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            max_height=100.00,
            size = 'cm'
        )

        return Response({"message": "All product dimensions updated to 5.00"}, status=status.HTTP_200_OK)


# New Product APIS

from .serializers import NewParentCategorySerializer, NewCategorySerializer


# Parent Category CRUD Operations

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def parent_category_list_create(request):
    """
    List all parent categories or create a new parent category
    """
    if request.method == 'GET':
        parent_categories = ParentCategory.objects.all()
        serializer = NewParentCategorySerializer(parent_categories, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    elif request.method == 'POST':
        # Only admin users can create parent categories
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Permission denied. Only admin users can create parent categories."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = NewParentCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Parent category created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def parent_category_detail(request, pk):
    """
    Retrieve, update or delete a parent category instance
    """
    try:
        parent_category = ParentCategory.objects.get(pk=pk)
    except ParentCategory.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Parent category not found"
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = NewParentCategorySerializer(parent_category)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    elif request.method == 'PUT':
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Permission denied. Only admin users can update parent categories."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = NewParentCategorySerializer(parent_category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Parent category updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Permission denied. Only admin users can delete parent categories."
            }, status=status.HTTP_403_FORBIDDEN)

        parent_category.delete()
        return Response({
            "status": "success",
            "message": "Parent category deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)


# Category CRUD Operations

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category_list_create(request):
    """
    List all categories or create a new category
    """
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = NewCategorySerializer(categories, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    elif request.method == 'POST':
        # Only admin users can create categories
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Permission denied. Only admin users can create categories."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = NewCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Category created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_detail(request, pk):
    """
    Retrieve, update or delete a category instance
    """
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Category not found"
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = NewCategorySerializer(category)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    elif request.method == 'PUT':
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Permission denied. Only admin users can update categories."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = NewCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Category updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Permission denied. Only admin users can delete categories."
            }, status=status.HTTP_403_FORBIDDEN)

        category.delete()
        return Response({
            "status": "success",
            "message": "Category deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)