from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Partners



@receiver(post_save, sender=Partners)
def add_partner_to_group(sender, instance, created, **kwargs):
    if instance.user:
        staff_group, _ = Group.objects.get_or_create(name="Partner Group")
        instance.user.groups.add(staff_group)  # Add user to group