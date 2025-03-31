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
from django.core.exceptions import ObjectDoesNotExist

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


@shared_task
def add_contacts_to_contactlist(contactlist_id, contact_ids):
    """
    Celery task to add contacts to the ContactList's many-to-many field.
    """
    try:
        # Fetch the ContactList instance
        contactlist = ContactList.objects.get(id=contactlist_id)

        # Fetch all Contact instances
        contacts = Contact.objects.filter(id__in=contact_ids)

        # Add contacts to the many-to-many field
        contactlist.contacts_new.add(*contacts)
        k = [x for x in contactlist.contacts_new.all()]
        print("K   ===",k)

        # Debug: Print success message
        print(f"Added {len(contacts)} contacts to ContactList {contactlist.name}")
    except ObjectDoesNotExist as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")





############## SENDING EMAIL CAMPAIGN #################

import re
from urllib.parse import urljoin
import traceback

from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import EmailCampaign, EmailRecipient, Contact


@shared_task
def send_email_campaign(campaign_id):
    print(f"Starting email campaign task for campaign_id: {campaign_id}")

    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)
        print(f"Found campaign: {campaign.name} (ID: {campaign_id})")

        # Get all contacts from associated contact lists
        contacts = Contact.objects.filter(
            contactlist__in=campaign.contact_lists.all()
        ).distinct()

        print(f"Found {contacts.count()} unique contacts to email")

        if not contacts.exists():
            print("No contacts found for this campaign. Exiting task.")
            campaign.status = 'sent'  # Mark as sent even though no emails were sent
            campaign.save()
            return

        # Create recipients
        recipients = []
        for contact in contacts:
            # Check if recipient already exists to avoid duplicates
            if not EmailRecipient.objects.filter(campaign=campaign, contact=contact).exists():
                recipients.append(
                    EmailRecipient(campaign=campaign, contact=contact)
                )

        if recipients:
            EmailRecipient.objects.bulk_create(recipients)
            print(f"Created {len(recipients)} email recipients")

        campaign.total_recipients = contacts.count()
        campaign.save()

        # Check if the campaign has content to send
        try:
            subject = campaign.subject or "No Subject"

            # Try to get content using get_email_content method if it exists
            if hasattr(campaign, 'get_email_content'):
                base_content = campaign.get_email_content()
            else:
                # Fallback content retrieval logic
                if campaign.custom_content:
                    base_content = campaign.custom_content
                elif campaign.template and hasattr(campaign.template, 'content'):
                    base_content = campaign.template.content
                else:
                    base_content = ""

            if not base_content:
                print("Campaign has no content. Setting default content.")
                base_content = "<p>This email does not have any content.</p>"

            print(f"Email subject: {subject}")
            print(f"Content length: {len(base_content)} characters")
            print(f"Content preview: {base_content[:100]}...")

        except Exception as e:
            print(f"Error preparing email content: {str(e)}")
            print(traceback.format_exc())
            base_content = "<p>This email could not be properly generated.</p>"
            subject = "Email from our system"

        # Make image URLs absolute
        try:
            soup = BeautifulSoup(base_content, 'html.parser')
            for img in soup.find_all('img'):
                if 'src' in img.attrs and img['src'].startswith(('/media/', '/static/')):
                    img['src'] = urljoin(settings.DOMAIN, img['src'])
            processed_content = str(soup)
        except Exception as e:
            print(f"Error processing HTML content: {str(e)}")
            print(traceback.format_exc())
            processed_content = base_content

        # Check email settings
        print(f"Using email sender: {campaign.sender_name or settings.DEFAULT_FROM_EMAIL}")
        print(f"EMAIL_BACKEND setting: {settings.EMAIL_BACKEND}")
        print(f"EMAIL_HOST setting: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT setting: {settings.EMAIL_PORT}")

        # Send emails to each recipient
        success_count = 0
        fail_count = 0

        for recipient in EmailRecipient.objects.filter(campaign=campaign):
            try:
                contact = recipient.contact
                print(f"Preparing email for: {contact.email}")

                if not contact.email:
                    print(f"Contact ID {contact.id} has no email address. Skipping.")
                    recipient.status = 'failed'
                    recipient.save()
                    fail_count += 1
                    continue
                # Replace placeholders in content
                try:
                    content = processed_content
                    # Find all placeholders with pattern [FIELD_NAME]
                    placeholders = re.findall(r'\[(.*?)\]', content)
                    for placeholder in placeholders:
                        field_value = None
                        try:
                            # Handle special cases for date and time
                            if placeholder.lower() == 'date':
                                field_value = timezone.now().strftime('%Y-%m-%d')
                                print(f"Replacing date placeholder with: {field_value}")
                            elif placeholder.lower() == 'time':
                                field_value = timezone.now().strftime('%H:%M:%S')
                                print(f"Replacing time placeholder with: {field_value}")
                            # Handle special cases for related fields
                            elif placeholder.lower() == 'account':
                                # Join all account names for many-to-many relationship
                                accounts = contact.account.all()
                                field_value = ', '.join(
                                    [str(account) for account in accounts]) if accounts.exists() else ''
                            else:
                                # Use getattr for other fields
                                field_value = getattr(contact, placeholder.lower(), '')
                        except Exception as e:
                            print(f"Error fetching placeholder {placeholder}: {str(e)}")
                            field_value = ''  # Fallback to empty string

                        # Replace placeholder in content
                        if field_value is not None:
                            content = content.replace(f'[{placeholder}]', str(field_value))
                except Exception as e:
                    print(f"Error replacing placeholders: {str(e)}")
                    print(traceback.format_exc())
                    content = processed_content  # Fallback to unprocessed content

                # Add tracking pixel
                try:
                    tracking_url = recipient.tracking_pixel_url()
                    tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" alt="">'
                    print(f"Adding tracking pixel with URL: {tracking_url}")

                    if '</body>' in content:
                        content = content.replace('</body>', f'{tracking_pixel}</body>')
                    else:
                        content += tracking_pixel

                except Exception as e:
                    print(f"Error adding tracking pixel: {str(e)}")
                    print(traceback.format_exc())

                # Create and send email
                try:
                    email_from = settings.DEFAULT_FROM_EMAIL
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body="This is the plain text version of your email. Please view in HTML for proper formatting.",
                        # Plain text version
                        from_email=email_from,
                        to=[contact.email]
                    )
                    msg.attach_alternative(content, "text/html")

                    print(f"SMTP DEBUG: Attempting to send email to {contact.email} from {email_from}")
                    print(f"SMTP DEBUG: Subject: {subject}")
                    print(f"SMTP DEBUG: Content length: {len(content)} characters")

                    # Try to send with explicit error capture
                    try:
                        msg.send(fail_silently=False)
                        print(f"Email sent successfully to {contact.email}")
                    except Exception as smtp_error:
                        print(f"SMTP ERROR: {str(smtp_error)}")
                        print(traceback.format_exc())
                        raise  # Re-raise to the outer exception handler

                    # Update recipient status
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    recipient.save()
                    success_count += 1

                except Exception as e:
                    print(f"Error sending email to {contact.email}: {str(e)}")
                    print(traceback.format_exc())
                    recipient.status = 'failed'
                    recipient.save()
                    fail_count += 1

            except Exception as e:
                print(f"Unexpected error processing recipient: {str(e)}")
                print(traceback.format_exc())
                if recipient:
                    recipient.status = 'failed'
                    recipient.save()
                fail_count += 1

        # Finalize campaign
        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()
        print("Email campaign task completed. === status ==",campaign.status)

        print(f"Campaign {campaign_id} completed: {success_count} sent, {fail_count} failed")
        return f"Campaign {campaign_id} completed: {success_count} sent, {fail_count} failed"

    except Exception as e:
        print(f"Fatal error in send_email_campaign task: {str(e)}")
        print(traceback.format_exc())
        try:
            # Try to update campaign status if possible
            campaign = EmailCampaign.objects.get(id=campaign_id)
            campaign.status = 'cancelled'
            campaign.save()
        except:
            pass
        raise


import logging
from django.core.exceptions import MultipleObjectsReturned
from customer .models import Customer
logger = logging.getLogger(__name__)


@shared_task
def link_contact_and_update_status(customer_email):
    try:
        # Retrieve customer with prefetched user
        customer = Customer.objects.select_related('user').get(user__email=customer_email)

        try:
            # Get single contact (assuming unique email)
            contact = Contact.objects.get(email=customer_email)

            # Update contact with customer's user
            contact.user = customer.user
            contact.status = 'client'
            contact.save()

            # Update related accounts using bulk_update for efficiency
            accounts = contact.account.all()
            if accounts.exists():
                for account in accounts:
                    account.status = 'client'
                Accounts.objects.bulk_update(accounts, ['status'])

            logger.info(f"Updated contact {contact.id} and associated accounts")

        except Contact.DoesNotExist:
            logger.warning(f"No contact found for email: {customer_email}")
        except MultipleObjectsReturned:
            logger.error(f"Multiple contacts found for email: {customer_email} - expected only one")

    except Customer.DoesNotExist:
        logger.error(f"Customer not found for email: {customer_email}")
    except Exception as e:
        logger.error(f"Critical error processing {customer_email}: {str(e)}", exc_info=True)