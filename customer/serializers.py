from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Customer

class CustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    dob = serializers.DateField()
    mobile = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password and Confirm Password do not match.")

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
            last_name=validated_data['last_name'],
            password=make_password(validated_data['password'])  # Hash the password
        )

        # Create the Customer instance
        customer = Customer.objects.create(
            user=user,
            dob=validated_data['dob'],
            mobile=validated_data['mobile']
        )
        return customer