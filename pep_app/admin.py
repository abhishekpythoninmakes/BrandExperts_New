import threading
from django.urls import path
from .admin_forms import PartnerAdminForm
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.core.mail import send_mail
from django.http import JsonResponse
from django.db import transaction
import pandas as pd
from .models import *
from django_json_widget.widgets import JSONEditorWidget
from django.shortcuts import render, redirect

class EmailThread(threading.Thread):
    def __init__(self, subject, message, recipient):
        self.subject = subject
        self.message = message
        self.recipient = recipient
        super().__init__()

    def run(self):
        send_mail(
            self.subject,
            self.message,
            'hello@brandexperts.ae',
            [self.recipient],
            fail_silently=False,
        )

@admin.register(Partners)
class PartnersAdmin(admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ('user_profile', 'commission_display', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('User Information', {
            'fields': ('first_name', 'last_name', 'email', 'mobile_number', 'password'),
            'classes': ('wide', 'extrapretty')
        }),
        ('Partner Details', {
            'fields': ('commission',),
            'classes': ('wide',)
        }),
    )

    def user_profile(self, obj):
        return format_html(
            '<strong>{} {}</strong><br>{}',
            obj.user.first_name,
            obj.user.last_name,
            obj.user.username
        )
    user_profile.short_description = 'User Profile'

    def commission_display(self, obj):
        commission = obj.commission or 0  # Handle None values
        return format_html('<span style="color: #28a745;">{} AED</span>', commission)
    commission_display.short_description = 'Commission'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change and form.new_user_password:
            subject = "Your Account Credentials"
            message = (
                f"Dear {obj.user.first_name},\n\n"
                "Your BrandExperts partner account has been created successfully.\n\n"
                f"Username: {form.new_user_email}\n"
                f"Temporary Password: {form.new_user_password}\n\n"
                "Please log in and change your password immediately.\n"
                "Best regards,\nBrandExperts Team"
            )

            EmailThread(subject, message, form.new_user_email).start()
            self.message_user(request,
                              format_html(
                                  'Partner created successfully! Credentials sent to <b>{}</b>.',
                                  form.new_user_email
                              ), messages.SUCCESS)
        else:
            self.message_user(request, 'Partner details updated successfully.', messages.SUCCESS)





@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")  # Display name and created date
    search_fields = ("name",)  # Add search functionality by name
    list_filter = ("created_at",)  # Filter by creation date
    ordering = ("-created_at",)  # Show recent accounts first
    date_hierarchy = "created_at"  # Add a date navigation filter


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    # List view configuration
    list_display = (
        'name',
        'email',
        'mobile',
        'partner_name',
        'status',
        'created_at',
        'account_list'
    )

    # Filters and search
    list_filter = ('status', 'partner', 'created_at')
    search_fields = ('name', 'email', 'mobile')
    date_hierarchy = 'created_at'

    # Form configuration
    filter_horizontal = ('account',)  # Better many-to-many widget
    readonly_fields = ('created_at',)

    # JSON field widget
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    # Custom methods for list display
    change_list_template = 'admin/pep_app/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-contacts/',
                 self.admin_site.admin_view(self.import_contacts_view),
                 name='pep_app_contact_import'),
        ]
        return custom_urls + urls

    def import_contacts_view(self, request):
        if request.method == 'POST':
            try:
                excel_file = request.FILES['excel_file']

                # Read and process Excel
                df = pd.read_excel(excel_file)
                df.columns = [str(col).strip().lower() for col in df.columns]

                # Define required and optional columns
                required_columns = {'account', 'email', 'mobile'}
                optional_columns = {'marriage', 'address'}  # Will be stored in additional_data

                # Validate required columns
                if not required_columns.issubset(df.columns):
                    missing = required_columns - set(df.columns)
                    return JsonResponse(
                        {'success': False, 'message': f"Missing required columns: {', '.join(missing)}"})

                # Get partner instance if current user is a partner
                partner_instance = None
                if request.user.is_authenticated and request.user.is_partner:
                    try:
                        partner_instance = Partners.objects.get(user=request.user)
                    except Partners.DoesNotExist:
                        pass

                # Process rows
                for _, row in df.iterrows():
                    # Convert all values to strings and strip whitespace
                    account_name = str(row.get('account', '')).strip()
                    email = str(row.get('email', '')).strip()
                    mobile = str(row.get('mobile', '')).strip()

                    # Skip if required fields are missing
                    if not account_name or not email:
                        continue

                    # Prepare additional data
                    additional_data = {}
                    for col in optional_columns:
                        if col in df.columns:
                            value = row.get(col)
                            if pd.notna(value):  # Only store if value exists
                                additional_data[col] = str(value).strip()

                    # Get or create account
                    account, _ = Accounts.objects.get_or_create(name=account_name)

                    # Create/update contact
                    contact, created = Contact.objects.update_or_create(
                        email=email,
                        defaults={
                            'name': email.split('@')[0] if '@' in email else email,
                            'mobile': mobile,
                            'additional_data': additional_data,
                            'partner': partner_instance  # Assign partner if exists
                        }
                    )

                    # Add account relationship if not exists
                    if account not in contact.account.all():
                        contact.account.add(account)

                return JsonResponse({
                    'success': True,
                    'message': f"Successfully imported {len(df)} contacts!"
                })

            except Exception as e:
                return JsonResponse({'success': False, 'message': f"Error importing contacts: {str(e)}"})

        # Render the form for GET requests
        return render(request, 'admin/pep_app/import_contacts.html', {
            'title': 'Import Contacts',
            'opts': self.model._meta,
            'has_permission': request.user.is_active and request.user.is_staff,
        })

    def partner_name(self, obj):
        return obj.partner.user.username if obj.partner and obj.partner.user else '-'

    partner_name.short_description = 'Partner'

    def account_list(self, obj):
        return ", ".join([a.name for a in obj.account.all()])

    account_list.short_description = 'Accounts'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        account_name = form.cleaned_data.get('account_name')
        if account_name:
            account, _ = Accounts.objects.get_or_create(name=account_name)
            obj.account.add(account)