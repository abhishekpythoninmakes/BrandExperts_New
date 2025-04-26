# tasks.py
import os
import pytz
import json
tz = pytz.UTC
import time
from urllib.parse import quote
from datetime import datetime, timedelta
from datetime import datetime, timezone as pytz_timezone
from datetime import datetime, timedelta, time as dt_time
from django.core.exceptions import ValidationError
from decimal import Decimal
from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import Contact, Partners, Tasks, ContactList, Accounts, EmailCronJob
import pandas as pd
from products_app.models import CustomUser
from django.core.exceptions import ObjectDoesNotExist
import pytz


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
        ).exclude(
            status='unsubscribed'
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
            processed_content = str(soup).encode('utf-8').decode('utf-8')
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

                # Double-check contact status (in case it changed after recipient creation)
                if contact.status == 'unsubscribed':
                    print(f"Contact {contact.email} is unsubscribed. Skipping.")
                    recipient.status = 'unsubscribed'
                    recipient.save()
                    continue

                if not contact.email:
                    print(f"Contact ID {contact.id} has no email address. Skipping.")
                    recipient.status = 'failed'
                    recipient.save()
                    fail_count += 1
                    continue
                # Replace placeholders in content
                try:
                    content = processed_content.encode('utf-8').decode('utf-8')
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

                # Add unsubscribe link
                unsubscribe_url = f"{settings.DOMAIN}/pep/unsubscribe/{recipient.tracking_id}/"
                unsubscribe_html = f"""
                <div style="margin: 20px 0; padding: 15px 0; border-top: 1px solid #eeeeee; font-size: 12px; color: #999999; text-align: center;">
                    <p>If you wish to unsubscribe from future emails, 
                    <a href="{unsubscribe_url}" style="color: #999999;">click here</a>.</p>
                </div>
                """

                # Process links for tracking
                try:
                    soup = BeautifulSoup(content, 'html.parser')

                    # First add the unsubscribe section to the email body
                    if soup.body:
                        soup.body.append(BeautifulSoup(unsubscribe_html, 'html.parser'))
                    else:
                        # If no <body> tag exists, append to the end
                        soup.append(BeautifulSoup(unsubscribe_html, 'html.parser'))

                    # Then process all other links for tracking
                    for a in soup.find_all('a', href=True):
                        original_url = a['href']
                        # Skip processing if it's the unsubscribe link we just added
                        if original_url == unsubscribe_url:
                            continue
                        if original_url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                            # Create tracking URL
                            tracking_url = f"{settings.DOMAIN}/pep/track-link/{recipient.tracking_id}/?url={quote(original_url)}"
                            a['href'] = tracking_url
                            print(f"Replaced link: {original_url} -> {tracking_url}")

                    content = str(soup)
                except Exception as e:
                    print(f"Error processing links for tracking: {str(e)}")
                    print(traceback.format_exc())
                    # Fallback: append unsubscribe section to raw content
                    if '</body>' in content:
                        content = content.replace('</body>', f'{unsubscribe_html}</body>')
                    else:
                        content += unsubscribe_html

                # Add tracking pixel
                try:
                    # Get tracking URL with cache busting
                    timestamp = int(time.time())  # Import time at the top of your file
                    tracking_url = recipient.tracking_pixel_url()

                    # Make sure the URL has cache busting
                    if '?' not in tracking_url:
                        tracking_url = f"{tracking_url}?t={timestamp}"

                    print(f"Adding tracking pixel with URL: {tracking_url}")

                    # Create an enhanced tracking pixel that's more likely to load
                    tracking_pixel = f'''
                    <!-- Email tracking pixel -->
                    <div style="display:none;font-size:1px;color:transparent;max-height:0;max-width:0;opacity:0;overflow:hidden;">
                        <img src="{tracking_url}" width="1" height="1" alt="" style="display:block;">
                    </div>
                    '''

                    # Add the tracking pixel before the closing body tag or at the end
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

            print(f"Updated contact {contact.id} and associated accounts")

        except Contact.DoesNotExist:
            logger.warning(f"No contact found for email: {customer_email}")
        except MultipleObjectsReturned:
            print(f"Multiple contacts found for email: {customer_email} - expected only one")

    except Customer.DoesNotExist:
        print(f"Customer not found for email: {customer_email}")
    except Exception as e:
        print(f"Critical error processing {customer_email}: {str(e)}", exc_info=True)



######################## CRON JOBS ########################

@shared_task
def check_and_execute_cron_jobs():
    """
    Check for cron jobs that need to be executed
    This task should be scheduled to run every day at 7:30 AM UTC
    """
    now = timezone.now()
    logger.info(f"Running check_and_execute_cron_jobs at {now}")

    # Only execute if it's around 7:30 AM UTC (with a 5-minute window)
    current_time = now.time()
    target_time = dt_time(7, 30)  # Fixed: Using time() correctly

    time_diff = abs((current_time.hour * 60 + current_time.minute) -
                    (target_time.hour * 60 + target_time.minute))

    if time_diff > 5:  # More than 5 minutes from 7:30 AM
        logger.info(f"Skipping execution, current time {current_time} is not close to 7:30 AM UTC")
        return

    # Find active jobs within their date range
    today = now.date()
    active_jobs = EmailCronJob.objects.filter(
        status='active',
    )

    # Filter by date range if specified
    date_filtered_jobs = []
    for job in active_jobs:
        if job.start_date and job.start_date > today:
            continue
        if job.end_date and job.end_date < today:
            # Mark as completed if end date has passed
            job.status = 'completed'
            job.save()
            continue
        date_filtered_jobs.append(job)

    logger.info(f"Found {len(date_filtered_jobs)} active cron jobs to execute")

    for job in date_filtered_jobs:
        try:
            # Execute the job
            execute_email_cron_job.delay(str(job.id))

            # Update job status
            job.last_run = now
            job.next_run = job.calculate_next_run()
            job.save()

        except Exception as e:
            logger.error(f"Error processing job {job.id}: {str(e)}")
            logger.error(traceback.format_exc())


@shared_task
def execute_email_cron_job(cron_job_id):
    """Execute a specific email cron job"""
    try:
        cron_job = EmailCronJob.objects.get(id=cron_job_id)
        logger.info(f"Executing cron job: {cron_job.name} (ID: {cron_job_id})")

        # Create execution record
        execution = CronJobExecution.objects.create(
            cron_job=cron_job,
            status='success'
        )

        try:
            # Determine time range for new contacts
            today = timezone.now().date()

            # For the first run, use start_date as reference
            # For subsequent runs, use last_run
            reference_date = None
            if cron_job.last_run:
                reference_date = cron_job.last_run
            else:
                reference_date = timezone.make_aware(
                    datetime.combine(cron_job.start_date or today, dt_time(0, 0)),
                    timezone=pytz.UTC
                )

            logger.info(f"Looking for contacts created after {reference_date}")

            # Find new contacts created since the reference date
            # Exclude contacts that have already been processed by this cron job
            new_contacts_query = Contact.objects.filter(
                created_at__gte=reference_date,
                created_at__date__lte=today
            ).exclude(
                status='unsubscribed'
            ).exclude(
                processed_by_cron_jobs=cron_job
            )

            # If contact lists are specified, only include contacts from those lists
            if cron_job.contact_lists.exists():
                new_contacts_query = new_contacts_query.filter(
                    contactlist__in=cron_job.contact_lists.all()
                )

            # Check email deliverability status
            valid_contacts = []
            partner_ids = set()  # Track unique partner IDs

            for contact in new_contacts_query:
                # Check if email deliverability status is OK
                if contact.email_deliverability:
                    try:
                        deliverability_data = json.loads(contact.email_deliverability)
                        status = deliverability_data.get('status', '').lower()

                        # Only include contacts with valid email status
                        if status in ['valid', 'ok', 'deliverable']:
                            valid_contacts.append(contact)
                            # Track partner ID if available
                            if contact.partner and contact.partner.id:
                                partner_ids.add(contact.partner.id)
                        else:
                            logger.info(f"Skipping contact {contact.email} due to deliverability status: {status}")
                    except json.JSONDecodeError:
                        # If we can't parse the JSON, assume it's not valid
                        logger.warning(f"Could not parse deliverability data for {contact.email}")
                else:
                    # If no deliverability data, include the contact (default to allowing)
                    valid_contacts.append(contact)
                    # Track partner ID if available
                    if contact.partner and contact.partner.id:
                        partner_ids.add(contact.partner.id)

            contacts_count = len(valid_contacts)
            logger.info(f"Found {contacts_count} valid contacts for cron job {cron_job.name}")

            execution.contacts_found = contacts_count
            execution.save()

            if contacts_count == 0:
                execution.status = 'no_contacts'
                execution.save()
                logger.info(f"No new contacts found for cron job {cron_job.name}")
                return f"No new contacts found for cron job {cron_job.name}"

            # Update partners for the cron job based on the contacts
            if partner_ids:
                partners = Partners.objects.filter(id__in=partner_ids)
                cron_job.partners.add(*partners)
                logger.info(f"Added {len(partners)} partners to cron job {cron_job.name}")

            # Create contact list
            contact_list_name = f"Auto-generated for {cron_job.name} on {today}"
            contact_list = ContactList.objects.create(
                name=contact_list_name,
                created_by=cron_job.created_by
            )
            contact_list.contacts_new.add(*valid_contacts)
            logger.info(f"Created contact list with {contacts_count} contacts")

            # Create campaign
            campaign_name = f"Auto-campaign from {cron_job.name} on {today}"
            campaign = EmailCampaign.objects.create(
                name=campaign_name,
                template=cron_job.email_template,
                subject=cron_job.email_template.subject if cron_job.email_template else "No Subject",
                status='draft',
                created_by=cron_job.created_by
            )
            campaign.contact_lists.add(contact_list)

            # Associate with cron job
            cron_job.campaigns.add(campaign)
            execution.campaign = campaign
            execution.save()

            # Add contacts to processed list
            cron_job.processed_contacts.add(*valid_contacts)
            execution.new_contacts_processed.add(*valid_contacts)

            # Queue for sending
            send_email_campaign.delay(campaign.id)
            campaign.status = 'pending'
            campaign.save()

            return f"Successfully executed cron job {cron_job.name}"

        except Exception as e:
            logger.error(f"Error executing cron job {cron_job.name}: {str(e)}")
            logger.error(traceback.format_exc())
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.save()
            return f"Error executing cron job {cron_job.name}: {str(e)}"

    except EmailCronJob.DoesNotExist:
        logger.error(f"Cron job with ID {cron_job_id} not found")
        return f"Error: Cron job with ID {cron_job_id} not found"


@shared_task
def schedule_cron_job(job_id):
    """Schedule a cron job for execution"""
    try:
        job = EmailCronJob.objects.get(id=job_id)
        logger.info(f"Scheduling cron job: {job.name} (ID: {job_id})")

        # Calculate next run time based on frequency
        job.next_run = job.calculate_next_run()

        # Check if the job should be active based on date range
        today = timezone.now().date()
        if job.end_date and today > job.end_date:
            job.status = 'completed'
            logger.info(f"Cron job {job.id} marked as completed (end date reached)")

        job.save()
        logger.info(f"Scheduled cron job {job.id} with next run at {job.next_run}")

    except EmailCronJob.DoesNotExist:
        logger.error(f"Cron job with ID {job_id} not found")
    except Exception as e:
        logger.error(f"Error in schedule_cron_job for job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())