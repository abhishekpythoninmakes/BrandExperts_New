import json

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import *
import re

class AuthInitiateSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate_identifier(self, value):
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        mobile_regex = r'^\+\d{1,3}\d{10}$'  # E.164 format with country code

        if '@' in value:
            if not re.match(email_regex, value):
                raise serializers.ValidationError("Invalid email format")
            return {'type': 'email', 'value': value}
        else:
            if not re.match(mobile_regex, value):
                raise serializers.ValidationError("Invalid mobile number format (must include country code)")
            return {'type': 'mobile', 'value': value}


class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)


class CompleteRegistrationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)# Required only if identifier is email
    country_code = serializers.CharField(max_length=5, required=False)

    def validate(self, data):
        otp_record = OTPRecord.objects.filter(otp=data['otp']).first()
        if not otp_record:
            raise serializers.ValidationError("Invalid or expired OTP")


        return data



class CustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    mobile = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Check if email already exists
        if CustomUser.objects.filter(username=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        # Check if mobile number already exists
        if Customer.objects.filter(mobile=data['mobile']).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")

        return data

    def create(self, validated_data):
        # Create the CustomUser instance
        user = CustomUser.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        # Set the password using set_password
        user.set_password(validated_data['password'])
        user.save()

        # Create the Customer instance
        customer = Customer.objects.create(
            user=user,
            mobile=validated_data['mobile']
        )
        return customer





class WarrantyRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarrantyRegistration
        fields = '__all__'
        read_only_fields = ['warranty_number']  # Make warranty_number read-only


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    hire_designer = serializers.StringRelatedField()

    # Option details fields
    thickness_details = serializers.SerializerMethodField()
    delivery_details = serializers.SerializerMethodField()
    turnaround_details = serializers.SerializerMethodField()
    installation_details = serializers.SerializerMethodField()
    distance_details = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'custom_width', 'custom_height', 'size_unit',
            'design_image', 'quantity', 'price', 'total_price', 'hire_designer',
            'status', 'created_at', 'is_smart', 'design_description',
            # Remove the direct foreign key fields from here
            'thickness_details', 'delivery_details', 'turnaround_details',
            'installation_details', 'distance_details'
        ]
        # Remove the extra_kwargs since we're not including the FK fields in response

    def get_thickness_details(self, obj):
        if obj.thickness:
            return {
                'id': obj.thickness.id,
                'size': getattr(obj.thickness, 'size', None),
                'price': getattr(obj.thickness, 'price', None) or
                         getattr(obj.thickness, 'price_decimal', None)
            }
        return None

    def get_delivery_details(self, obj):
        if obj.delivery:
            return {
                'id': obj.delivery.id,
                'name': getattr(obj.delivery, 'name', None),
                'price': getattr(obj.delivery, 'price_decimal', None) or
                         getattr(obj.delivery, 'price_percentage', None)
            }
        return None

    def get_turnaround_details(self, obj):
        if obj.turnaround_time:
            return {
                'id': obj.turnaround_time.id,
                'name': getattr(obj.turnaround_time, 'name', None),
                'price': getattr(obj.turnaround_time, 'price_decimal', None) or
                         getattr(obj.turnaround_time, 'price_percentage', None)
            }
        return None

    def get_installation_details(self, obj):
        if obj.installation:
            return {
                'id': obj.installation.id,
                'name': getattr(obj.installation, 'name', None),
                'days': getattr(obj.installation, 'days', None),
                'price': getattr(obj.installation, 'price_decimal', None) or
                         getattr(obj.installation, 'price_percentage', None)
            }
        return None

    def get_distance_details(self, obj):
        if obj.distance:
            return {
                'id': obj.distance.id,
                'km': getattr(obj.distance, 'km', None),
                'price': getattr(obj.distance, 'price_decimal', None) or
                         getattr(obj.distance, 'price_percentage', None)
            }
        return None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'status', 'created_at','items']

class CartItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = [
            'product', 'custom_width', 'custom_height', 'size_unit',
            'design_image', 'quantity', 'design_description', 'is_smart',
            'thickness', 'delivery', 'turnaround_time', 'installation', 'distance'
        ]

    def validate_quantity(self, value):
        """Ensure quantity is at least 1."""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer_Address
        fields = [
            'company_name', 'ext', 'address_line1', 'address_line2',
            'country', 'city', 'state', 'zip_code'
        ]

class OrderSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)
    address = CustomerAddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'status', 'ordered_date', 'payment_method',
            'payment_status', 'amount', 'delivered_date', 'transaction_id',
            'site_visit', 'site_visit_fee', 'vat_percentage', 'vat_amount',
            'cart', 'address'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)
    address = CustomerAddressSerializer(read_only=True)
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'status', 'ordered_date', 'payment_method',
            'payment_status', 'amount', 'delivered_date', 'transaction_id',
            'site_visit', 'site_visit_fee', 'vat_percentage', 'vat_amount',
            'cart', 'address'
        ]

    def get_customer(self, obj):
        """Return customer details"""
        if obj.customer and obj.customer.user:
            return {
                'id': obj.customer.id,
                'username': obj.customer.user.username,
                'first_name': obj.customer.user.first_name,
                'last_name': obj.customer.user.last_name,
                'email': obj.customer.user.email,
                'mobile': obj.customer.mobile,
                'country_code': obj.customer.country_code,
            }
        return None






class CustomerDesignSerializer(serializers.ModelSerializer):
    design_data = serializers.JSONField()
    anonymous_uuid = serializers.UUIDField(required=False)  # Explicitly declare to override validation

    class Meta:
        model = CustomerDesign
        fields = [
            'id', 'customer', 'anonymous_uuid', 'product',
            'width', 'height', 'unit', 'quantity', 'design_data', 'design_image_url'
        ]
        extra_kwargs = {
            'customer': {'required': False},
            'product': {'required': False},
            'anonymous_uuid': {'required': False, 'validators': []},  # No validation for anonymous_uuid
            'design_image_url': {'required': False},  # Optional field
        }

    def validate(self, data):
        # No validation for customer or anonymous_uuid
        try:
            json.dumps(data['design_data'])  # Validate JSON data structure
        except TypeError:
            raise serializers.ValidationError("Invalid JSON data structure")
        return data

    def to_internal_value(self, data):
        if 'anonymous_uuid' in data and data['anonymous_uuid']:
            try:
                data['anonymous_uuid'] = uuid.UUID(data['anonymous_uuid'])
            except ValueError:
                raise serializers.ValidationError({"anonymous_uuid": "Invalid UUID format"})
        return super().to_internal_value(data)


class EnableAlertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    alert_type = serializers.ChoiceField(choices=['email', 'mobile'])
    country_code = serializers.CharField(max_length=5, required=False)

class VerifyAlertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    alert_type = serializers.ChoiceField(choices=['email', 'mobile'])
    otp = serializers.CharField(max_length=6)



class OTPVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_identifier(self, value):
        if '@' in value:
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
                raise serializers.ValidationError("Invalid email format")
        else:
            if not any(c.isdigit() for c in value):
                raise serializers.ValidationError("Invalid mobile number")
        return value


class OTPUpdateSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    identifier = serializers.CharField(required=False, allow_null=True)
    country_code = serializers.CharField(required=False, allow_null=True)

    def validate_country_code(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Country code must start with '+'")
        return value


class OTPVerifySerializer2(serializers.Serializer):
    otp = serializers.CharField(required=True, min_length=6, max_length=6)




class FinalRegistrationSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, min_length=8, write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data


class RequestedEmailUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestedEmailUsers
        fields = ['name', 'email', 'mobile', 'company', 'status', 'type']



# New Order Serializers

from rest_framework import serializers
from .models import Order, Customer, Customer_Address, Cart, CartItem
from products_app.models import Product
from products_app.serializers import ProductListSerializer


class CustomerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_name', 'user_email', 'user_first_name', 'user_last_name', 'mobile', 'status']







    def get_items_count(self, obj):
        return obj.items.count()

    def get_total_amount(self, obj):
        return sum(item.total_price for item in obj.items.all() if item.total_price)


class OrderListSerializer(serializers.ModelSerializer):
    customer_details = CustomerSerializer(source='customer', read_only=True)
    address_details = CustomerAddressSerializer(source='address', read_only=True)
    cart_details = CartSerializer(source='cart', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_details', 'customer_name', 'customer_email',
            'address', 'address_details', 'cart', 'cart_details', 'status',
            'ordered_date', 'payment_method', 'payment_status', 'amount',
            'delivered_date', 'transaction_id', 'site_visit', 'site_visit_fee',
            'vat_percentage', 'vat_amount', 'items_count'
        ]

    def get_customer_name(self, obj):
        if obj.customer and obj.customer.user:
            return f"{obj.customer.user.first_name} {obj.customer.user.last_name}".strip()
        return "Unknown Customer"

    def get_customer_email(self, obj):
        if obj.customer and obj.customer.user:
            return obj.customer.user.email
        return None

    def get_items_count(self, obj):
        if obj.cart:
            return obj.cart.items.count()
        return 0


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'address', 'cart', 'status', 'payment_method',
            'payment_status', 'amount', 'delivered_date', 'transaction_id',
            'site_visit', 'site_visit_fee', 'vat_percentage', 'vat_amount'
        ]
        extra_kwargs = {
            'customer': {'required': True},
            'address': {'required': True},
            'amount': {'required': True},
        }

    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value

    def validate_payment_method(self, value):
        valid_methods = [choice[0] for choice in Order.PAYMENT_METHOD_CHOICES]
        if value not in valid_methods:
            raise serializers.ValidationError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        return value