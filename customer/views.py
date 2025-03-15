import json
import os
import tempfile
import time
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from products_app.models import VAT, site_visit
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
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            # Check if email already exists
            if CustomUser.objects.filter(email=validated_data['email']).exists():
                return Response({
                    "success": False,
                    "message": "A user with this email already exists.",
                    "status_code": status.HTTP_409_CONFLICT
                }, status=status.HTTP_409_CONFLICT)

            # Generate a 4-digit OTP
            otp = ''.join(random.choices('0123456789', k=4))

            # Send OTP via email
            subject = 'Your OTP for Registration'
            message = f'Your OTP code is: {otp}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [validated_data['email']]

            send_mail(subject, message, from_email, recipient_list)

            # Delete existing OTP records for this email
            OTPRecord.objects.filter(email=validated_data['email']).delete()

            # Create new OTP record
            OTPRecord.objects.create(
                email=validated_data['email'],
                otp=otp,
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                mobile=validated_data['mobile'],
                password=validated_data['password']
            )
            print("OTP =",otp)
            return Response({
                "success": True,
                "message": "OTP sent successfully.",
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

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

from django.utils import timezone
# Verify OTP
class OTPVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')

        if not otp:
            return Response({
                "success": False,
                "error": "OTP is required.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_record = OTPRecord.objects.get(otp=otp)
        except OTPRecord.DoesNotExist:
            return Response({
                "success": False,
                "error": "Invalid OTP.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check OTP expiration (10 minutes)
        current_time = timezone.now()
        time_difference = current_time - otp_record.created_at
        if time_difference.total_seconds() > 600:
            otp_record.delete()
            return Response({
                "success": False,
                "error": "OTP has expired.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing user (race condition)
        if CustomUser.objects.filter(username=otp_record.email).exists():
            otp_record.delete()
            return Response({
                "success": False,
                "error": "A user with this email already exists.",
                "status_code": status.HTTP_409_CONFLICT
            }, status=status.HTTP_409_CONFLICT)

        # Check for existing mobile (race condition)
        if Customer.objects.filter(mobile=otp_record.mobile).exists():
            otp_record.delete()
            return Response({
                "success": False,
                "error": "A user with this mobile number already exists.",
                "status_code": status.HTTP_409_CONFLICT
            }, status=status.HTTP_409_CONFLICT)

        try:
            # Create user
            user = CustomUser.objects.create(
                username=otp_record.email,
                email=otp_record.email,
                first_name=otp_record.first_name,
                last_name=otp_record.last_name
            )
            user.set_password(otp_record.password)
            user.save()

            # Create customer
            customer = Customer.objects.create(
                user=user,
                mobile=otp_record.mobile
            )
        except IntegrityError as e:
            otp_record.delete()
            return Response({
                "success": False,
                "error": "User creation failed due to a conflict.",
                "error_details": str(e),
                "status_code": status.HTTP_409_CONFLICT
            }, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            otp_record.delete()
            return Response({
                "success": False,
                "error": "An error occurred during user creation.",
                "error_details": str(e),
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Delete OTP record
        otp_record.delete()

        return Response({
            "success": True,
            "message": "User registered and logged in successfully.",
            "user_id": user.id,
            "customer_id": customer.id,
            "access_token": access_token,
            "refresh_token": str(refresh),
            "user_details": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "mobile": customer.mobile,
            },
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)






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
                - Amount Paid: AED {warranty.warranty_plan_amount},
                🔔 Your warranty will be active after a 30-day cooling-off period.
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

from datetime import datetime, timedelta
# VALIDATE WARRANTY NUMBER
@api_view(['POST'])
@csrf_exempt
def validate_warranty_number(request):
    try:
        data = json.loads(request.body)
        warranty_number = data.get('warranty_number', '').strip()

        if not warranty_number:
            return Response({"is_valid": False, "message": "Warranty number is required"}, status=400)

        try:
            warranty = WarrantyRegistration.objects.get(warranty_number=warranty_number)
        except WarrantyRegistration.DoesNotExist:
            return Response({"is_valid": False, "message": "Invalid or inactive warranty number"}, status=404)

        # Check 30-day cooling period
        cooling_period_end = warranty.created_at + timedelta(days=30)
        if timezone.now() < cooling_period_end:
            return Response({
                "is_valid": False,
                "message": "Sorry, you need to wait 30 days (cooling period) to claim warranty",
                "cooling_period_end": cooling_period_end.strftime("%Y-%m-%d")
            }, status=200)

        # Check if warranty plan has expired
        warranty_plan = warranty.invoice_value
        if not warranty_plan:
            return Response({"is_valid": False, "message": "No warranty plan associated"}, status=400)

        # Calculate warranty duration
        warranty_duration = None
        if warranty_plan.year1:
            warranty_duration = 1
        elif warranty_plan.year2:
            warranty_duration = 2
        elif warranty_plan.year5:
            warranty_duration = 5

        if not warranty_duration:
            return Response({"is_valid": False, "message": "Invalid warranty duration"}, status=400)

        expiration_date = warranty.created_at + timedelta(days=365 * warranty_duration)
        if timezone.now() > expiration_date:
            return Response({"is_valid": False, "message": "Warranty plan has expired"}, status=400)

        # Build complete warranty details
        warranty_details = {
            "full_name": warranty.full_name,
            "email": warranty.email,
            "phone": warranty.phone,
            "invoice_number": warranty.invoice_number,
            "invoice_date": warranty.invoice_date.strftime("%Y-%m-%d"),
            "invoice_file": warranty.invoice_file.url if warranty.invoice_file else None,
            "warranty_plan_amount": str(warranty.warranty_plan_amount),
            "warranty_number": warranty.warranty_number,
            "created_at": warranty.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "warranty_plan": {
                "price_range": warranty_plan.price_range,
                "duration_years": warranty_duration,
                "plan_amount": str(getattr(warranty_plan, f'year{warranty_duration}', '0.00'))
            },
            "expiration_date": expiration_date.strftime("%Y-%m-%d"),
            "cooling_period_end": cooling_period_end.strftime("%Y-%m-%d")
        }

        return Response({
            "is_valid": True,
            "message": "Warranty number is valid and active",
            "warranty_details": warranty_details
        })

    except json.JSONDecodeError:
        return Response({"is_valid": False, "message": "Invalid JSON format"}, status=400)


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

            # Check if warranty plan has expired
            warranty_plan = warranty.invoice_value
            if not warranty_plan:
                return JsonResponse({"error": "No warranty plan associated with this warranty number"}, status=400)

            # Calculate warranty expiration date
            warranty_duration = None
            if warranty_plan.year1:
                warranty_duration = 1
            elif warranty_plan.year2:
                warranty_duration = 2
            elif warranty_plan.year5:
                warranty_duration = 5

            if not warranty_duration:
                return JsonResponse({"error": "Invalid warranty plan duration"}, status=400)

            expiration_date = warranty.created_at + timedelta(days=365 * warranty_duration)
            if timezone.now() > expiration_date:
                return JsonResponse({"error": "Warranty plan has expired. Cannot create a new claim."}, status=400)

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
                    "invoice_value": warranty.invoice_value.price_range if warranty.invoice_value else "No Warranty Plan",
                    "invoice_file": warranty.invoice_file if warranty.invoice_file else None,
                    "warranty_plan": warranty.invoice_value.price_range if warranty.invoice_value else "No Warranty Plan",
                    "warranty_number": warranty.warranty_number,
                    "warranty_amount": warranty.warranty_plan_amount,
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
    site_visit = request.data.get('site_visit', False)
    print('cart data = ', request.data)
    if not customer_id:
        return Response({"error": "Customer ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get or create the cart
    cart, created = Cart.objects.get_or_create(customer=customer, status='active')

    cart.site_visit = site_visit
    cart.save()

    if not created:
        CartItem.objects.filter(cart=cart, status='pending').delete()

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
            "site_visit": cart.site_visit,
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
            print("PAYMENT INTENET ==", data)
            cart_id = data.get('cart_id')

            # Fetch the cart and its items
            cart = Cart.objects.get(id=cart_id)
            cart_items = cart.items.filter(status='pending')

            # Calculate the base total price (without tax adjustments)
            total_price = sum(item.total_price for item in cart_items)
            # Add 350 AED if site_visit is True
            if cart.site_visit:
                # Fetch the first site_visit amount from the database
                site_visit_obj = site_visit.objects.first()
                if site_visit_obj and site_visit_obj.amount:
                    total_price += Decimal(str(site_visit_obj.amount))  # Add site_visit amount to the total price
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


            print("TOTAL PRICE ==", total_price)
            print("BASE PRICE ==", base_price)
            print("total_with_vat ==", total_with_vat)
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
                'is_vat_inclusive': is_vat_inclusive,
                'site_visit': cart.site_visit,
                'site_visit_fee': float(site_visit_obj.amount) if cart.site_visit and site_visit_obj else 0.00
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

                # Calculate the base total price (without tax adjustments)
                total_price = sum(item.total_price for item in cart_items)
                product_price = total_price
                # Add site_visit amount if site_visit is True
                site_visit_fee = Decimal('0.00')
                if cart.site_visit:
                    # Fetch the first site_visit amount from the database
                    site_visit_obj = site_visit.objects.first()
                    if site_visit_obj and site_visit_obj.amount:
                        site_visit_fee = Decimal(str(site_visit_obj.amount))
                        total_price += site_visit_fee  # Add site_visit amount to the total price

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

                # Get the latest customer address
                customer_address = Customer_Address.objects.filter(customer=customer).latest('id')

                # Create an order with the transaction ID and VAT details
                order = Order.objects.create(
                    customer=customer,
                    address=customer_address,
                    cart=cart,
                    payment_method='card',
                    payment_status='paid',
                    amount=total_with_vat,  # Use total_with_vat instead of total_price
                    transaction_id=payment_intent_id, # Add from cart
                    site_visit=cart.site_visit,
                    site_visit_fee=site_visit_fee,  # Store site visit fee
                    vat_percentage=vat_percentage,  # Store VAT percentage
                    vat_amount=vat_amount  # Store VAT amount
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
                    'product_price': float(product_price),
                    'base_product_amount': float(base_price),
                    'vat_percentage': float(vat_percentage),
                    'vat_amount': float(vat_amount),
                    'total_with_vat': float(total_with_vat),
                    'customer_name': customer.user.first_name,
                    'customer_email': customer.user.email,
                    'billing_address': f"{customer_address.address_line1}, {customer_address.city}, {customer_address.zip_code}",
                    'transaction_id': payment_intent_id,
                    'site_visit_fee': float(site_visit_fee)  # Include site visit fee in email
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
                    'transaction_id': payment_intent_id,
                    'base_product_amount': float(base_price),
                    'vat_percentage': float(vat_percentage),
                    'vat_amount': float(vat_amount),
                    'total_with_vat': float(total_with_vat),
                    'site_visit': order.site_visit,
                    'site_visit_fee': float(site_visit_fee)  # Include site visit fee in response
                })

            else:
                return JsonResponse({'success': False, 'message': 'Payment failed.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



# Order Detail View

class CustomerOrderDetailView(APIView):
    def get(self, request, customer_id):
        try:
            # Check if the customer exists
            customer = Customer.objects.filter(id=customer_id).first()
            if not customer:
                return Response(
                    {"error": "Customer not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Fetch all orders for the given customer ID
            orders = Order.objects.filter(customer=customer).order_by('-id')
            if not orders.exists():
                return Response(
                    {"error": "No orders found for this customer."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize the orders
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Order Details view

class OrderDetailView(RetrieveAPIView):
    queryset = Order.objects.select_related('customer__user', 'address', 'cart').prefetch_related('cart__items')
    serializer_class = OrderDetailSerializer
    # permission_classes = [IsAuthenticated]


# SEND EMAIL RFQ
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import now


class RFQRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get("email")
        name = data.get("name")
        mobile = data.get("mobile")
        cart_items = data.get("cart_items", [])
        subtotal = data.get("subtotal", 0)
        site_visit = data.get("site_visit", False)
        site_visit_fee = data.get("site_visit_fee", 0)
        total = data.get("total", 0)

        # Set up current date and valid until date (20 days from now)
        current_date = now()
        valid_until = (current_date + timedelta(days=20)).strftime('%d %b %Y')

        # Generate quote number (year + 4 digit sequence)
        year = current_date.strftime('%Y')
        # Get last quote number and increment
        last_quote = 1000  # Default starting number
        # You might want to store and retrieve this from a database
        quote_number = f"{last_quote + 1}"

        # Generate reference number
        ref_number = f"{year}-{str(random.randint(10000, 99999))}"

        # Check for existing user with this email
        user = None
        client_address = None

        if email:
            try:
                user = CustomUser.objects.get(email=email)
                # Try to get customer for this user
                try:
                    customer = Customer.objects.get(user=user)
                    # Check if customer has any addresses
                    addresses = Customer_Address.objects.filter(customer=customer).order_by('-id')
                    if addresses.exists():
                        client_address = addresses.first()
                except Customer.DoesNotExist:
                    pass
            except CustomUser.DoesNotExist:
                pass  # No user found with this email

        # Create Client_user object
        client_user = Client_user.objects.create(
            user=user,
            name=name,
            mobile=mobile,
            email=email,
            status='lead'
        )

        # Calculate VAT amount (5%)
        vat_amount = float(total) * 0.05
        subtotal_without_vat = float(total) - vat_amount

        # Format currency values
        formatted_total = "{:,.2f}".format(float(total))
        formatted_subtotal = "{:,.2f}".format(subtotal_without_vat)
        formatted_vat = "{:,.2f}".format(vat_amount)

        # Render and send email
        context = {
            # Company info
            "company_name": "Brand Experts Advertising LLC",
            "company_address": "Industrial Area 17, Sharjah Kalba Ring Road",
            "company_city": "Sharjah",
            "company_country": "United Arab Emirates",
            "company_po_box": "PO Box 23943",
            "company_phone": "+971 6 531 4088",
            "company_email": "hello@brandexperts.ae",

            # Quote info
            "quote_number": quote_number,
            "ref_number": ref_number,
            "current_datetime": current_date.strftime('%Y-%m-%d'),
            "valid_until": valid_until,

            # Client info
            "client_name": name,
            "client_email": email,
            "client_mobile": mobile,
            "client_address": client_address,
            "contact_person": f"Mr.{name}" if name else None,

            # Order details
            "quote_title": 'Quote for "Available for Rent" Unit Stickers',
            "cart_items": cart_items,
            "subtotal": formatted_subtotal,
            "vat_amount": formatted_vat,
            "total": formatted_total,
            "site_visit": site_visit,
            "site_visit_fee": site_visit_fee,
        }

        # Create HTML content for email
        html_email_content = render_to_string("rfq_email.html", context)
        text_content = strip_tags(html_email_content)

        # Create a special version for PDF (using a separate template for better PDF compatibility)
        html_pdf_content = render_to_string("rfq_pdf.html", context)

        # Create a simple email message
        msg = EmailMultiAlternatives(
            subject="Request for Quotation (RFQ) - BrandExperts",
            body=text_content,
            from_email="hello@brandexperts.ae",
            to=[email]
        )
        msg.attach_alternative(html_email_content, "text/html")

        # Generate PDF from HTML using xhtml2pdf
        try:
            # Create a file-like buffer to receive PDF data
            buffer = BytesIO()

            # Import xhtml2pdf library
            from xhtml2pdf import pisa

            # Convert HTML to PDF
            pisa_status = pisa.CreatePDF(
                html_pdf_content,  # the HTML to convert
                dest=buffer,  # file handle to receive result
                encoding='UTF-8'
            )

            # Close the PDF buffer
            buffer.seek(0)

            # Create a PDF filename
            pdf_filename = f"BrandExperts_Quote_{quote_number}.pdf"

            # Only attach PDF if successful
            if not pisa_status.err:
                # Attach PDF to email
                msg.attach(pdf_filename, buffer.getvalue(), 'application/pdf')
            else:
                print(f"Error generating PDF with xhtml2pdf: {pisa_status.err}")

        except Exception as e:
            # Log the error but continue with sending the email
            print(f"Error generating PDF: {e}")

        # Send the email
        msg.send()

        return Response(
            {"message": "RFQ email sent successfully with PDF quote attachment."},
            status=status.HTTP_200_OK
        )


# SAVE DESIGNER DETAILS

class CustomerDesignView(APIView):
    def post(self, request):
        serializer = CustomerDesignSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        response_data = {}

        # Handle anonymous UUID
        anonymous_uuid = data.get('anonymous_uuid')
        customer = data.get('customer')

        # Generate new UUID if neither customer nor anonymous_uuid is provided
        if not anonymous_uuid and not customer:
            anonymous_uuid = uuid.uuid4()
            response_data['anonymous_uuid'] = str(anonymous_uuid)

        # Product handling
        product = None
        if data.get('product'):
            try:
                product = Product.objects.get(pk=data['product'].id)
                product_data = {
                    'product_name': product.name,
                    'product_min_width': float(product.min_width),
                    'product_min_height': float(product.min_height),
                    'product_max_width': float(product.max_width),
                    'product_max_height': float(product.max_height),
                    'product_price': float(product.price) if product.price else None,
                    'product_image': product.image1
                }
                response_data.update(product_data)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update or create logic
        update_data = {
            'product': product,
            'product_name': product.name if product else None,
            'product_min_width': product.min_width if product else None,
            'product_min_height': product.min_height if product else None,
            'product_max_width': product.max_width if product else None,
            'product_max_height': product.max_height if product else None,
            'product_price': product.price if product else None,
            'product_image': product.image1 if product else None,
            'width': data.get('width'),
            'height': data.get('height'),
            'unit': data.get('unit', 'cm'),
            'quantity': data.get('quantity', 1),
            'design_data': json.dumps(data['design_data']),
            'design_image_url': data.get('design_image_url', None),  # Add design_image_url
        }

        # Create or update based on customer or anonymous_uuid
        if customer:
            design, created = CustomerDesign.objects.update_or_create(
                customer=customer,
                defaults=update_data
            )
        elif anonymous_uuid:
            design, created = CustomerDesign.objects.update_or_create(
                anonymous_uuid=anonymous_uuid,
                defaults=update_data
            )
        else:
            return Response({"error": "Missing identifier"}, status=status.HTTP_400_BAD_REQUEST)

        # Build response
        response_data.update({
            'id': str(design.id),
            'created_at': design.created_at,
            'updated_at': design.updated_at,
            'design_data': design.get_design_data(),
            'width': float(design.width) if design.width else None,
            'height': float(design.height) if design.height else None,
            'unit': design.unit,
            'quantity': design.quantity,
            'design_image_url': design.design_image_url,  # Include design_image_url in response
        })

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class GenerateAnonymousUUID(APIView):
    def get(self, request):
        """
        Generates a unique UUID for anonymous users.
        Ensures the UUID does not already exist in the CustomerDesign model.
        """
        max_attempts = 10  # Maximum attempts to generate a unique UUID
        for _ in range(max_attempts):
            new_uuid = uuid.uuid4()
            # Check if the UUID already exists in the database
            if not CustomerDesign.objects.filter(anonymous_uuid=new_uuid).exists():
                return Response(
                    {"anonymous_uuid": str(new_uuid)},
                    status=status.HTTP_200_OK
                )

        # If no unique UUID can be generated after max attempts
        return Response(
            {"error": "Unable to generate a unique UUID. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# GET DESIGN

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import CustomerDesign


def convert_units(value, from_unit, to_unit):
    """Convert a value from one unit to another using meter as base unit"""
    unit_to_meters = {
        'mm': Decimal('0.001'),
        'cm': Decimal('0.01'),
        'meter': Decimal('1'),
        'inches': Decimal('0.0254'),
        'feet': Decimal('0.3048'),
        'yard': Decimal('0.9144'),
    }

    if from_unit not in unit_to_meters or to_unit not in unit_to_meters:
        raise ValueError("Invalid unit provided")

    value_in_meters = Decimal(str(value)) * unit_to_meters[from_unit]
    return value_in_meters / unit_to_meters[to_unit]

def generate_design_image(request, uid):
    # Fetch the design from the database
    design = get_object_or_404(CustomerDesign, id=uid)

    try:
        design_data = json.loads(design.design_data)
    except json.JSONDecodeError as e:
        return JsonResponse({"error": f"Invalid JSON: {e}"}, status=400)

    # Determine canvas size
    product = design.product
    if product and design.product_max_width and design.product_max_height:
        canvas_width = int(design.product_max_width)
        canvas_height = int(design.product_max_height)
    else:
        frame_data = design_data.get("frame", {})
        canvas_width = int(frame_data.get("width", 1200))
        canvas_height = int(frame_data.get("height", 1200))



    # Create TRANSPARENT canvas (RGBA with alpha=0)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)

    # Process all layers
    for scene in design_data.get("scenes", []):
        for layer in scene.get("layers", []):
            layer_type = layer.get("type")

            # Convert negative coordinates to positive
            left = max(0, int(layer.get("left", 0)))
            top = max(0, int(layer.get("top", 0)))

            if layer_type == "Background":
                # Draw background rectangle
                draw.rectangle(
                    [
                        left,
                        top,
                        left + int(layer["width"]),
                        top + int(layer["height"])
                    ],
                    fill=layer.get("fill", "#FFFFFF")
                )

            elif layer_type == "StaticImage":
                try:
                    response = requests.get(layer["src"], timeout=10)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content)).convert("RGBA")
                        img = img.resize((
                            int(layer["width"] * layer.get("scaleX", 1)),
                            int(layer["height"] * layer.get("scaleY", 1))
                        ))
                        # Ensure image stays within canvas bounds
                        paste_x = max(0, min(left, canvas_width - img.width))
                        paste_y = max(0, min(top, canvas_height - img.height))
                        canvas.paste(img, (paste_x, paste_y), img)
                except Exception as e:
                    print(f"Image Error: {str(e)}")

            elif layer_type == "StaticText":
                try:
                    text = layer.get("text", "")
                    fill_color = layer.get("fill", "#000000")
                    font_size = int(layer.get("fontSize", 20))

                    # Load font with fallback
                    font = None
                    if "fontURL" in layer:
                        try:
                            font_data = requests.get(layer["fontURL"], timeout=5).content
                            font = ImageFont.truetype(BytesIO(font_data), font_size)
                        except:
                            pass
                    if not font:
                        font = ImageFont.load_default(size=font_size)

                    # Calculate text position
                    text_x = max(0, min(left, canvas_width))
                    text_y = max(0, min(top, canvas_height))

                    draw.text((text_x, text_y), text, font=font, fill=fill_color)
                except Exception as e:
                    print(f"Text Error: {str(e)}")

    # Save as PNG with transparency
    image_filename = f"{uid}_{uuid.uuid4().hex}.png"
    image_path = os.path.join(settings.MEDIA_ROOT, "designs", image_filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    canvas.save(image_path, "PNG")

    # Update model
    design.design_image_url = settings.MEDIA_URL + "designs/" + image_filename
    design.save()

    # Calculate total price
    total_price = 0
    if product and product.price:
        try:
            from_unit = design.unit if design.unit else 'cm'
            to_unit = product.size

            # Handle width conversion or default to product's minimum
            if design.width is not None:
                width = Decimal(str(design.width))
                converted_width = convert_units(width, from_unit, to_unit)
            else:
                # Directly use product's min width in its native unit
                converted_width = product.min_width

            # Handle height conversion or default to product's minimum
            if design.height is not None:
                height = Decimal(str(design.height))
                converted_height = convert_units(height, from_unit, to_unit)
            else:
                # Directly use product's min height in its native unit
                converted_height = product.min_height

            area = converted_width * converted_height
            quantity = design.quantity if design.quantity is not None else 1
            total_price = float(area * product.price * quantity)

        except (ValueError, InvalidOperation, TypeError, AttributeError) as e:
            print(f"Price calculation error: {str(e)}")

    response_data = {
        "amazon_url": product.amazon_url if product and product.amazon_url else None,
        "allow_direct_add_to_cart": product.allow_direct_add_to_cart if product else False,
        "id": product.id if product else None,
        "name": product.name if product else "Unnamed Product",
        "design_image": request.build_absolute_uri(design.design_image_url),
        "quantity": design.quantity,
        "timestamp": int(time.time() * 1000),  # Current timestamp in milliseconds
        "total": round(total_price, 2),
        "customSize": {
            "width": float(design.width) if design.width else 1,
            "height": float(design.height) if design.height else 1,
            "unit": design.unit if design.unit else "cm"
        }
    }
    return JsonResponse(response_data)
    # return JsonResponse({
    #     "product_name":product.name,
    #     "image_url": request.build_absolute_uri(design.design_image_url),
    #     "canvas_width": canvas_width,
    #     "canvas_height": canvas_height,
    #     "product_id": str(product.id) if product else None,
    #     "quantity": design.quantity,
    #     "total_price": product.price
    # })


from .models import PasswordResetSession


@api_view(['POST'])
def send_otp(request):
    email = request.data.get('email')
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    # Check if email exists
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Email not found"}, status=404)

    # Generate OTP and session token
    otp = str(random.randint(100000, 999999))
    session = PasswordResetSession.objects.create(email=email, otp=otp)

    # Send OTP via email
    send_mail(
        'Password Reset OTP',
        f'Your OTP is: {otp}',
        'hello@brandexperts.ae',
        [email],
        fail_silently=False,
    )


    return JsonResponse({
        "message": "OTP sent successfully",
        "session_token": str(session.session_token)
    }, status=200)


@api_view(['POST'])
def verify_otp2(request):
    session_token = request.data.get('session_token')
    otp = request.data.get('otp')

    if not session_token or not otp:
        return JsonResponse({"error": "Session token and OTP are required"}, status=400)

    # Validate UUID format
    try:
        session_token = uuid.UUID(session_token, version=4)
    except ValueError:
        return JsonResponse({"error": "Invalid session token"}, status=400)

    try:
        session = PasswordResetSession.objects.get(session_token=session_token)
    except PasswordResetSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session token"}, status=404)

    if not session.is_valid():
        return JsonResponse({"error": "Session expired or already used"}, status=400)

    if session.otp != otp:
        return JsonResponse({"error": "Invalid OTP"}, status=400)

    session.is_verified = True
    session.save()

    return JsonResponse({"message": "OTP verified successfully"}, status=200)


@api_view(['POST'])
def reset_password(request):
    session_token = request.data.get('session_token')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not session_token or not new_password or not confirm_password:
        return JsonResponse({"error": "Session token, new password, and confirm password are required"}, status=400)

    if new_password != confirm_password:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    # Validate UUID format
    try:
        session_token = uuid.UUID(session_token, version=4)
    except ValueError:
        return JsonResponse({"error": "Invalid session token"}, status=400)

    try:
        session = PasswordResetSession.objects.get(session_token=session_token)
    except PasswordResetSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session token"}, status=404)

    # Debugging logs
    print(f"Session Found: {session.email}, Verified: {session.is_verified}, Created At: {session.created_at}, Token: {session.session_token}")

    # Check if the session is still valid
    if not session.is_valid():
        return JsonResponse({"error": "Session expired"}, status=400)

    if not session.is_verified:
        return JsonResponse({"error": "OTP not verified"}, status=400)

    try:
        user = CustomUser.objects.get(email=session.email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    # Update password
    user.set_password(new_password)
    user.save()

    # Invalidate the session
    session.delete()

    return JsonResponse({"message": "Password reset successfully"}, status=200)


# @api_view(['POST'])
# def upload_image(request):
#     if 'image' not in request.FILES:
#         return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
#
#     image = request.FILES['image']
#
#     # Validate file size (5MB limit)
#     if image.size > 5 * 1024 * 1024:
#         return Response({'error': 'File size exceeds 5MB limit'}, status=status.HTTP_400_BAD_REQUEST)
#
#     # Validate file type
#     allowed_types = ['image/jpeg', 'image/png', 'image/gif']
#     if image.content_type not in allowed_types:
#         return Response({'error': 'Invalid file type. Allowed: JPEG, PNG, GIF'},
#                         status=status.HTTP_400_BAD_REQUEST)
#
#     try:
#         # Generate unique filename
#         ext = image.name.split('.')[-1]
#         filename = f"{uuid.uuid4().hex}.{ext}"
#         filepath = os.path.join(settings.MEDIA_ROOT, filename)
#
#         # Save file
#         with open(filepath, 'wb+') as destination:
#             for chunk in image.chunks():
#                 destination.write(chunk)
#
#         # Build URL
#         image_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
#
#         return Response({'url': image_url}, status=status.HTTP_201_CREATED)
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Test


from rest_framework.decorators import api_view
from rest_framework.response import Response
import random
import re
import requests
from urllib.parse import quote
import os
import pytesseract
from PIL import Image
from django.conf import settings

# Gemini AI API Key (replace with your actual key)
GEMINI_API_KEY = settings.GEMINI_API_KEY
import threading
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
# Twilio Configuration
TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_NUMBER = settings.TWILIO_WHATSAPP_NUMBER # Twilio sandbox number
EMERGENCY_CONTACT = settings.EMERGENCY_CONTACT
CONTENT_SID = settings.CONTENT_SID

import random


def handle_creator_questions(text):
    """Handle questions about the bot's creator/developer"""
    creator_keywords = [
        'creator', 'developer', 'made you', 'created you',
        'who are you', 'your maker', 'your parent', 'your boss'
    ]

    responses = [
        "I am an AI assistant designed to empower individuals through advanced deep learning technologies. My development was guided by Revathy.",
        "Crafted with precision and innovation, I am an AI assistant built to assist and enhance experiences. My creator, Revathy, envisioned me to make a difference.",
        "Born from deep learning and innovation, I exist to assist and inspire. Revathy, my developer, has shaped me to bring AI-driven solutions to the world.",
        "I am the product of AI ingenuity, designed to make the world more accessible and intelligent. My development was led by Revathy with a vision for innovation.",
        "An AI assistant at your service, blending deep learning with human-centered design. Revathy is the mind behind my creation, guiding me to serve you better.",
        "I am the bridge between artificial intelligence and human needs, built to assist and empower. Revathy, my creator, designed me with purpose and precision.",
        "Created with the latest advancements in AI, I strive to assist and inspire. My developer, Revathy, brought me to life with a vision for intelligent assistance."
    ]

    if any(keyword in text.lower() for keyword in creator_keywords):
        return random.choice(responses)

    return None





# Modified emergency handling section
def send_emergency_alert_async(lat, lng):
    """Send WhatsApp alert using Twilio sandbox with template support"""

    def async_task():
        try:
            # Convert coordinates to floats first
            lat_float = float(lat)
            lng_float = float(lng)

            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            # Create message with template
            message = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                content_sid=CONTENT_SID,  # Your template SID
                content_variables=json.dumps({
                    "1": f"{lat_float:.6f}",
                    "2": f"{lng_float:.6f}",
                    "3": f"https://maps.google.com/?q={lat_float:.6f},{lng_float:.6f}"
                }),
                to=EMERGENCY_CONTACT
            )

            print(f"Alert sent: {message.sid}")
            print(f"Message Status: {message.status}")

        except ValueError as e:
            print(f"Invalid coordinates: {lat}, {lng} - {str(e)}")
        except TwilioRestException as e:
            print(f"Twilio Error: {e.code} - {e.msg}")
        except Exception as e:
            print(f"General Error: {str(e)}")

    threading.Thread(target=async_task, daemon=True).start()


import time



def extract_text_with_ocrspace(image_file):
    API_KEY = 'K82218497288957'  # Your API key here
    API_URL = 'https://api.ocr.space/parse/image'

    try:
        # Read image file content
        image_bytes = image_file.read()

        response = requests.post(
            API_URL,
            files={'image': (image_file.name, image_bytes)},
            data={
                'apikey': API_KEY,
                'language': 'eng',
                'isOverlayRequired': False,
                'OCREngine': 2  # Better accuracy engine
            }
        )

        response.raise_for_status()
        result = response.json()

        if result.get('IsErroredOnProcessing', False):
            error_message = result.get('ErrorMessage', 'Unknown OCR error')
            return None, error_message

        parsed_results = result.get('ParsedResults', [])
        if not parsed_results:
            return None, 'No text found in image'

        extracted_text = ' '.join([res.get('ParsedText', '') for res in parsed_results]).strip()
        extracted_text = extracted_text.replace('\n', '   ')  # 3 spaces for slight pause
        return extracted_text, None

    except Exception as e:
        return None, str(e)





def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
        headers = {'User-Agent': 'YourAppName/1.0 (contact@yourapp.com)'}  # Required for Nominatim
        response = requests.get(url, headers=headers).json()
        address = response.get('address', {})
        return f"{address.get('road', '')} {address.get('city', '')} {address.get('country', '')}".strip()
    except:
        return "Location details not available"


def get_nearby_places(lat, lng, query):
    try:
        # Map query to OpenStreetMap amenity tags
        amenity_mapping = {
            "restaurant": "restaurant",
            "hospital": "hospital",
            "park": "park",
            "hotel": "hotel",
            "bus_station": "bus_station",
            "cinema": "cinema",
            "mall":"mall",
            "police": "police",
            "fire_station": "fire_station",
            "pharmacy": "pharmacy",
            "parking": "parking",
            "school": "school",
            "university": "university",
            "library": "library",
            "museum": "museum",
            "zoo": "zoo",
            "gym": "gym",
            "bank": "bank",
            "atm": "atm",
            "post_office": "post_office",
            "supermarket": "supermarket",
            "bakery": "bakery",
            "cafe": "cafe",
            "bar": "bar",
            "pub": "pub",
            "nightclub": "nightclub",
            "airport": "airport",
            "railway_station": "railway_station",
            "train_station": "train_station",
            "train": "train",
            "automobile": "automobile",
            "auto stand": "auto stand",
            "medical college": "medical college",
            "medical store": "medical store",

        }

        # Get the correct OpenStreetMap tag
        amenity = amenity_mapping.get(query, query)

        # Overpass API query
        overpass_query = f"""
        [out:json];
        node(around:1000,{lat},{lng})["amenity"="{amenity}"];
        out;
        """

        # Make the request
        url = "https://overpass-api.de/api/interpreter"
        response = requests.post(url, data=overpass_query)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the response
        places = response.json().get('elements', [])
        if not places:
            return None  # No places found

        # Extract place names
        return [place['tags'].get('name', 'Unnamed place')
                for place in places
                if 'tags' in place][:3]
    except Exception as e:
        print(f"Error fetching nearby places: {e}")
        return None


def get_wikipedia_summary(query):
    try:
        # Clean up the query (remove typos, special characters, etc.)
        query = re.sub(r'[^\w\s]', '', query)  # Remove special characters
        query = query.strip()  # Remove leading/trailing spaces

        # Fetch Wikipedia summary
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query)}"
        response = requests.get(url).json()
        return response.get('extract', 'No information found')
    except:
        return "Could not fetch information at this time"


def get_youtube_link(query):
    try:
        # YouTube Data API endpoint
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 1,
            'key': settings.YOUTUBE_API_KEY  # Replace with your API key
        }

        # Make the request
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Extract the video link
        items = response.json().get('items', [])
        if items:
            video_id = items[0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
        return None
    except Exception as e:
        print(f"Error fetching YouTube link: {e}")
        return None


def ask_gemini_ai(query, location=None):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}

        # Build the prompt
        prompt = query
        if location and any(word in query for word in ["near me", "nearby", "close to me"]):
            prompt += f"\n\nContext: User's current location is {location}."

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        if "candidates" in result and result["candidates"]:
            full_response = result["candidates"][0]["content"]["parts"][0]["text"]

            # Step 1: Remove markdown formatting (e.g., ##, **, etc.)
            cleaned_response = re.sub(r'#+\s*', '', full_response)  # Remove headers
            cleaned_response = re.sub(r'\*\*', '', cleaned_response)  # Remove bold
            cleaned_response = re.sub(r'\*', '', cleaned_response)  # Remove italics

            # Step 2: Replace newlines with spaces
            cleaned_response = cleaned_response.replace('\n', ' ')

            # Step 3: Split into sentences and truncate to 4 sentences
            sentences = re.split(r'(?<=[.!?])\s+', cleaned_response)  # Split by punctuation
            truncated_response = ' '.join(sentences[:3])  # Join first 4 sentences
            if len(sentences) > 3:
                truncated_response += '.'  # Add a period if the response was truncated

            return truncated_response
        return "No information found."
    except Exception as e:
        print(f"Error fetching Gemini AI response: {e}")
        return "Could not fetch information at this time."


def contains_word(text, words):
    return any(re.search(rf'\b{word}\b', text, re.IGNORECASE) for word in words)


# Main API View

@api_view(["POST"])
def process_text(request):
    data = {
        "response": "",
        "camera": False,
        "emergency": False,
        "longitude": request.data.get("longitude"),
        "latitude": request.data.get("latitude"),
        "map_link": "",
        "response_urls": [] , # New field for YouTube or Wikipedia URLs
        "app_exit": False
    }
    text = request.data.get("text", "").lower().strip()

    # 1. Exit command handling
    exit_pattern = r'\b(exit|close|bye|shutdown|quit|stop|goodbye)\b|(close|terminate)\s+(app|application)'
    if re.search(exit_pattern, text, re.IGNORECASE):
        data['response'] = "Okay, closing the app. Goodbye!"
        data['app_exit'] = True
        return Response(data)

    # 2. Handle creator/developer questions
    creator_response = handle_creator_questions(text)
    if creator_response:
        data['response'] = creator_response
        return Response(data)

    # Check for image upload
    if 'image' in request.FILES:
        try:
            print("Image found..!")
            image_file = request.FILES['image']
            print(f"Received file: {image_file.name}, Size: {image_file.size} bytes")

            # Validate file size (max 5MB)
            if image_file.size > 5 * 1024 * 1024:
                data['response'] = "Image too large (max 5MB)"
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            # Extract text using OCR.space
            extracted_text, error = extract_text_with_ocrspace(image_file)
            print(f"OCR Response - Text: {extracted_text}, Error: {error}")

            if error:
                data['response'] = f"OCR Error: {error}"
                return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if extracted_text:
                data['response'] = extracted_text
            else:
                data['response'] = "No text detected. Please ensure clear image with visible text."

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Image processing error: {str(e)}")
            data['response'] = f"Processing Error: {str(e)}"
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    # Camera detection
    camera_words = ['camera', 'open camera', 'scan', 'scanner']
    data['camera'] = contains_word(text, camera_words)

    # Emergency detection
    emergency_words = ['emergency', 'help', 'rescue', 'urgent', 'accident', 'danger', 'fire', 'police', 'ambulance',
                       'robbery']
    data['emergency'] = contains_word(text, emergency_words)

    # 4. Emergency handling (async)
    if data['emergency']:
        lat = data['latitude']
        lng = data['longitude']
        map_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}&zoom=16" if lat else ""

        # Start async WhatsApp send
        if lat and lng:
            send_emergency_alert_async(lat, lng)
            data['response'] = f"Emergency response sent. An emergency message with your current location has been texted to the authorities, and the dialer will now open to initiate a call."
        else:
            data['response'] = "Emergency detected! But location missing - enable location services."

        data['map_link'] = map_link
        return Response(data)

    # Generate map link (only for location-related responses)
    if data['latitude'] and data['longitude']:
        data['map_link'] = f"https://www.openstreetmap.org/?mlat={data['latitude']}&mlon={data['longitude']}&zoom=16"

    # Handle greetings
    greeting_words = ['hi', 'hello', 'hey', 'hola', 'namaste','hai']
    if contains_word(text, greeting_words):
        data['response'] = random.choice([
            "Hello! How can I assist you today?",
            "Welcome! What would you like to do?",
            "Glad to have you here! Need any help?"
        ])
        return Response(data)

    # 3. Location-based priority handling
    def handle_location_requests():
        # A. Current location request
        if re.search(r'\b(current location|where am i)\b', text):
            if data['latitude'] and data['longitude']:
                address = get_address_from_coords(data['latitude'], data['longitude'])
                data[
                    'response'] = f"Your approximate location: {address}" if address else "Location found but address unavailable"
            else:
                data['response'] = "Location coordinates not provided"
            return True

        # B. Nearby places lookup
        place_mapping = {
            'bus_station': {'keywords': ['bus stop', 'bus stand', 'bus station'],
                            'query': 'public transit stop'},
            'restaurant': {'keywords': ['restaurant', 'dine', 'eat']},
            'hospital': {'keywords': ['hospital', 'clinic']},
            'park': {'keywords': ['park', 'garden']},
            'hotel': {'keywords': ['hotel', 'lodging']},
            'cinema': {'keywords': ['theater', 'theatre', 'cinema']}
        }

        for place_type, config in place_mapping.items():
            if contains_word(text, config['keywords']):
                if not (data['latitude'] and data['longitude']):
                    data['response'] = "Location access required to find nearby places."
                    return True

                places = get_nearby_places(
                    data['latitude'],
                    data['longitude'],
                    config.get('query', place_type)
                )

                if places:
                    data['response'] = f"Nearby {place_type.replace('_', ' ')}s: {', '.join(places[:3])}"
                else:
                    address = get_address_from_coords(data['latitude'], data['longitude'])
                    prompt = f"Are there any {config.get('query', place_type)}s near {address or 'this location'}?"
                    data['response'] = ask_gemini_ai(prompt, f"{data['latitude']},{data['longitude']}")
                return True
        return False

    if handle_location_requests():
        return Response(data)

    # 4. Enhanced location-aware Gemini integration
    location_triggers = r'\b(near( me)?|closest|close by|around|nearby|in my area)\b'
    if re.search(location_triggers, text, re.IGNORECASE):
        if data['latitude'] and data['longitude']:
            address = get_address_from_coords(data['latitude'], data['longitude'])
            prompt = f"{text} near {address}" if address else f"{text} at coordinates {data['latitude']}, {data['longitude']}"
            data['response'] = ask_gemini_ai(prompt, f"{data['latitude']},{data['longitude']}")
        else:
            data['response'] = "Please enable location services for this feature."
        return Response(data)

    # 5. Core functionality handlers
    handlers = [
        {
            'condition': lambda: contains_word(text, ['camera', 'scan']),
            'response': "Camera access requested. When ready, point your camera at the subject.",
            'field': 'camera'
        },
        {
            'condition': lambda: contains_word(text, ['emergency', 'help']),
            'response': "Emergency detected! Contact local authorities. Map link provided.",
            'field': 'emergency'
        },
        {
            'condition': lambda: 'play' in text,
            'action': lambda: (get_youtube_link(text.replace('play', '').strip())),
            'response': "Here's a YouTube link:",
            'url_field': True
        }
    ]

    for handler in handlers:
        if handler['condition']():
            if 'action' in handler:
                result = handler['action']()
                if result:
                    data['response_urls'].append(result)
            data['response'] = handler.get('response', '')
            if 'field' in handler:
                data[handler['field']] = True
            return Response(data)

    # 6. Knowledge base fallback
    wikipedia_summary = get_wikipedia_summary(text)
    if "No information found" not in wikipedia_summary:
        data['response'] = wikipedia_summary
        data['response_urls'].append(f"https://en.wikipedia.org/wiki/{quote(text)}")
    else:
        data['response'] = ask_gemini_ai(text,
                                         f"{data['latitude']},{data['longitude']}" if data['latitude'] else None
                                         )

    return Response(data)
