from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from products_app.models import CustomUser
from django.urls import reverse
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import datetime, time
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

STATUS_CHOICES = [
    ('data', 'Data'),
    ('lead', 'Lead'),
    ('client', 'Client'),
    ('unsubscribed','Unsubscribed'),
    ('prospect', 'Prospect'),
]




class Partners(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    commission = models.DecimalField(max_digits=10,decimal_places=2,default=0.00,null=False,blank=False)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username if self.user else "No User"

    def get_commission(self):
        return self.commission if self.commission is not None else 0.00



class Tasks(models.Model):
    task_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    # New fields
    goal = models.PositiveIntegerField(default=0, help_text="Target goal for this task")
    email = models.EmailField(blank=True, null=True, help_text="Contact email for the task")
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission percentage for this task"
    )
    bonus_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Bonus percentage for task completion"
    )
    partners_list = models.ManyToManyField(
        Partners,
        related_name='tasks',
        blank=True,
        help_text="Select partners assigned to this task"
    )

    def __str__(self):
        return self.task_name






class Accounts(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='data',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Account"


class Contact(models.Model):

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='contact')
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    account = models.ManyToManyField(Accounts,blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='data')
    partner = models.ForeignKey(Partners, on_delete=models.CASCADE, related_name='contacts',null=True,blank=True)
    additional_data = models.JSONField(default=dict, blank=True)  # For storing extra columns from Excel
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='created_contacts')
    email_deliverability = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Stores the verification result from Clearout API as a JSON string"
    )
    def save(self, *args, **kwargs):
        # Save the contact first to ensure it has an ID
        super().save(*args, **kwargs)
        # Trigger task evaluation after save
        from .tasks import evaluate_partner_tasks  # Avoid circular import
        evaluate_partner_tasks.delay(self.id)

    def __str__(self):
        return f"{self.name} - {self.email}"

    def get_verification_data(self):
        """Helper method to get verification data as a dictionary"""
        if not self.email_verification_status:
            return {}
        try:
            import json
            return json.loads(self.email_verification_status)
        except:
            return {}

    def set_verification_data(self, data):
        """Helper method to set verification data from a dictionary"""
        import json
        self.email_verification_status = json.dumps(data)


class ContactList(models.Model):
    name = models.CharField(max_length=255)
    contacts_new = models.ManyToManyField(Contact, blank=True)
    excel_file = models.FileField(upload_to='contact_lists', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    @property
    def contact_count(self):
        return self.contacts.count()

    def __str__(self):
        return self.name




class EmailTemplateCategory(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class EmailTemplate(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(EmailTemplateCategory, on_delete=models.CASCADE,null=True,blank=True)
    subject = models.CharField(max_length=255,null=True,blank=True)
    content = RichTextUploadingField(null=True, blank=True,config_name='default')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    selected = models.BooleanField(default=False,null=True,blank=True)

    def get_email_content(self):
        if self.custom_content:
            content = self.custom_content
        elif self.template:
            content = self.template.content
        else:
            content = ""
        return content

    def get_email_subject(self):
        return self.subject or (self.template.subject if self.template else "No Subject")
    def __str__(self):
        return self.name



class Placeholder(models.Model):
    key = models.CharField(max_length=255, unique=True)


    def __str__(self):
        return self.key





class EmailCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=255,null=True,blank=True)
    contact_lists = models.ManyToManyField(ContactList)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    custom_content = RichTextUploadingField(null=True, blank=True,config_name='default')
    subject = models.CharField(max_length=255,null=True,blank=True,default="No Subject")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    selected = models.BooleanField(default=False,null=True,blank=True)

    def get_email_content(self):
        if self.custom_content:
            content = self.custom_content
        elif self.template:
            content = self.template.content
        else:
            content = ""
        return content


    def get_email_subject(self):
        return self.subject or (self.template.subject if self.template else "No Subject")

    def __str__(self):
        return self.name


class EmailRecipient(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('link','Link Clicked'),
        ('unsubscribed','Unsubscribed'),
        ('opened', 'Opened'),
        ('failed', 'Failed'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def tracking_pixel_url(self):
        from django.urls import reverse
        from django.conf import settings

        # Build the absolute URL with a cache-busting parameter
        base_url = settings.DOMAIN.rstrip('/') + reverse('track_email_open', args=[str(self.tracking_id)])

        # Add a timestamp parameter to prevent caching
        import time
        cache_buster = int(time.time())
        return f"{base_url}?t={cache_buster}"

    def __str__(self):
        return f"{self.contact.name or self.contact.email or 'Unknown Contact'} - {self.campaign.name} status: - {self.status}"


class EmailCampaignAnalytics(models.Model):
    """
    This is a dummy model used to create an admin interface
    for displaying email campaign analytics.
    """
    class Meta:
        verbose_name = 'Email Campaign Analytics'
        verbose_name_plural = 'Email Campaign Analytics'




############################## SETTING CRON JOB ##############################


class CronJobFrequency(models.TextChoices):
    MINUTES = 'minutes', 'Minutes'
    HOURLY = 'hourly', 'Hourly'
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'
    SPECIFIC_DATE = 'specific_date', 'Specific Date'


class CronJobStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class EmailCronJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Name of the cron job for identification")
    email_template = models.ForeignKey(
        EmailTemplate,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='cron_jobs',
        help_text="Select the email template to use for campaigns triggered by this cron job"
    )
    email_category = models.ForeignKey(
        EmailTemplateCategory,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='cron_jobs',
        help_text="Select the email category"
    )
    # Partner field is optional - will be determined automatically based on contacts
    partners = models.ManyToManyField(
        Partners,
        related_name='email_cron_jobs',
        blank=True,
        help_text="Partners associated with this cron job (automatically determined from contacts)"
    )
    contact_lists = models.ManyToManyField(
        ContactList,
        related_name='email_cron_jobs',
        blank=True,
        help_text="Contact lists to include in this cron job"
    )
    frequency = models.CharField(
        max_length=20,
        choices=CronJobFrequency.choices,
        default=CronJobFrequency.DAILY,
        help_text="Frequency of the cron job execution"
    )
    # For more complex schedules, we can use a cron expression
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Custom cron expression (e.g., '0 7 * * *' for daily at 7 AM)"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date in UTC. Cron job will start checking for contacts from this date."
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date in UTC. Cron job will stop running after this date."
    )
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CronJobStatus.choices,
        default=CronJobStatus.ACTIVE,
        help_text="Current status of the cron job"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cron_jobs',
        help_text="User who created the cron job"
    )
    campaigns = models.ManyToManyField(EmailCampaign, related_name='cron_jobs', blank=True)
    processed_contacts = models.ManyToManyField(
        Contact,
        related_name='processed_by_cron_jobs',
        blank=True,
        help_text="Contacts that have already been processed by this cron job"
    )

    class Meta:
        verbose_name = "Email Cron Job"
        verbose_name_plural = "Email Cron Jobs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

    def calculate_next_run(self):
        """Calculate the next run time based on frequency and last run"""
        from datetime import timedelta

        now = timezone.now()

        if not self.last_run:
            # First run - schedule for tomorrow at 7:30 AM UTC
            tomorrow = now.date() + timedelta(days=1)
            return timezone.make_aware(datetime.combine(tomorrow, time(7, 30)))

        if self.frequency == CronJobFrequency.MINUTES:
            return self.last_run + timedelta(minutes=15)  # Default to 15 minutes
        elif self.frequency == CronJobFrequency.HOURLY:
            return self.last_run + timedelta(hours=1)
        elif self.frequency == CronJobFrequency.DAILY:
            return self.last_run + timedelta(days=1)
        elif self.frequency == CronJobFrequency.WEEKLY:
            return self.last_run + timedelta(days=7)
        elif self.frequency == CronJobFrequency.MONTHLY:
            # Approximate a month as 30 days
            return self.last_run + timedelta(days=30)
        elif self.frequency == CronJobFrequency.YEARLY:
            # Approximate a year as 365 days
            return self.last_run + timedelta(days=365)
        else:
            # Default to daily
            return self.last_run + timedelta(days=1)

    def save(self, *args, **kwargs):
        # Calculate next run time if not set
        if not self.next_run:
            now = timezone.now()
            tomorrow = now.date() + timezone.timedelta(days=1)
            self.next_run = timezone.make_aware(
                datetime.combine(tomorrow, time(7, 30))
            )

        super().save(*args, **kwargs)


class CronJobExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cron_job = models.ForeignKey(
        EmailCronJob,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cron_executions'
    )
    execution_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('no_contacts', 'No Contacts Found')
        ],
        default='success'
    )
    contacts_found = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    new_contacts_processed = models.ManyToManyField(
        Contact,
        related_name='processed_in_executions',
        blank=True,
        help_text="New contacts processed in this execution"
    )

    class Meta:
        ordering = ['-execution_time']

    def __str__(self):
        return f"Execution of {self.cron_job.name} at {self.execution_time}"