from decimal import Decimal

from django import forms
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Partners


class PartnerAdminForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'vTextField'})
    )
    mobile_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'vTextField',
            'placeholder': 'Auto-generated if left blank'
        }),
        required=False,
        initial='Temp@1234',
        help_text='Leave blank to keep existing password when editing'
    )
    commission = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'vTextField'}),
        required=False,
    )

    class Meta:
        model = Partners
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.user:
            # Populate fields for existing partner
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['mobile_number'].initial = self.instance.mobile_number
            self.fields['password'].widget.attrs.update({
                'placeholder': 'Leave blank to keep current password'
            })

    # Remove the clean_email method that was raising validation errors
    # We'll handle existing users in the save method instead

    def clean_commission(self):
        commission = self.cleaned_data.get('commission')
        return commission if commission is not None else Decimal('0.00')

    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data.get('password') or 'Temp@1234'
        mobile_number = self.cleaned_data['mobile_number']

        user_data = {
            'username': email,  # Username is set to email
            'email': email,
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'is_partner': True
        }

        # Check if we're updating an existing partner or creating a new one
        is_new_partner = not self.instance.pk

        # Find existing user by email
        existing_user = CustomUser.objects.filter(email=email).first()

        if existing_user:
            # If user exists, update their details
            for field, value in user_data.items():
                setattr(existing_user, field, value)

            # Only set password if explicitly provided and this is not an update
            if self.cleaned_data.get('password') and is_new_partner:
                existing_user.set_password(password)

            # Ensure they have partner permissions
            existing_user.is_partner = True
            existing_user.is_staff = True
            existing_user.save()

            user = existing_user
        else:
            # Create a new user
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_partner=True,
                is_staff=True
            )

        # Save partner instance
        partner = super().save(commit=False)
        partner.user = user
        partner.mobile_number = mobile_number

        if commit:
            partner.save()

        # Store credentials if this is a new partner record
        self.new_user_email = email
        # Only store password for new users we created (not existing ones)
        self.new_user_password = password if not existing_user else None

        return partner