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
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)  # Required only if identifier is mobile
    mobile = serializers.CharField(max_length=20, required=False)  # Required only if identifier is email
    country_code = serializers.CharField(max_length=5, required=False)

    def validate(self, data):
        otp_record = OTPRecord.objects.filter(otp=data['otp']).first()
        if not otp_record:
            raise serializers.ValidationError("Invalid or expired OTP")

        # Determine missing fields based on identifier type
        if otp_record.email:  # Identifier was an email
            if 'mobile' not in data or not data['mobile']:
                raise serializers.ValidationError("Mobile number is required")
        elif otp_record.mobile:  # Identifier was a mobile number
            if 'email' not in data or not data['email']:
                raise serializers.ValidationError("Email is required")

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
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'custom_width', 'custom_height', 'size_unit',
            'design_image', 'quantity', 'price', 'total_price', 'hire_designer','status', 'created_at'
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'status', 'created_at','items']

class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity", "total_price"]  # Only updatable fields

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



class CartItemWithProductNameSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    # product_image = serializers.URLField(source='product.image1')

    class Meta:
        model = CartItem
        fields = [
            'id', 'product_name', 'custom_width', 'custom_height',
            'size_unit', 'design_image', 'quantity', 'price', 'total_price',
            'hire_designer', 'status', 'created_at'
        ]

class CartWithItemsSerializer(serializers.ModelSerializer):
    items = CartItemWithProductNameSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'status', 'created_at', 'items']

class PaymentSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    method = serializers.CharField(source='payment_method')
    status = serializers.CharField(source='payment_status')

class OrderDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    address = CustomerAddressSerializer()
    cart = CartWithItemsSerializer()
    payment = PaymentSerializer(source='*')
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, source='amount')
    site_visit_charge = serializers.DecimalField(max_digits=10, decimal_places=2, source='site_visit_fee')
    vat = serializers.DecimalField(max_digits=10, decimal_places=2, source='vat_amount')

    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'ordered_date', 'delivered_date', 'payment',
            'status', 'total_amount', 'cart', 'address', 'site_visit_charge', 'vat'
        ]

    def get_customer_name(self, obj):
        return obj.customer.user.get_full_name()


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