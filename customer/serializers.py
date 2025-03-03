from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import *


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