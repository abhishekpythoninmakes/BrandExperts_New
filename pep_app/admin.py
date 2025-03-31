import threading
from django.urls import path
from .admin_forms import PartnerAdminForm
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from .tasks import *
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.forms.widgets import DateInput
from django.utils.html import format_html
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.db import transaction
from django.contrib.auth.models import  Group, Permission
import pandas as pd
from .models import *
from django_json_widget.widgets import JSONEditorWidget
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django import forms
from dateutil.relativedelta import relativedelta

# Task



# Define choices for the period unit and end date mode
PERIOD_UNIT_CHOICES = (
    ('days', 'Days'),
    ('weeks', 'Weeks'),
    ('months', 'Months'),
    ('years', 'Years'),
)
END_DATE_CHOICES = (
    ('manual', 'Manual End Date'),
    ('period', 'Period Based End Date'),
)

class TasksAdminForm(forms.ModelForm):
    # Choice field to select the end date method
    end_date_choice = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=END_DATE_CHOICES,
        label="Select End Date Mode"
    )
    # Extra fields for period-based entry
    period_value = forms.IntegerField(
        required=False,
        label="Period Value",
        help_text="Enter period value if period mode is selected."
    )
    period_unit = forms.ChoiceField(
        required=False,
        choices=PERIOD_UNIT_CHOICES,
        label="Period Unit",
        help_text="Select unit for period (days, weeks, months, years)."
    )
    # Field for manual end date using a single date picker widget
    manual_end_date = forms.DateField(
        required=False,
        label="Manual End Date",
        widget=DateInput(attrs={'type': 'date'}),
        help_text="Select manual end date if manual mode is selected."
    )

    class Meta:
        model = Tasks
        fields = [
            'task_name',
            'description',
            'start_date',
            'goal',
            'email',
            'commission_percentage',
            'bonus_percentage',
            'partners_list',
            'end_date_choice',
            'manual_end_date',
            'period_value',
            'period_unit'
        ]
        widgets = {
            'partners_list': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing an instance, default to manual mode and populate manual_end_date.
        if self.instance and self.instance.pk:
            self.fields['end_date_choice'].initial = 'manual'
            self.fields['manual_end_date'].initial = self.instance.end_date

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('end_date_choice')
        start_date = cleaned_data.get('start_date')
        manual_end_date = cleaned_data.get('manual_end_date')
        period_value = cleaned_data.get('period_value')
        period_unit = cleaned_data.get('period_unit')

        if not start_date:
            raise forms.ValidationError("Start date is required.")

        if mode == 'manual':
            if not manual_end_date:
                raise forms.ValidationError("Manual end date is required in manual mode.")
            # Clear period fields
            cleaned_data['period_value'] = None
            cleaned_data['period_unit'] = None
            cleaned_data['end_date'] = manual_end_date
        elif mode == 'period':
            if not (period_value and period_unit):
                raise forms.ValidationError("Both period value and period unit are required in period mode.")
            # Calculate the end_date based on period unit and value
            if period_unit == 'days':
                cleaned_data['end_date'] = start_date + relativedelta(days=period_value)
            elif period_unit == 'weeks':
                cleaned_data['end_date'] = start_date + relativedelta(weeks=period_value)
            elif period_unit == 'months':
                cleaned_data['end_date'] = start_date + relativedelta(months=period_value)
            elif period_unit == 'years':
                cleaned_data['end_date'] = start_date + relativedelta(years=period_value)
            # Clear manual field
            cleaned_data['manual_end_date'] = None
        else:
            raise forms.ValidationError("Please choose an end date mode.")

        return cleaned_data

    class Media:
        js = ('admin/js/tasks_admin.js',)

class TasksAdmin(admin.ModelAdmin):
    form = TasksAdminForm
    list_display = ('task_name', 'start_date', 'end_date', 'goal', 'created_date', 'created_by')
    readonly_fields = ('created_date', 'created_by')
    filter_horizontal = ('partners_list',)

    def save_model(self, request, obj, form, change):
        # Set the created_by field to the current user for new tasks.
        if not obj.pk:
            obj.created_by = request.user
        # Use the computed end_date from the form's clean() method.
        if 'end_date' in form.cleaned_data:
            obj.end_date = form.cleaned_data['end_date']
        super().save_model(request, obj, form, change)
    fieldsets = (
        ('Task Information', {
            'fields': ('task_name', 'description', 'start_date')
        }),
        ('Performance Metrics', {
            'fields': ('goal', 'commission_percentage', 'bonus_percentage')
        }),
        ('Contact & Assignment', {
            'fields': ('email', 'partners_list')
        }),
        ('Duration Configuration', {
            'fields': ('end_date_choice', 'manual_end_date', 'period_value', 'period_unit')
        }),
    )

admin.site.register(Tasks, TasksAdmin)









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

                    if 'partner' in df.columns:
                        partner_email = str(row.get('partner', '')).strip()
                        if partner_email:
                            try:
                                partner_inst = Partners.objects.get(user__email=partner_email)
                            except Partners.DoesNotExist:
                                partner_inst = None
                        else:
                            partner_inst = None
                    else:
                        # Fallback: assign partner from request user if available.
                        partner_inst = partner_instance

                    # Create/update contact
                    contact, created = Contact.objects.update_or_create(
                        email=email,
                        defaults={
                            'name': email.split('@')[0] if '@' in email else email,
                            'mobile': mobile,
                            'additional_data': additional_data,
                            'partner': partner_inst , # Assign partner if exists
                            'status': 'data',
                            'created_by': request.user if request.user.is_authenticated else None
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


# Function to shorten permission names
def short_permission_name(permission_name):
    """Shorten permission labels for better readability."""
    parts = permission_name.split(" ")
    if len(parts) > 2:
        return f"{parts[0]} {parts[-1]}"  # Show only first and last word
    return permission_name


# Custom GroupAdmin to show users and their permissions
class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "user_count", "users_list", "group_permissions")
    search_fields = ("name",)

    def user_count(self, obj):
        """Count users in the group."""
        return obj.user_set.count()

    def users_list(self, obj):
        """List all users under the group."""
        users = obj.user_set.all().values_list("username", flat=True)
        return ", ".join(users) if users else "-"

    def group_permissions(self, obj):
        """Show compressed list of group permissions."""
        permissions = obj.permissions.all().values_list("name", flat=True)
        short_perms = [short_permission_name(perm) for perm in permissions]
        return mark_safe("<br>".join(short_perms) if short_perms else "-")

    user_count.short_description = "Total Users"
    users_list.short_description = "Users in Group"
    group_permissions.short_description = "Permissions (Shortened)"


# Unregister default Group admin and register our custom version
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)




# Custom admin form for ContactList
class ContactListAdminForm(forms.ModelForm):
    IMPORT_OR_MANUAL_CHOICES = (
        ('import', 'Import Contacts'),
        ('manual', 'Manually Add Contacts'),
    )
    # Extra field to determine which input to show
    import_or_manual = forms.ChoiceField(
        choices=IMPORT_OR_MANUAL_CHOICES,
        widget=forms.RadioSelect,
        label="Contact Addition Method",
        initial='manual'
    )

    class Meta:
        model = ContactList
        # Include our extra field along with the model fields.
        fields = ['name', 'import_or_manual', 'excel_file', 'contacts_new']

    def __init__(self, *args, **kwargs):
        super(ContactListAdminForm, self).__init__(*args, **kwargs)
        # Make both excel_file and contacts_new optional here;
        # we'll enforce required validation based on the chosen method.
        self.fields['excel_file'].required = False
        self.fields['contacts_new'].required = False

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('import_or_manual')
        excel_file = cleaned_data.get('excel_file')
        contacts = cleaned_data.get('contacts_new')
        if method == 'import':
            if not excel_file:
                self.add_error('excel_file', "Please upload an Excel file.")
        elif method == 'manual':
            if not contacts:
                self.add_error('contacts_new', "Please select at least one contact.")
        return cleaned_data

class ContactListAdmin(admin.ModelAdmin):
    form = ContactListAdminForm
    list_display = ['id', 'name', 'created_at', 'total_contacts', 'custom_actions']  # Renamed to custom_actions
    list_display_links = ['id', 'name']
    search_fields = ['name']
    list_filter = ['created_at']
    readonly_fields = ['total_contacts']

    class Media:
        js = ('admin/js/contact_list_admin.js',)

    def total_contacts(self, obj):
        """Display the total number of contacts in the ContactList."""
        return obj.contacts_new.count()

    total_contacts.short_description = 'Total Contacts'

    def custom_actions(self, obj):  # Renamed to custom_actions
        """Custom action buttons for the ContactList."""
        return format_html(
            '<a class="button" href="{}">View Contacts</a>&nbsp;'
            '<a class="button" href="{}">Edit</a>',
            f'/admin/pep_app/contactlist/{obj.id}/change/',
            f'/admin/pep_app/contactlist/{obj.id}/change/',
        )

    custom_actions.short_description = 'Actions'
    custom_actions.allow_tags = True

    def save_model(self, request, obj, form, change):
        """
        Save the ContactList instance. Then, if the import method was chosen,
        process the uploaded Excel file, create or update Contacts, and pass
        the ContactList ID and Contact IDs to a Celery task for adding to the M2M field.
        """
        # Save the ContactList instance first (basic fields only)
        obj.name = form.cleaned_data['name']
        obj.save()  # Save manually to avoid form.save() clearing M2M

        # If "Import Contacts" was selected and an Excel file is present, process it.
        if form.cleaned_data.get('import_or_manual') == 'import' and form.cleaned_data.get('excel_file'):
            excel_file = form.cleaned_data.get('excel_file')
            try:
                df = pd.read_excel(excel_file)
                df.columns = [str(col).strip().lower() for col in df.columns]

                # Define required and optional columns
                required_columns = {'account', 'email', 'mobile'}
                optional_columns = {'marriage', 'address'}

                # Validate required columns
                if not required_columns.issubset(df.columns):
                    missing = required_columns - set(df.columns)
                    messages.error(request, f"Missing required columns: {', '.join(missing)}")
                    return

                # Determine partner instance if available from the request user.
                partner_instance = None
                if request.user.is_authenticated and hasattr(request.user, 'is_partner') and request.user.is_partner:
                    try:
                        partner_instance = Partners.objects.get(user=request.user)
                    except Partners.DoesNotExist:
                        partner_instance = None

                created_count = 0
                contact_ids = []  # List to hold contact IDs for Celery task

                for _, row in df.iterrows():
                    account_name = str(row.get('account', '')).strip()
                    email = str(row.get('email', '')).strip()
                    mobile = str(row.get('mobile', '')).strip()
                    if not account_name or not email:
                        continue

                    # Prepare additional data from optional columns.
                    additional_data = {}
                    for col in optional_columns:
                        if col in df.columns:
                            value = row.get(col)
                            if pd.notna(value):
                                additional_data[col] = str(value).strip()

                    # Get or create the account.
                    account, _ = Accounts.objects.get_or_create(name=account_name)

                    # Determine partner for the contact.
                    if 'partner' in df.columns:
                        partner_email = str(row.get('partner', '')).strip()
                        if partner_email:
                            try:
                                partner_inst = Partners.objects.get(user__email=partner_email)
                            except Partners.DoesNotExist:
                                partner_inst = None
                        else:
                            partner_inst = None
                    else:
                        partner_inst = partner_instance

                    # Create or update the contact.
                    contact, created = Contact.objects.update_or_create(
                        email=email,
                        defaults={
                            'name': email.split('@')[0] if '@' in email else email,
                            'mobile': mobile,
                            'additional_data': additional_data,
                            'partner': partner_inst,
                            'status': 'data',
                            'created_by': request.user if request.user.is_authenticated else None,
                        }
                    )

                    # Ensure the account relationship exists.
                    if account not in contact.account.all():
                        contact.account.add(account)

                    # Add the contact ID to the list for the Celery task
                    contact_ids.append(contact.id)
                    if created:
                        created_count += 1

                # Debug: Print contacts to be added
                print("Contacts to add:", contact_ids)

                # Pass the ContactList ID and Contact IDs to the Celery task
                add_contacts_to_contactlist.delay(obj.id, contact_ids)

                messages.success(request, f"Successfully imported {created_count} new contacts! Contacts will be added to the list shortly.")
            except Exception as e:
                messages.error(request, f"Error importing contacts: {str(e)}")

    def response_add(self, request, obj, post_url_continue=None):
        """
        Override the response after adding a ContactList instance.
        """
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Return a JSON response for AJAX requests
            return JsonResponse({
                'success': True,
                'message': 'ContactList created successfully!',
                'redirect_url': '/admin/pep_app/contactlist/'  # Redirect to the contact list page
            })
        else:
            # Default behavior for non-AJAX requests
            return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """
        Override the response after changing a ContactList instance.
        """
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Return a JSON response for AJAX requests
            return JsonResponse({
                'success': True,
                'message': 'ContactList updated successfully!',
                'redirect_url': '/admin/pep_app/contactlist/'  # Redirect to the contact list page
            })
        else:
            # Default behavior for non-AJAX requests
            return super().response_change(request, obj)

admin.site.register(ContactList, ContactListAdmin)



class EmailTemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'created_by']
    search_fields = ['name', 'created_by__username']
    ordering = ['-created_at']
    list_filter = ['created_by']
    exclude = ('created_by',)  # Exclude this field from the admin form

    def save_model(self, request, obj, form, change):
        # Set the created_by field to the current logged-in user on creation.
        if not change:
            obj.created_by = request.user
        obj.save()

admin.site.register(EmailTemplateCategory, EmailTemplateCategoryAdmin)



class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at', 'created_by']
    search_fields = ['name', 'category__name', 'created_by__username']
    list_filter = ['category', 'created_by']
    ordering = ['-created_at']
    exclude = ('created_by',)  # Auto-set created_by in save_model

    def save_model(self, request, obj, form, change):
        # On creation, assign the current logged-in user to created_by.
        if not change:
            obj.created_by = request.user
        obj.save()

admin.site.register(EmailTemplate, EmailTemplateAdmin)


admin.site.register(Placeholder)


class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status_badge', 'created_at', 'campaign_actions')
    list_filter = ('status', 'created_by')
    search_fields = ('name', 'subject', 'sender_name')
    readonly_fields = ('created_at', 'created_by')
    filter_horizontal = ('contact_lists',)
    ordering = ('-created_at',)

    def get_queryset(self, request):
        # Disable caching for the queryset
        return super().get_queryset(request).select_related()

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sender_name', 'status')
        }),
        ('Campaign Content', {
            'fields': ('subject', 'template', 'custom_content'),
            'classes': ('wide', 'collapse')
        }),
        ('Recipients', {
            'fields': ('contact_lists',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def campaign_actions(self, obj):
        """Generate action buttons for the changelist based on campaign status."""
        if obj.status == 'draft':
            return format_html(
                '<a class="button" href="{}" style="background: #4CAF50; color: white;">Send Now</a>',
                reverse('admin:pep_app_emailcampaign_send', args=[obj.id])  # Updated URL name
            )
        elif obj.status == 'sent':
            return format_html(
                '<button class="button" style="background: #9E9E9E; color: white; padding: 5px 10px; cursor: not-allowed;" disabled>Sent</button>'
            )
        elif obj.status == 'pending':
            return format_html(
                '<button class="button" style="background: #FF9800; color: white; padding: 5px 10px; cursor: not-allowed;" disabled>Pending</button>'
            )
        elif obj.status == 'cancelled':
            return format_html(
                '<button class="button" style="background: #F44336; color: white; padding: 5px 10px; cursor: not-allowed;" disabled>Cancelled</button>'
            )
        return ''

    campaign_actions.short_description = 'Actions'
    campaign_actions.allow_tags = True

    def status_badge(self, obj):
        """Display the campaign status with a colored badge."""
        status_colors = {
            'draft': 'gray',
            'pending': 'orange',
            'sent': 'green',
            'cancelled': 'red'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            status_colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def get_urls(self):
        """Add custom URLs for the admin interface."""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/send/',
                self.admin_site.admin_view(self.send_campaign),
                name='pep_app_emailcampaign_send'  # Updated to follow convention
            ),
        ]
        return custom_urls + urls

    def send_campaign(self, request, object_id):
        """Handle the 'Send Now' action by triggering a Celery task."""
        try:
            campaign = EmailCampaign.objects.get(id=object_id)
            if campaign.status != 'draft':
                messages.error(request, 'Only draft campaigns can be sent.')
                return HttpResponseRedirect("../")

            # Trigger the Celery task
            send_email_campaign.delay(campaign.id)
            campaign.status = 'pending'
            campaign.save()

            messages.success(request, 'Campaign is being sent in the background.')
            return HttpResponseRedirect("../")
        except EmailCampaign.DoesNotExist:
            messages.error(request, 'Campaign not found.')
            return HttpResponseRedirect("../")

    def save_model(self, request, obj, form, change):
        """Set the created_by field when creating a new campaign."""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }

admin.site.register(EmailCampaign, EmailCampaignAdmin)



admin.site.register(EmailRecipient)