import json

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
    design_data = serializers.JSONField()  # Handle JSON parsing/validation

    class Meta:
        model = CustomerDesign
        fields = [
            'id', 'customer', 'anonymous_uuid', 'product',
            'width', 'height', 'unit', 'quantity', 'design_data'
        ]
        extra_kwargs = {
            'customer': {'required': False},
            'anonymous_uuid': {'required': False},
            'product': {'required': False},
        }

    def validate(self, data):
        # Ensure either customer or anonymous_uuid is provided
        if not data.get('customer') and not data.get('anonymous_uuid'):
            raise serializers.ValidationError("Either customer or anonymous_uuid must be provided")

        # Validate JSON data structure
        try:
            json.dumps(data['design_data'])  # Test JSON serialization
        except TypeError:
            raise serializers.ValidationError("Invalid JSON data structure")

        return data

    def to_internal_value(self, data):
        # Convert UUID strings to UUID objects if present
        if 'anonymous_uuid' in data and data['anonymous_uuid']:
            try:
                data['anonymous_uuid'] = uuid.UUID(data['anonymous_uuid'])
            except ValueError:
                raise serializers.ValidationError({"anonymous_uuid": "Invalid UUID format"})
        return super().to_internal_value(data)