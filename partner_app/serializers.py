# serializers.py
import json
from django.utils import timezone
from rest_framework import serializers
from pep_app .models import Contact, Partners, Accounts
from django.contrib.auth import get_user_model
User = get_user_model()
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
        default=[]
    )

    class Meta:
        model = Contact
        fields = [
            'partner_user_id',
            'name',
            'email',
            'mobile',
            'accounts',
            'status',
            'additional_data'
        ]
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True},
            'mobile': {'required': False, 'allow_null': True},
            'status': {'required': False, 'default': 'data'},
            'additional_data': {'required': False, 'default': {}}
        }

    def validate_partner_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            # Check if user has a partner or is a partner themselves
            if not (hasattr(user, 'partner') or user.is_partner):
                raise serializers.ValidationError("User is not associated with a partner")
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with ID {value} does not exist")
        return value

    def validate_accounts(self, value):
        # This will validate the accounts field after the view has potentially converted
        # from string to list
        if isinstance(value, str):
            # In case any string slips through to here, handle it
            return [acc.strip() for acc in value.split(',') if acc.strip()]
        return value

    def create(self, validated_data):
        partner_user_id = validated_data.pop('partner_user_id')
        account_names = validated_data.pop('accounts', [])

        # Get or create accounts - FIXED to handle Accounts model without created_by field
        accounts = []
        for name in account_names:
            try:
                # First try to get existing account
                account = Accounts.objects.get(name=name.strip())
                accounts.append(account)
            except Accounts.DoesNotExist:
                # Create new account without created_by field
                account = Accounts.objects.create(name=name.strip())
                accounts.append(account)

        # Get the partner - handle both direct partner users and users with partner profiles
        try:
            # First try to get the partner directly
            partner = Partners.objects.get(user_id=partner_user_id)
        except Partners.DoesNotExist:
            # If no partner profile exists, check if the user is a partner themselves
            user = User.objects.get(id=partner_user_id)
            if user.is_partner:
                # Create a partner profile for this user
                partner = Partners.objects.create(
                    user=user,
                    created_at=timezone.now()
                )
            else:
                raise serializers.ValidationError(
                    {"partner_user_id": "User is not associated with a partner and cannot be automatically assigned"}
                )

        # Create the contact
        contact = Contact.objects.create(
            partner=partner,
            created_by=self.context['request'].user,
            **validated_data
        )

        # Add accounts to contact
        if accounts:
            contact.account.set(accounts)

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


