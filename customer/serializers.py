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


class CustomProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomProduct
        fields = "__all__"  # Includes all fields
        read_only_fields = ["status", "created_at", "customer"]