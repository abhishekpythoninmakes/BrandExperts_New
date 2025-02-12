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


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # Requires authentication
def create_custom_product(request):
    try:
        user = request.user  # Get logged-in user
        customer = Customer.objects.get(user=user)  # Get customer profile

        # Extract data from request
        product_id = request.data.get("product")  # Get product ID from request
        quantity = request.data.get("quantity", 1)
        custom_width = request.data.get("custom_width")
        custom_height = request.data.get("custom_height")
        size_unit = request.data.get("size_unit", "inches")
        design_image = request.data.get("design_image")  # URL instead of file
        price = request.data.get("price")

        # Check if product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Invalid product ID"}, status=status.HTTP_404_NOT_FOUND)

        # Create CustomProduct instance
        custom_product = CustomProduct.objects.create(
            customer=customer,
            product=product,
            custom_width=custom_width,
            custom_height=custom_height,
            size_unit=size_unit,
            design_image=design_image,  # Store the URL
            quantity=quantity,
            price=price
        )

        # Serialize and return response
        serializer = CustomProductSerializer(custom_product, context={"request": request})
        return Response(
            {"message": "Custom product created successfully", "custom_product": serializer.data},
            status=status.HTTP_201_CREATED
        )

    except Customer.DoesNotExist:
        return Response({"error": "Customer profile not found"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Adding Custom Product To Cart

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_custom_product_to_cart(request):
    try:
        user = request.user
        customer = Customer.objects.get(user=user)

        # Get custom product ID from request
        custom_product_id = request.data.get("custom_product_id")

        # Validate if the custom product exists
        try:
            custom_product = CustomProduct.objects.get(id=custom_product_id, customer=customer)
        except CustomProduct.DoesNotExist:
            return Response({"error": "Invalid Custom Product ID or not owned by user"}, status=status.HTTP_404_NOT_FOUND)

        # Get or create cart for the customer
        cart, created = Cart.objects.get_or_create(customer=customer, status="active")

        # Check if product already in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            custom_product=custom_product,
            defaults={"quantity": custom_product.quantity, "price": custom_product.price}
        )

        # If item already exists, update quantity and price
        if not item_created:
            cart_item.quantity += custom_product.quantity
            cart_item.price = custom_product.price  # Ensure price is updated
            cart_item.save()

        # Serialize response
        serializer = CartItemSerializer(cart_item, context={"request": request})

        return Response(
            {
                "message": f"Custom Product '{custom_product.product.name}' added to cart successfully",
                "cart_item": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    except Customer.DoesNotExist:
        return Response({"error": "Customer profile not found"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CART VIEW API

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart_details(request):
    try:
        user = request.user
        customer = Customer.objects.get(user=user)

        # Fetch the active cart of the logged-in customer
        cart = Cart.objects.filter(customer=customer, status="active").first()

        if not cart:
            return Response({"message": "Your cart is empty."}, status=status.HTTP_200_OK)

        # Fetch cart items
        cart_items = cart.items.all()
        serializer = CartItemSerializer(cart_items, many=True, context={"request": request})

        # Calculate total price and total products
        total_price = sum(item.total_price for item in cart_items)
        total_products = cart_items.count()

        return Response(
            {
                "cart_id": cart.id,
                "customer_name": customer.user.first_name,
                "total_products": total_products,
                "total_price": str(total_price),
                "cart_items": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    except Customer.DoesNotExist:
        return Response({"error": "Customer profile not found"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Return success response
            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": "Invalid token or token already blacklisted"},
                status=status.HTTP_400_BAD_REQUEST
            )




# Product Ordering API

class CreateOrderView(APIView):
    def post(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        address_id = request.data.get('address_id')
        cart_item_id = request.data.get('cart_item_id')
        cart_id = request.data.get('cart_id')

        # Validate required fields
        if not customer_id or not address_id:
            return Response({"error": "Customer ID and Address ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch customer and address
        customer = get_object_or_404(Customer, id=customer_id)
        address = get_object_or_404(Customer_Address, id=address_id)

        cart_items = []
        if cart_item_id:
            # Handle single cart item
            cart_item = get_object_or_404(CartItem, id=cart_item_id)
            if cart_item.status != 'pending':
                return Response({"error": "Cart item status is not pending."}, status=status.HTTP_400_BAD_REQUEST)
            cart_items.append(cart_item)
        elif cart_id:
            # Handle all cart items in a cart
            cart = get_object_or_404(Cart, id=cart_id)
            for item in cart.items.all():
                if item.status != 'pending':
                    return Response({"error": f"Cart item {item.id} status is not pending."}, status=status.HTTP_400_BAD_REQUEST)
                cart_items.append(item)
        else:
            return Response({"error": "Either cart_item_id or cart_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the order
        order = Order.objects.create(
            customer=customer,
            address=address,
            amount=sum(item.total_price for item in cart_items)
        )
        order.cart_items.set(cart_items)

        # Update the status of cart items to 'ordered'
        for item in cart_items:
            item.status = 'ordered'
            item.save()

        return Response({"message": "Order created successfully.", "order_id": order.id}, status=status.HTTP_201_CREATED)


# Order Detail View
class OrderDetailView(APIView):
    def get(self, request, order_id, *args, **kwargs):
        # Fetch the order
        order = get_object_or_404(Order, id=order_id)

        # Fetch all cart items associated with the order
        cart_items = order.cart_items.all()
        cart_items_data = []
        for item in cart_items:
            product = item.product if item.product else item.custom_product.product
            cart_items_data.append({
                "id": item.id,
                "product_name": product.name,
                "image_url": product.image1,  # Assuming image1 is the main image URL
                "price": item.price,
                "quantity": item.quantity,
                "total_price": item.total_price,
                "status": item.status,
            })

        # Prepare the response
        response_data = {
            "order_id": order.id,
            "customer": order.customer.user.username,
            "address": {
                "building_name": order.address.building_name,
                "street_address": order.address.street_address,
                "city": order.address.city,
                "district": order.address.district,
            },
            "status": order.status,
            "status_options": [choice[0] for choice in ORDER_STATUS_CHOICES],  # List of status options
            "payment_method": order.payment_method,
            "payment_options": [choice[0] for choice in PAYMENT_METHOD_CHOICES],  # List of payment options
            "amount": order.amount,
            "ordered_date": order.ordered_date,
            "delivered_date": order.delivered_date,
            "cart_items": cart_items_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)



# Order Update view


class OrderUpdateView(APIView):
    def patch(self, request, order_id, *args, **kwargs):
        # Fetch the order
        order = get_object_or_404(Order, id=order_id)

        # Allowed fields to update
        allowed_fields = ['status', 'delivered_date', 'payment_method']
        update_data = {key: request.data.get(key) for key in allowed_fields if key in request.data}

        # Validate status and payment method
        if 'status' in update_data and update_data['status'] not in [choice[0] for choice in ORDER_STATUS_CHOICES]:
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        if 'payment_method' in update_data and update_data['payment_method'] not in [choice[0] for choice in PAYMENT_METHOD_CHOICES]:
            return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the order
        for key, value in update_data.items():
            setattr(order, key, value)
        order.save()

        # Update the status of associated cart items if the order status is updated
        if 'status' in update_data:
            cart_items = order.cart_items.all()
            for cart_item in cart_items:
                cart_item.status = update_data['status']
                cart_item.save()

        return Response({"message": "Order updated successfully.", "order_id": order.id}, status=status.HTTP_200_OK)


# Custom Product Detail View

class CartItemDetailView(APIView):
    def get(self, request, cartitem_id, *args, **kwargs):
        # Fetch the cart item
        cart_item = get_object_or_404(CartItem, id=cartitem_id)

        # Fetch custom product details if it exists
        custom_product_data = None
        if cart_item.custom_product:
            custom_product = cart_item.custom_product
            custom_product_data = {
                "product": custom_product.product.name,
                "custom_width": custom_product.custom_width,
                "custom_height": custom_product.custom_height,
                "size_unit": custom_product.size_unit,
                "design_image": custom_product.design_image,
                "quantity": custom_product.quantity,
                "price": custom_product.price,
            }

        # Prepare the response
        response_data = {
            "id": cart_item.id,
            "cart_id": cart_item.cart.id,
            "product": cart_item.product.name if cart_item.product else None,
            "custom_product": custom_product_data,
            "quantity": cart_item.quantity,
            "price": cart_item.price,
            "total_price": cart_item.total_price,
            "status": cart_item.status,
            "created_at": cart_item.created_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


# CART ITEM EDIT VIEW
class CartItemEditView(APIView):
    def patch(self, request, cartitem_id, *args, **kwargs):
        # Fetch the cart item
        cart_item = get_object_or_404(CartItem, id=cartitem_id)

        # Update cart item fields
        if 'quantity' in request.data:
            cart_item.quantity = request.data['quantity']
            cart_item.save()  # Save to update total_price

        # Update custom product fields if it exists
        if cart_item.custom_product and 'custom_product' in request.data:
            custom_product_data = request.data['custom_product']
            custom_product = cart_item.custom_product

            if 'custom_width' in custom_product_data:
                custom_product.custom_width = custom_product_data['custom_width']
            if 'custom_height' in custom_product_data:
                custom_product.custom_height = custom_product_data['custom_height']
            if 'size_unit' in custom_product_data:
                custom_product.size_unit = custom_product_data['size_unit']
            if 'design_image' in custom_product_data:
                custom_product.design_image = custom_product_data['design_image']
            if 'quantity' in custom_product_data:
                custom_product.quantity = custom_product_data['quantity']
            if 'price' in custom_product_data:
                custom_product.price = custom_product_data['price']

            custom_product.save()

        return Response({"message": "Cart item updated successfully.", "cartitem_id": cart_item.id}, status=status.HTTP_200_OK)



# CARTITEM DELETE

class CartItemDeleteView(APIView):
    def delete(self, request, cartitem_id, *args, **kwargs):
        # Fetch the cart item
        cart_item = get_object_or_404(CartItem, id=cartitem_id)

        # Delete the cart item
        cart_item.delete()

        return Response({"message": "Cart item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


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



# CUSTOM PRODUCT LIST


def list_custom_products(request):
    if request.method == "GET":
        custom_products = CustomProduct.objects.all()
        data = []

        for product in custom_products:
            data.append({
                "id": product.id,
                "customer": product.customer.user.first_name if product.customer else "Unknown",
                "product": product.product.name if product.product else "Unknown",
                "custom_width": str(product.custom_width),
                "custom_height": str(product.custom_height),
                "size_unit": product.size_unit,
                "design_image": product.design_image,
                "quantity": product.quantity,
                "price": str(product.price),
                "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            })

        return JsonResponse({"custom_products": data}, status=200)

    return JsonResponse({"error": "Invalid request method. Use GET instead."}, status=405)



# CUSTOM PRODUCT EDIT
@csrf_exempt
def edit_custom_product(request, product_id):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)

            # Fetch the product
            custom_product = get_object_or_404(CustomProduct, id=product_id)

            # Allowed fields for update
            editable_fields = ["design_image", "custom_width", "custom_height", "size_unit", "quantity", "price"]

            # Update the fields if provided in request
            for field in editable_fields:
                if field in data:
                    setattr(custom_product, field, data[field])

            # Save changes
            custom_product.save()

            return JsonResponse({
                "message": "Custom product updated successfully.",
                "updated_product": {
                    "id": custom_product.id,
                    "design_image": custom_product.design_image,
                    "custom_width": custom_product.custom_width,
                    "custom_height": custom_product.custom_height,
                    "size_unit": custom_product.size_unit,
                    "quantity": custom_product.quantity,
                    "price": custom_product.price
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data format."}, status=400)

    return JsonResponse({"error": "Invalid request method. Use PATCH instead."}, status=405)


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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Customer_Address

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
