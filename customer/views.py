import json
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
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

from products_app.models import VAT
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




import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import stripe
import random
import string
from django.core.cache import cache
from .models import CustomUser, Customer, Warranty_plan
from .serializers import WarrantyRegistrationSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


from decimal import Decimal  # Import Decimal for precise decimal handling


class WarrantyRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        price_range = data.get("price_range")
        warranty_plan_amount = data.get("warranty_plan_amount")

        # Validate warranty plan amount
        try:
            warranty_plan_amount_float = float(warranty_plan_amount)
            warranty_plan_amount_decimal = Decimal(warranty_plan_amount_float).quantize(Decimal('0.01'))
        except (ValueError, TypeError):
            return Response({"error": "Invalid warranty plan amount."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create user
        email = data.get("email")
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": data.get("full_name", "").split(" ")[0],
                "last_name": " ".join(data.get("full_name", "").split(" ")[1:]),
            }
        )

        if created:
            dummy_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(dummy_password)
            user.save()

            # Store dummy password in cache
            cache_key = f"dummy_password_{user.email}"
            cache.set(cache_key, dummy_password, timeout=3600)

        # Get or create customer
        customer, _ = Customer.objects.get_or_create(user=user,
                                                     defaults={"mobile": data.get("phone"), "status": "lead"})

        # Get warranty plan
        warranty_plan = Warranty_plan.objects.filter(price_range=price_range).first()
        if not warranty_plan:
            return Response({"error": "Invalid price range. No matching warranty plan found."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create warranty registration
        warranty_data = {
            "full_name": data.get("full_name"),
            "email": email,
            "phone": data.get("phone"),
            "invoice_number": data.get("invoice_number"),
            "invoice_date": data.get("invoice_date"),
            "invoice_value": warranty_plan.id,
            "invoice_file": data.get("invoice_file"),
            "warranty_plan_amount": warranty_plan_amount_decimal,
            "customer": customer.id
        }
        serializer = WarrantyRegistrationSerializer(data=warranty_data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        warranty = serializer.save()

        # Create Stripe PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(warranty_plan_amount_float * 100),
                currency='aed',
                metadata={
                    "customer_email": email,
                    "customer_name": data.get("full_name"),
                    "invoice_number": data.get("invoice_number"),
                    "warranty_plan": warranty_plan.price_range
                },
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Proceed to payment",
            "client_secret": intent.client_secret,
            "customer_id": customer.id,
            "warranty_id": warranty.id,
            "metadata": {
                "customer_email": email,
                "customer_name": data.get("full_name"),
                "invoice_number": data.get("invoice_number"),
                "invoice_date": data.get("invoice_date"),
                "invoice_file": data.get("invoice_file"),
                "warranty_plan_amount": warranty_plan_amount_decimal,
                "warranty_plan": warranty_plan.price_range
            }
        }, status=status.HTTP_200_OK)


@csrf_exempt
def confirm_payment_warranty(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_intent_id = data.get('payment_intent_id')
            warranty_id = data.get('warranty_id')  # Retrieve warranty ID

            # Retrieve payment intent
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Retrieve dummy_password from cache using metadata
            customer_email = intent.metadata.get('customer_email')
            customer = Customer.objects.get(user__email=customer_email)
            cache_key = f"dummy_password_{customer.user.email}"
            dummy_password = cache.get(cache_key)
            if not dummy_password:
                dummy_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                customer.user.set_password(dummy_password)
                customer.user.save()

            if intent.status == 'succeeded':
                # Update customer status to "lead"
                customer.status = 'client'
                customer.save()

                # Send email with warranty and login details
                warranty = WarrantyRegistration.objects.get(id=warranty_id)
                subject = "Warranty Registration & Payment Confirmation"
                message = f"""Dear {warranty.full_name},
Your payment was successful! 
🔑 Login Credentials:
Username: {warranty.email}
Password: {dummy_password}
📌 Warranty Details:
- Number: {warranty.warranty_number}
- Invoice Number: {warranty.invoice_number}
- Amount Paid: AED {warranty.warranty_plan_amount}
Thank you for choosing us!"""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [warranty.email],
                    fail_silently=False
                )

                # Clear dummy_password from cache
                cache.delete(cache_key)

                return JsonResponse({
                    "status": "success",
                    "warranty_number": warranty.warranty_number,
                    "customer_status": "lead"
                })

            else:
                # Payment failed - delete warranty registration
                WarrantyRegistration.objects.filter(id=warranty_id).delete()

                # Send only login credentials
                subject = "Your Login Credentials"
                message = f"""Dear {customer.user.first_name},
Your payment failed. Here are your login credentials:
🔑 Login Credentials:
Username: {customer.user.email}
Password: {dummy_password}
Please try again later."""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [customer.user.email],
                    fail_silently=False
                )

                # Clear dummy_password from cache
                cache.delete(cache_key)

                return JsonResponse({
                    "status": "payment_failed",
                    "message": "Payment failed. Login credentials sent."
                }, status=400)

        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)
        except WarrantyRegistration.DoesNotExist:
            return JsonResponse({"error": "Warranty registration not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)



# class WarrantyRegistrationAPIView(APIView):
#     permission_classes = [AllowAny]  # Allows anyone to access this API
#
#     def post(self, request):
#         data = request.data.copy()
#         price_range = data.get("price_range")  # Get price range string from request
#
#         # Fetch the matching Warranty_plan object
#         warranty_plan = Warranty_plan.objects.filter(price_range=price_range).first()
#
#         if not warranty_plan:
#             return Response(
#                 {"error": "Invalid price range. No matching warranty plan found."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         data["invoice_value"] = warranty_plan.id  # Assign the Warranty_plan ID
#
#         serializer = WarrantyRegistrationSerializer(data=data)
#         if serializer.is_valid():
#             warranty = serializer.save()
#
#             # Send email with warranty number
#             subject = "Warranty Registration Successful"
#             message = (
#                 f"Dear {warranty.full_name},\n\n"
#                 f"Your warranty registration was successful!\n\n"
#                 f"📌 **Warranty Details:**\n"
#                 f"- **Warranty Number:** {warranty.warranty_number}\n"
#                 f"- **Product Name:** {warranty.product_name}\n"
#                 f"- **Warranty Plan:** {warranty_plan.price_range}\n"
#                 f"- **Amount Paid:** ${warranty.warranty_plan_amount}\n\n"
#                 "🛠️ Please keep this number safe for future reference.\n\n"
#                 "Best regards,\n"
#                 "BrandExperts.ae"
#             )
#
#             send_mail(
#                 subject,
#                 message,
#                 f"BrandExperts <{settings.DEFAULT_FROM_EMAIL}>",
#                 [warranty.email],
#                 fail_silently=False,
#             )
#
#             return Response(
#                 {
#                     "message": "Warranty registered successfully!",
#                     "warranty_number": warranty.warranty_number,
#                     "data": serializer.data
#                 },
#                 status=status.HTTP_201_CREATED
#             )
#
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# VALIDATE WARRANTY NUMBER
@api_view(['GET'])
def validate_warranty_number(request):
    warranty_number = request.GET.get('warranty_number')

    if not warranty_number:
        return Response({"is_valid": False, "message": "Warranty number is required"}, status=400)

    try:
        warranty = WarrantyRegistration.objects.get(warranty_number=warranty_number)
        return Response({"is_valid": True, "message": "Warranty number is valid and active"})
    except WarrantyRegistration.DoesNotExist:
        return Response({"is_valid": False, "message": "Invalid or inactive warranty number"}, status=404)



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
                        "invoice_number": warranty.invoice_number,
                        "invoice_date": warranty.invoice_date.strftime("%Y-%m-%d"),
                        "invoice_value": warranty.invoice_value.price_range,
                        "invoice_file": warranty.invoice_file if warranty.invoice_file else None,
                        "warranty_plan": warranty.invoice_value.price_range if warranty.invoice_value else "No Warranty Plan",
                        "warranty_number": warranty.warranty_number,
                        "warranty_amount":warranty.warranty_plan_amount,
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
                    "invoice_number": warranty.invoice_number,
                    "invoice_date": warranty.invoice_date.strftime("%Y-%m-%d"),
                    "invoice_value": str(warranty.invoice_value),
                    "invoice_file": warranty.invoice_file if warranty.invoice_file else None,
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
            company_name = data.get("company_name", "").strip()
            ext = data.get("ext", "").strip()
            address_line1 = data.get("address_line1", "").strip()
            address_line2 = data.get("address_line2", "").strip()
            country = data.get("country", "").strip()
            city = data.get("city", "").strip()
            state = data.get("state", "").strip()
            zip_code = data.get("zip_code", "").strip()

            # Validate customer ID
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                return JsonResponse({"error": "Invalid customer ID. Customer not found."}, status=404)

            # Validate country choice
            # valid_countries = dict(countrys)  # Use the globally defined tuple
            # if country and country not in valid_countries:
            #     return JsonResponse({"error": "Invalid country selected."}, status=400)

            # Check if the exact same address already exists for the customer
            existing_address = Customer_Address.objects.filter(
                customer=customer,
                company_name=company_name,
                ext=ext,
                address_line1=address_line1,
                address_line2=address_line2,
                country=country,
                city=city,
                state=state,
                zip_code=zip_code
            ).first()

            if existing_address:
                return JsonResponse({"error": "This address already exists."}, status=400)

            # Create and save the new address
            customer_address = Customer_Address.objects.create(
                customer=customer,
                company_name=company_name,
                ext=ext,
                address_line1=address_line1,
                address_line2=address_line2,
                country=country,
                city=city,
                state=state,
                zip_code=zip_code
            )

            # Prepare response data
            response_data = {
                "message": "Customer address successfully created.",
                "address_details": {
                    "id": customer_address.id,
                    "customer": customer.user.first_name if customer.user else "Unknown",
                    "company_name": customer_address.company_name,
                    "ext": customer_address.ext,
                    "address_line1": customer_address.address_line1,
                    "address_line2": customer_address.address_line2,
                    "country": customer_address.country,
                    "city": customer_address.city,
                    "state": customer_address.state,
                    "zip_code": customer_address.zip_code,
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
                "company_name": address.company_name,
                "ext": address.ext,
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "country": address.country,
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
            }
            for address in addresses
        ]

        return JsonResponse(
            {
                "customer": customer.user.first_name if customer.user else "Unknown",
                "addresses": address_list,
            },
            status=200,
        )

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

            # Validate country choice
            valid_countries = dict(countrys)
            country = data.get("country", address.country)
            # if country and country not in valid_countries:
            #     return JsonResponse({"error": "Invalid country selected."}, status=400)

            # Check for duplicate addresses
            existing_address = Customer_Address.objects.filter(
                customer=address.customer,
                company_name=data.get("company_name", address.company_name),
                ext=data.get("ext", address.ext),
                address_line1=data.get("address_line1", address.address_line1),
                address_line2=data.get("address_line2", address.address_line2),
                country=country,
                city=data.get("city", address.city),
                state=data.get("state", address.state),
                zip_code=data.get("zip_code", address.zip_code)
            ).exclude(id=address_id).first()

            if existing_address:
                return JsonResponse({"error": "A similar address already exists."}, status=400)

            # Update the address fields if provided in the request
            address.company_name = data.get("company_name", address.company_name)
            address.ext = data.get("ext", address.ext)
            address.address_line1 = data.get("address_line1", address.address_line1)
            address.address_line2 = data.get("address_line2", address.address_line2)
            address.country = country
            address.city = data.get("city", address.city)
            address.state = data.get("state", address.state)
            address.zip_code = data.get("zip_code", address.zip_code)

            # Save the updated address
            address.save()

            # Prepare response data
            response_data = {
                "message": "Customer address updated successfully.",
                "updated_address": {
                    "id": address.id,
                    "company_name": address.company_name,
                    "ext": address.ext,
                    "address_line1": address.address_line1,
                    "address_line2": address.address_line2,
                    "country": address.country,
                    "city": address.city,
                    "state": address.state,
                    "zip_code": address.zip_code,
                }
            }

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method. Use PUT instead."}, status=405)


# Create Cart
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem, Customer, Product
from .serializers import CartItemSerializer
from rest_framework.decorators import api_view
from .models import Cart, CartItem, Customer, Product, Designer_rate

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
        product_id = item_data.get('productid')
        product_name = item_data.get('name')
        custom_width = item_data.get('size', {}).get('width')
        custom_height = item_data.get('size', {}).get('height')
        design_image = item_data.get('design_image')
        quantity = item_data.get('quantity', 1)
        price = float(item_data.get('price', 0))
        total_price_item = float(item_data.get('total', 0))
        size_unit = item_data.get('unit', 'inches')  # Default to 'inches' if not provided
        hire_designer_id = item_data.get('hire_designer_id', None)  # Get hire_designer_id from request
        design_description = item_data.get('design_description', '')  # Get design_description from request

        if not product_id:
            return Response({"error": "Product ID is required for each cart item"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": f"Product with ID {product_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the Designer_rate instance if hire_designer_id is provided
        hire_designer = None
        if hire_designer_id:
            try:
                hire_designer = Designer_rate.objects.get(id=hire_designer_id)
            except Designer_rate.DoesNotExist:
                return Response({"error": f"Designer_rate with ID {hire_designer_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create or update the cart item
        cart_item, item_created = CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            defaults={
                'custom_width': custom_width,
                'custom_height': custom_height,
                'design_image': design_image,
                'quantity': quantity,
                'price': price,
                'total_price': total_price_item,
                'size_unit': size_unit,
                'status': 'pending',  # Default status
                'hire_designer': hire_designer,  # Set hire_designer (can be None)
                'design_description': design_description  # Set design_description
            }
        )

        total_price += total_price_item
        total_items += quantity
        cart_items_list.append({
            "productid": product.id,
            "name": product.name,
            "quantity": quantity,
            "price": price,
            "total": total_price_item,
            "size": {
                "width": custom_width,
                "height": custom_height
            },
            "design_image": design_image,
            "unit": size_unit,
            "hire_designer_id": hire_designer.id if hire_designer else None,  # Include hire_designer_id in response
            "design_description": design_description  # Include design_description in response
        })

    # Prepare response
    response_data = {
        "message": "Cart updated successfully" if not created else "Cart created successfully",
        "cart": {
            "cart_id": cart.id,
            "customer_id": customer.id,
            "cart_items": cart_items_list,
            "total_items": total_items,
            "total_price": total_price
        }
    }

    return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

# CartItem Update

class UpdateCartItemView(APIView):
    def patch(self, request, cart_item_id):
        cart_item = get_object_or_404(CartItem, id=cart_item_id)  # Get the CartItem or return 404
        serializer = CartItemUpdateSerializer(cart_item, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "CartItem updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#  CART ITEM DELETE

class DeleteCartItemView(APIView):
    def delete(self, request, cart_item_id):
        cart_item = get_object_or_404(CartItem, id=cart_item_id)  # Fetch CartItem or return 404
        cart_item.delete()
        return Response({"message": "CartItem deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



# Order Creation
@api_view(["POST"])
def create_order(request):
    cart_id = request.data.get("cart_id")
    customer_address_id = request.data.get("customer_address_id")
    payment_status = request.data.get("payment_status")
    payment_method = request.data.get("payment_method")

    # Validate cart
    try:
        cart = Cart.objects.get(id=cart_id, status="active")
    except Cart.DoesNotExist:
        return Response({"error": "Invalid or inactive cart."}, status=status.HTTP_400_BAD_REQUEST)

    # Validate customer address
    try:
        customer_address = Customer_Address.objects.get(id=customer_address_id)
    except Customer_Address.DoesNotExist:
        return Response({"error": "Invalid customer address."}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate total order amount
    cart_items = cart.items.filter(status="pending")
    if not cart_items.exists():
        return Response({"error": "Cart is empty or already processed."}, status=status.HTTP_400_BAD_REQUEST)

    total_amount = sum(item.total_price for item in cart_items)

    # Create Order
    order = Order.objects.create(
        customer=cart.customer,
        address=customer_address,
        cart=cart,
        payment_method=payment_method,
        payment_status=payment_status,
        amount=total_amount,
    )

    # Update CartItem statuses to "ordered"
    cart_items.update(status="ordered")

    # Update Cart status to "checked_out"
    cart.status = "checked_out"
    cart.save()

    return Response({"message": "Order created successfully.", "order_id": order.id}, status=status.HTTP_201_CREATED)



# Payment

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import stripe
from django.shortcuts import get_object_or_404


stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_payment_intent(request):
    if request.method == 'POST':
        try:
            # Get cart ID from the request
            data = json.loads(request.body)
            cart_id = data.get('cart_id')

            # Fetch the cart and its items
            cart = Cart.objects.get(id=cart_id)
            cart_items = cart.items.filter(status='pending')

            # Calculate the base total price (without tax adjustments)
            total_price = sum(item.total_price for item in cart_items)

            # Fetch VAT settings from the database (default to 5% exclusive tax)
            vat = VAT.objects.first()
            vat_percentage = Decimal(vat.percentage) if vat else Decimal('5.00')
            is_vat_inclusive = vat.is_inclusive if vat else False  # Check if VAT is inclusive

            if is_vat_inclusive:
                base_price = total_price / (Decimal('1') + vat_percentage / Decimal('100'))
                vat_amount = total_price - base_price
                total_with_vat = total_price  # No additional tax applied
            else:
                base_price = total_price
                vat_amount = (total_price * vat_percentage) / Decimal('100')
                total_with_vat = total_price + vat_amount

            # Get customer details
            customer = cart.customer
            customer_name = customer.user.first_name + " " + customer.user.last_name
            customer_email = customer.user.email

            # Fetch customer's latest billing address
            customer_address = Customer_Address.objects.filter(customer=customer).latest('id')

            # Create a PaymentIntent with Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(total_with_vat * 100),  # Convert to cents
                currency='aed',
                metadata={
                    'cart_id': cart_id,
                    'customer_name': customer_name,
                    'customer_email': customer_email,
                },
            )

            # Return response with billing details
            return JsonResponse({
                'clientSecret': intent.client_secret,
                'transaction_id': intent.id,  # Stripe PaymentIntent ID
                'username': customer_name,
                'email': customer_email,
                'billing_address': {
                    'state': customer_address.state,
                    'country': customer_address.country,
                    'zip_code': customer_address.zip_code,
                    'line1': customer_address.address_line1,  # Use address_line1
                    'city': customer_address.city
                },
                'base_product_amount': float(base_price),
                'vat_percentage': float(vat_percentage),
                'vat_amount': float(vat_amount),
                'total_with_vat': float(total_with_vat),
                'is_vat_inclusive': is_vat_inclusive
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'GET method not allowed'}, status=405)


from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order, Cart, Customer_Address

@csrf_exempt
def confirm_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_intent_id = data.get('payment_intent_id')
            cart_id = data.get('cart_id')

            # Retrieve the PaymentIntent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if intent.status == 'succeeded':
                # Fetch the cart and its items
                cart = Cart.objects.get(id=cart_id)
                customer = cart.customer
                cart_items = cart.items.filter(status='pending')

                # Calculate total price
                total_price = sum(item.total_price for item in cart_items)

                # Get the latest customer address
                customer_address = Customer_Address.objects.filter(customer=customer).latest('id')

                # Create an order with the transaction ID
                order = Order.objects.create(
                    customer=customer,
                    address=customer_address,
                    cart=cart,
                    payment_method='card',
                    payment_status='paid',
                    amount=total_price,
                    transaction_id=payment_intent_id  # Save the Stripe PaymentIntent ID
                )

                # Update cart and cart item statuses
                cart.status = 'checked_out'
                cart.save()

                for item in cart_items:
                    item.status = 'ordered'
                    item.save()

                # Send email to the customer with billing details
                subject = 'Order Confirmation'
                html_message = render_to_string('order_confirmation.html', {
                    'order': order,
                    'cart_items': cart_items,
                    'total_price': total_price,
                    'customer_name': customer.user.first_name,
                    'customer_email': customer.user.email,
                    'billing_address': f"{customer_address.address_line1}, {customer_address.city}, {customer_address.zip_code}",
                    'transaction_id': payment_intent_id
                })
                plain_message = strip_tags(html_message)
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [customer.user.email],
                    html_message=html_message,
                )

                return JsonResponse({
                    'success': True,
                    'message': 'Payment successful!',
                    'order_id': order.id,
                    'transaction_id': payment_intent_id
                })

            else:
                return JsonResponse({'success': False, 'message': 'Payment failed.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



# Test


import random


@api_view(["POST"])
def process_text(request):
    text = request.data.get("text", "").lower()  # Get the text and convert to lowercase
    contains_camera = "camera" in text  # Check if "camera" exists in the text

    # Random welcome responses
    random_responses = [
        "Hello! How can I assist you today?",
        "Welcome! What would you like to do?",
        "Glad to have you here! Need any help?",
        "Hey there! Tell me what you need assistance with.",
        "Hi! Ready to get started?"
    ]

    if contains_camera:
        response_text = "Opening the camera. Place the phone camera above the book page, and it will be scanned after a 3-second timer."
    else:
        response_text = random.choice(random_responses)

    return Response({
        "response": response_text,
        "camera": contains_camera
    })
