# serializers.py
from rest_framework import serializers
from pep_app .models import Contact, Partners, Accounts


class ContactCreateSerializer(serializers.ModelSerializer):
    partner_user_id = serializers.IntegerField(write_only=True)
    accounts = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Contact
        fields = [
            'partner_user_id',
            'name',
            'email',
            'mobile',
            'accounts',
            'additional_data',
            'status'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'mobile': {'required': True},
            'status': {'required': False},
            'additional_data': {'required': False}
        }

    def validate_partner_user_id(self, value):
        try:
            Partners.objects.get(user_id=value)
        except Partners.DoesNotExist:
            raise serializers.ValidationError("Partner not found with this user ID")
        return value

    def create(self, validated_data):
        partner_user_id = validated_data.pop('partner_user_id')
        account_names = validated_data.pop('accounts', [])
        partner = Partners.objects.get(user_id=partner_user_id)

        contact = Contact.objects.create(
            **validated_data,
            partner=partner,
            created_by=self.context['request'].user
        )

        # Add accounts from request
        for name in account_names:
            account, _ = Accounts.objects.get_or_create(name=name)
            contact.account.add(account)

        return contact