import json

from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from rest_framework.permissions import IsAuthenticated
from datetime import date
from django.contrib.auth import authenticate, logout


# Create your views here.

# Customer Registration

def home(request):
    return render(request,'home.html')


class CustomerRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = CustomerRegistrationSerializer(data=request.data)

        try:
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "success": True,
                        "message": "User registered successfully.",
                        "status_code": status.HTTP_201_CREATED
                    }, status=status.HTTP_201_CREATED)

                except IntegrityError as e:
                    return Response({
                        "success": False,
                        "message": "A user with this email or mobile already exists.",
                        "error_details": str(e),
                        "status_code": status.HTTP_409_CONFLICT
                    }, status=status.HTTP_409_CONFLICT)

        except serializers.ValidationError as e:
            return Response({
                "success": False,
                "message": "Registration failed",
                "errors": serializer.errors,
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "success": False,
                "message": "An unexpected error occurred",
                "error_details": str(e),
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CUSTOMER LOGIN

class LoginAPIView(APIView):
    permission_classes = [AllowAny]  # Make sure login doesn't require authentication

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({"error": "Invalid credentials"},
                            status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        try:
            customer = Customer.objects.get(user=user)
            customer_id = customer.id
            mobile = customer.mobile
        except Customer.DoesNotExist:
            customer_id = None
            mobile = None

        return Response({
            "user_id": user.id,
            "customer_id": customer_id,
            "access_token": access_token,
            "refresh_token": str(refresh),
            "user_details": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name" : user.last_name,
                "email": user.email,
                "mobile": mobile,
            }
        }, status=status.HTTP_200_OK)



# Warranty Registration

class WarrantyRegistrationAPIView(APIView):
    permission_classes = [AllowAny]  # Allows anyone to access this API

    def post(self, request):
        serializer = WarrantyRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            warranty = serializer.save()

            # Send email with warranty number
            subject = "Warranty Registration Successful"
            message = (
                f"Dear {warranty.full_name},\n\n"
                f"Your warranty registration was successful.\n"
                f"Warranty Number: {warranty.warranty_number}\n"
                f"Product: {warranty.product_name}\n"
                f"Warranty Plan: {warranty.get_warranty_plan_display()}\n\n"
                "Please keep this number safe for future reference.\n\n"
                "Best regards,\n"
                "BrandExperts.ae"
            )
            send_mail(
                subject,
                message,
                "hiddenhope00@gmail.com",  # Your email (from settings)
                [warranty.email],
                fail_silently=False,
            )

            return Response(
                {
                    "message": "Warranty registered successfully!",
                    "warranty_number": warranty.warranty_number,
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# CREATE CLAIM WARRANTY

@csrf_exempt
def create_claim_warranty(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            warranty_number = data.get("warranty_number")
            description = data.get("description")

            # Validate input
            if not warranty_number:
                return JsonResponse({"error": "Warranty registration number is required."}, status=400)

            if not description:
                return JsonResponse({"error": "Claim description is required."}, status=400)

            # Check if warranty number exists
            try:
                warranty = WarrantyRegistration.objects.get(warranty_number=warranty_number)
            except WarrantyRegistration.DoesNotExist:
                return JsonResponse({"error": "Invalid warranty number. No registration found."}, status=404)

            # Check if a claim already exists for the same warranty number
            existing_claim = ClaimWarranty.objects.filter(warranty_number=warranty_number).first()
            if existing_claim:
                return JsonResponse({
                    "message": "A claim for this warranty number already exists.",
                    "claim_details": {
                        "warranty_number": existing_claim.warranty_number,
                        "description": existing_claim.description,
                        "status": existing_claim.status,
                        "claimed_at": existing_claim.claimed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    "warranty_details": {
                        "full_name": warranty.full_name,
                        "email": warranty.email,
                        "phone": warranty.phone,
                        "product_name": warranty.product_name,
                        "invoice_date": warranty.invoice_date.strftime("%Y-%m-%d"),
                        "invoice_value": str(warranty.invoice_value),
                        "invoice_file": warranty.invoice_file.url if warranty.invoice_file else None,
                        "warranty_plan": warranty.get_warranty_plan_display(),
                        "warranty_number": warranty.warranty_number,
                        "created_at": warranty.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                }, status=200)

            # Create a new claim warranty entry
            claim = ClaimWarranty.objects.create(
                warranty_number=warranty_number,
                description=description
            )

            # Prepare response data
            response_data = {
                "message": "Claim warranty successfully created.",
                "claim_details": {
                    "warranty_number": claim.warranty_number,
                    "description": claim.description,
                    "status": claim.status,
                    "claimed_at": claim.claimed_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "warranty_details": {
                    "full_name": warranty.full_name,
                    "email": warranty.email,
                    "phone": warranty.phone,
                    "product_name": warranty.product_name,
                    "invoice_date": warranty.invoice_date.strftime("%Y-%m-%d"),
                    "invoice_value": str(warranty.invoice_value),
                    "invoice_file": warranty.invoice_file.url if warranty.invoice_file else None,
                    "warranty_plan": warranty.get_warranty_plan_display(),
                    "warranty_number": warranty.warranty_number,
                    "created_at": warranty.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }

            return JsonResponse(response_data, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data format."}, status=400)

    return JsonResponse({"error": "Invalid request method. Use POST instead."}, status=405)


# ADDING CUSTOMER ADDRESS

@csrf_exempt
def create_customer_address(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract customer ID and other fields
            customer_id = data.get("customer_id")
            building_name = data.get("building_name", "").strip()
            street_address = data.get("street_address", "").strip()
            landmark = data.get("landmark", "").strip()
            city = data.get("city", "").strip()
            district = data.get("district", "").strip()
            delivery_instructions = data.get("delivery_instructions", "").strip()

            # Validate customer ID
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                return JsonResponse({"error": "Invalid customer ID. Customer not found."}, status=404)

            # Check if the exact same address already exists for the customer
            existing_address = Customer_Address.objects.filter(
                customer=customer,
                building_name=building_name,
                street_address=street_address,
                landmark=landmark,
                city=city,
                district=district,
                delivery_instructions=delivery_instructions
            ).first()

            if existing_address:
                return JsonResponse({"error": "This address already exists."}, status=400)

            # Create and save the new address
            customer_address = Customer_Address.objects.create(
                customer=customer,
                building_name=building_name,
                street_address=street_address,
                landmark=landmark,
                city=city,
                district=district,
                delivery_instructions=delivery_instructions
            )

            # Prepare response data
            response_data = {
                "message": "Customer address successfully created.",
                "address_details": {
                    "id": customer_address.id,
                    "customer": customer.user.first_name if customer.user else "Unknown",
                    "building_name": customer_address.building_name,
                    "street_address": customer_address.street_address,
                    "landmark": customer_address.landmark,
                    "city": customer_address.city,
                    "district": customer_address.district,
                    "delivery_instructions": customer_address.delivery_instructions,
                }
            }

            return JsonResponse(response_data, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data format."}, status=400)

    return JsonResponse({"error": "Invalid request method. Use POST instead."}, status=405)


# LIST CUSTOMER ADDRESS

@csrf_exempt
def get_customer_addresses(request, customer_id):
    if request.method == "GET":
        try:
            # Validate customer ID
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Invalid customer ID. Customer not found."}, status=404)

        # Fetch all addresses for the given customer
        addresses = Customer_Address.objects.filter(customer=customer)

        if not addresses.exists():
            return JsonResponse({"message": "No addresses found for this customer."}, status=200)

        # Prepare response data
        address_list = [
            {
                "id": address.id,
                "building_name": address.building_name,
                "street_address": address.street_address,
                "landmark": address.landmark,
                "city": address.city,
                "district": address.district,
                "delivery_instructions": address.delivery_instructions,
            }
            for address in addresses
        ]

        return JsonResponse({"customer": customer.user.first_name, "addresses": address_list}, status=200)

    return JsonResponse({"error": "Invalid request method. Use GET instead."}, status=405)


# CUSTOMER ADDRESS EDIT

@csrf_exempt
def edit_customer_address(request, address_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            # Check if the address exists
            try:
                address = Customer_Address.objects.get(id=address_id)
            except Customer_Address.DoesNotExist:
                return JsonResponse({"error": "Customer address not found."}, status=404)

            # Update the address fields if provided in the request
            address.building_name = data.get("building_name", address.building_name)
            address.street_address = data.get("street_address", address.street_address)
            address.landmark = data.get("landmark", address.landmark)
            address.city = data.get("city", address.city)
            address.district = data.get("district", address.district)
            address.delivery_instructions = data.get("delivery_instructions", address.delivery_instructions)

            # Save the updated address
            address.save()

            # Prepare response data
            response_data = {
                "message": "Customer address updated successfully.",
                "updated_address": {
                    "id": address.id,
                    "building_name": address.building_name,
                    "street_address": address.street_address,
                    "landmark": address.landmark,
                    "city": address.city,
                    "district": address.district,
                    "delivery_instructions": address.delivery_instructions,
                }
            }

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method. Use PUT instead."}, status=405)


# Create Cart
@api_view(['POST'])
def create_or_update_cart(request):
    customer_id = request.data.get('customer_id')
    cart_items_data = request.data.get('cart_items', [])

    if not customer_id:
        return Response({"error": "Customer ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get or create the cart
    cart, created = Cart.objects.get_or_create(customer=customer, status='active')

    # Process each cart item in the request
    total_price = 0
    total_items = 0
    cart_items_list = []

    for item_data in cart_items_data:
        product_id = item_data.get('product_id')
        custom_width = item_data.get('custom_width')
        custom_height = item_data.get('custom_height')
        size_unit = item_data.get('size_unit')
        design_image = item_data.get('design_image')
        quantity = item_data.get('quantity', 1)
        price = item_data.get('price')
        total_price_item = item_data.get('total_price')
        status_item = item_data.get('status', 'pending')

        if not product_id:
            return Response({"error": "Product ID is required for each cart item"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": f"Product with ID {product_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create or update the cart item
        cart_item, item_created = CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            defaults={
                'custom_width': custom_width,
                'custom_height': custom_height,
                'size_unit': size_unit,
                'design_image': design_image,
                'quantity': quantity,
                'price': price,
                'total_price': total_price_item,
                'status': status_item
            }
        )

        total_price += total_price_item
        total_items += quantity
        cart_items_list.append(CartItemSerializer(cart_item).data)

    # Prepare response
    response_data = {
        "message": "Cart updated successfully" if not created else "Cart created successfully",
        "cart": {
            "id": cart.id,
            "status": cart.status,
            "created_at": cart.created_at,
            "total_items": total_items,
            "total_price": total_price,
            "cart_items": cart_items_list
        }
    }

    return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
