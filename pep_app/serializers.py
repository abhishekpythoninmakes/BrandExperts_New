from rest_framework import serializers
from django.utils import timezone
from .models import (
    EmailTemplateCategory, EmailTemplate, EmailCronJob,
    CronJobExecution, CronJobFrequency, Partners, Contact,
    EmailCampaign, EmailRecipient
)


class EmailTemplateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplateCategory
        fields = ['id', 'name']


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'subject', 'category']


class CronJobExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CronJobExecution
        fields = [
            'id', 'execution_time', 'status',
            'contacts_found', 'emails_sent', 'error_message'
        ]


class EmailCronJobSerializer(serializers.ModelSerializer):
    email_category_name = serializers.CharField(source='email_category.name', read_only=True)
    email_template_name = serializers.CharField(source='email_template.name', read_only=True)
    last_execution = serializers.SerializerMethodField()
    partner_names = serializers.SerializerMethodField()
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)

    class Meta:
        model = EmailCronJob
        fields = [
            'id', 'name', 'email_category', 'email_category_name',
            'email_template', 'email_template_name', 'partners', 'partner_names',
            'frequency', 'frequency_display', 'cron_expression',
            'start_date', 'end_date', 'last_run', 'next_run', 'status',
            'created_at', 'last_execution', 'contact_lists'
        ]
        read_only_fields = ['last_run', 'next_run', 'created_at']

    def get_last_execution(self, obj):
        last_exec = obj.executions.order_by('-execution_time').first()
        if last_exec:
            return CronJobExecutionSerializer(last_exec).data
        return None

    def get_partner_names(self, obj):
        return [partner.user.username if partner.user else f"Partner {partner.id}"
                for partner in obj.partners.all()]

    def validate(self, data):
        # Validate that template belongs to the selected category
        email_template = data.get('email_template')
        email_category = data.get('email_category')

        if email_template and email_category:
            if email_template.category != email_category:
                raise serializers.ValidationError({
                    'email_template': 'Selected template does not belong to the selected category.'
                })

        # Validate end_date is after start_date if provided
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if end_date and start_date and end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })

        return data


class CronJobCreateSerializer(EmailCronJobSerializer):
    """Serializer for creating a new cron job"""

    def create(self, validated_data):
        # Calculate next run time (7:30 AM UTC on the next day)
        today = timezone.now().date()
        next_run_date = today + timezone.timedelta(days=1)
        validated_data['next_run'] = timezone.make_aware(
            timezone.datetime.combine(next_run_date, timezone.datetime.min.time()) +
            timezone.timedelta(hours=7, minutes=30)
        )

        # Create the cron job
        cron_job = EmailCronJob.objects.create(**validated_data)
        return cron_job


class PartnerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Partners
        fields = ['id', 'username', 'email', 'commission', 'mobile_number', 'created_at']


class ContactSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.user.username', read_only=True)

    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'mobile', 'status', 'partner', 'partner_name', 'created_at','email_deliverability']


class EmailCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailCampaign
        fields = ['id', 'name', 'status', 'created_at', 'sent_at', 'total_recipients']


class CampaignAnalyticsSerializer(serializers.Serializer):
    """Serializer for campaign analytics"""
    total_campaigns = serializers.IntegerField()
    total_sent = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    total_opened = serializers.IntegerField()
    total_clicked = serializers.IntegerField()
    total_unsubscribed = serializers.IntegerField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    last_campaign_date = serializers.DateTimeField(allow_null=True)
    upcoming_campaigns = serializers.ListField(
        child=serializers.DictField()
    )
    recent_campaigns = serializers.ListField(
        child=serializers.DictField()
    )
    new_contacts_count = serializers.IntegerField()
    total_contacts = serializers.IntegerField()
    contact_status_distribution = serializers.ListField(
        child=serializers.DictField()
    )
    partner_name = serializers.CharField()
    partner_earnings = serializers.FloatField()
    partner_tasks = serializers.IntegerField()




class CampaignAnalyticsSerializerNew(serializers.Serializer):
    total_campaigns = serializers.IntegerField()
    total_recipients = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sent_campaigns = serializers.IntegerField()
    total_completed_campaigns = serializers.IntegerField()
    total_failed_campaigns = serializers.IntegerField()
    total_queued_campaigns = serializers.IntegerField()  # Added for queued campaigns
    total_opened_emails = serializers.IntegerField()
    total_link_clicked = serializers.IntegerField()
    valid_email_contacts = serializers.IntegerField()  # Added for valid email contacts
    invalid_email_contacts = serializers.IntegerField()  # Added for invalid email contacts


from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from products_app.models import CustomUser
from .models import Partners


class PartnerCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Partners
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'commission', 'mobile_number'
        ]

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        # Extract user data
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        # Create user
        user = CustomUser.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password)
        )

        # Create partner
        partner = Partners.objects.create(user=user, **validated_data)
        return partner


class PartnerUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)

    class Meta:
        model = Partners
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'commission', 'mobile_number', 'created_at'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        # Update user fields if provided
        if user_data:
            user = instance.user
            if 'username' in user_data:
                user.username = user_data['username']
            if 'email' in user_data:
                user.email = user_data['email']
            if 'first_name' in user_data:
                user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                user.last_name = user_data['last_name']
            user.save()

        # Update partner fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class PartnerDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    is_active = serializers.BooleanField(source='user.is_active')
    date_joined = serializers.DateTimeField(source='user.date_joined')

    class Meta:
        model = Partners
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'is_active',
            'date_joined', 'commission', 'mobile_number', 'created_at'
        ]
