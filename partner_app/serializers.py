# serializers.py
import json

from rest_framework import serializers
from pep_app .models import Contact, Partners, Accounts


# class ContactCreateSerializer(serializers.ModelSerializer):
#     partner_user_id = serializers.IntegerField(write_only=True)
#     accounts = serializers.ListField(
#         child=serializers.CharField(),
#         required=False,
#         allow_empty=True
#     )
#
#     class Meta:
#         model = Contact
#         fields = [
#             'partner_user_id',
#             'name',
#             'email',
#             'mobile',
#             'accounts',
#             'additional_data',
#             'status'
#         ]
#         extra_kwargs = {
#             'name': {'required': True},
#             'email': {'required': True},
#             'mobile': {'required': True},
#             'status': {'required': False},
#             'additional_data': {'required': False}
#         }
#
#     def validate_partner_user_id(self, value):
#         try:
#             Partners.objects.get(user_id=value)
#         except Partners.DoesNotExist:
#             raise serializers.ValidationError("Partner not found with this user ID")
#         return value
#
#     def create(self, validated_data):
#         partner_user_id = validated_data.pop('partner_user_id')
#         account_names = validated_data.pop('accounts', [])  # Get accounts from request
#         partner = Partners.objects.get(user_id=partner_user_id)
#
#         contact = Contact.objects.create(
#             **validated_data,
#             partner=partner,
#             created_by=self.context['request'].user
#         )
#
#         # Add only the accounts provided in the request
#         for name in account_names:
#             account, _ = Accounts.objects.get_or_create(name=name)
#             contact.account.add(account)
#
#         return contact


class ContactCreateSerializer(serializers.ModelSerializer):
    partner_user_id = serializers.IntegerField(write_only=True)
    accounts = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    verification_data = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = [
            'partner_user_id',
            'name',
            'email',
            'mobile',
            'accounts',
            'additional_data',
            'status',
            'verification_data'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'mobile': {'required': True},
            'status': {'required': False},
            'additional_data': {'required': False}
        }

    def get_verification_data(self, obj):
        """Get verification data as a dictionary"""
        if not obj.email_verification_status:
            return {}
        try:
            return json.loads(obj.email_verification_status)
        except:
            return {}

    def validate_partner_user_id(self, value):
        try:
            Partners.objects.get(user_id=value)
        except Partners.DoesNotExist:
            raise serializers.ValidationError("Partner not found with this user ID")
        return value

    def create(self, validated_data):
        partner_user_id = validated_data.pop('partner_user_id')
        account_names = validated_data.pop('accounts', [])  # Get accounts from request
        partner = Partners.objects.get(user_id=partner_user_id)

        # Set initial verification status
        initial_status = json.dumps({
            'status': 'Pending',
            'sub_status': 'Verification in progress'
        })

        contact = Contact.objects.create(
            **validated_data,
            partner=partner,
            created_by=self.context['request'].user,
            email_verification_status=initial_status
        )

        # Add only the accounts provided in the request
        for name in account_names:
            account, _ = Accounts.objects.get_or_create(name=name)
            contact.account.add(account)

        # Trigger email verification in background
        from .tasks import verify_single_email
        verify_single_email.delay(contact.email, contact.id)

        return contact


class ContactListSerializer(serializers.ModelSerializer):
    account_names = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = [
            'id',
            'name',
            'email',
            'mobile',
            'status',
            'account_names',
            'verification_status',
            'created_at'
        ]

    def get_account_names(self, obj):
        return ", ".join([account.name for account in obj.account.all()])

    def get_verification_status(self, obj):
        if not obj.email_verification_status:
            return "Not Verified"
        try:
            verification_data = json.loads(obj.email_verification_status)
            return verification_data.get('status', 'Not Verified')
        except:
            return "Error"