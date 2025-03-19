from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from products_app.models import CustomUser



class Partners(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username if self.user else "No User"


class Accounts(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Account"


class Contact(models.Model):
    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('client', 'Client'),
        ('prospect', 'Prospect'),
    ]

    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    account = models.ManyToManyField(Accounts,blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    partner = models.ForeignKey(Partners, on_delete=models.CASCADE, related_name='contacts',null=True,blank=True)
    additional_data = models.JSONField(default=dict, blank=True)  # For storing extra columns from Excel
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Save the contact first to ensure it has an ID
        super().save(*args, **kwargs)

        # Check if an account name is provided (assuming you want to use the contact's name)
        if self.name:
            # Get or create the account based on the contact's name
            account, created = Accounts.objects.get_or_create(name=self.name)
            # Add the account to the contact's many-to-many relationship
            self.account.add(account)

    def __str__(self):
        return f"{self.name} - {self.email}"


class ContactList(models.Model):
    name = models.CharField(max_length=255)
    contacts = models.ManyToManyField(Contact, through='ContactListMembership')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    @property
    def contact_count(self):
        return self.contacts.count()

    def __str__(self):
        return self.name


class ContactListMembership(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    contact_list = models.ForeignKey(ContactList, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contact', 'contact_list')


class EmailTemplateCategory(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class EmailTemplate(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(EmailTemplateCategory, on_delete=models.CASCADE,null=True,blank=True)
    content = RichTextUploadingField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return self.name


class EmailCampaign(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=255)
    contact_lists = models.ManyToManyField(ContactList)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    custom_content = RichTextUploadingField(null=True, blank=True)
    subject = models.CharField(max_length=255,null=True,blank=True,default="No Subject")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    @property
    def total_contacts(self):
        return sum(cl.contact_count for cl in self.contact_lists.all())

    @property
    def total_contact_lists(self):
        return self.contact_lists.count()

    def __str__(self):
        return self.name