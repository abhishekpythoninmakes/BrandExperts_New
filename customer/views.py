from django.db import IntegrityError
from django.shortcuts import render
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
from django.contrib.auth import authenticate
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