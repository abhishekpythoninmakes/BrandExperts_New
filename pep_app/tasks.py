# tasks.py
import os
from django.core.exceptions import ValidationError
from decimal import Decimal
from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import Contact, Partners, Tasks , ContactList , Accounts
import pandas as pd
from products_app.models import CustomUser

@shared_task
def evaluate_partner_tasks(contact_id):
    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return

    partner = contact.partner
    if not partner or not partner.user:
        return

    current_date = timezone.now().date()

    # Get partner's commission safely
    partner_commission = partner.get_commission()

    # Get tasks ordered by highest commission first
    tasks = partner.tasks.filter(
        start_date__lte=current_date,
        end_date__gte=current_date
    ).order_by('-commission_percentage')

    for task in tasks:
        # Skip if task commission not higher than partner's current commission
        if task.commission_percentage <= partner_commission:
            continue

        # Count contacts within task period
        contacts_count = Contact.objects.filter(
            partner=partner,
            created_at__date__range=(task.start_date, task.end_date)
        ).count()

        goal = task.goal
        if goal == 0:  # Prevent division by zero
            progress = 0
        else:
            progress = (contacts_count / goal) * 100

        # Check goal achievement
        if contacts_count >= goal:
            # Update partner commission
            partner.commission = task.commission_percentage
            partner.save(update_fields=['commission'])

            # Send achievement email
            send_mail(
                '🎉 Task Goal Achieved!',
                f'''Congratulations {partner.user.username}!\n
You've achieved the goal for "{task.task_name}".\n
New commission rate: {task.commission_percentage}%''',
                settings.DEFAULT_FROM_EMAIL,
                [partner.user.email],
                fail_silently=False,
            )
            break  # Stop after highest valid commission task

        else:
            # Send progress notifications
            message = None
            if progress >= 70:
                message = '70% of your goal! Almost there! 💪'
            elif progress >= 50:
                message = '50% of your goal reached! Keep going! 🚀'

            if message:
                remaining = goal - contacts_count
                send_mail(
                    '📈 Task Progress Update',
                    f'''Hi {partner.user.first_name},\n
{message}\n
Task: {task.task_name}\n
Progress: {int(progress)}%\n
Contacts added: {contacts_count}\n
Remaining: {remaining}''',
                    settings.DEFAULT_FROM_EMAIL,
                    [partner.user.email],
                    fail_silently=False,
                )

