from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from products_app.models import CustomUser
from django.urls import reverse
from django.conf import settings
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

STATUS_CHOICES = [
    ('data', 'Data'),
    ('lead', 'Lead'),
    ('client', 'Client'),
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

    def save(self, *args, **kwargs):
        # Save the contact first to ensure it has an ID
        super().save(*args, **kwargs)
        # Trigger task evaluation after save
        from .tasks import evaluate_partner_tasks  # Avoid circular import
        evaluate_partner_tasks.delay(self.id)



    def __str__(self):
        return f"{self.name} - {self.email}"


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
    content = RichTextUploadingField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)

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
    value = models.CharField(max_length=255)

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
    custom_content = RichTextUploadingField(null=True, blank=True)
    subject = models.CharField(max_length=255,null=True,blank=True,default="No Subject")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

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
        return settings.DOMAIN + reverse('track_email_open', args=[str(self.tracking_id)])