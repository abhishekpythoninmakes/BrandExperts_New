# admin_forms.py
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

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exclude(
            pk=self.instance.user.pk if self.instance.user else None
        ).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

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

        if self.instance.pk:
            # Update existing user
            user = self.instance.user
            for field, value in user_data.items():
                setattr(user, field, value)
            if password != 'Temp@1234':  # Only update password if changed
                user.set_password(password)
            user.save()
        else:
            # Create new user
            user = CustomUser.objects.create_user(
                username=email,  # Username is set to email
                email=email,
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_partner=True
            )

        # Save partner instance
        partner = super().save(commit=False)
        partner.user = user
        partner.mobile_number = mobile_number

        if commit:
            partner.save()

        # Store credentials for email notification
        self.new_user_email = email
        self.new_user_password = password if not self.instance.pk else None

        return partner