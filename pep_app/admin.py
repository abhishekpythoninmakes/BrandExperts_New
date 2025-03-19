import threading
from .admin_forms import PartnerAdminForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.utils.html import format_html
from django.core.mail import send_mail

from .models import *

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
