from django.shortcuts import render, HttpResponse, redirect
from django.views import View
from .tasks import *
from products_app .models import CustomUser
from .models import *
import json
from urllib.parse import unquote
# Create your views here.
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers import serialize
from .models import ContactList
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers import serialize
from django.utils import timezone
from django.db.models import Count, Q, Sum, F, Case, When, IntegerField, FloatField, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from urllib.parse import unquote
import json
import logging

from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


def users_list(request):
    # Force a fresh query for contact lists and their contacts
    contact_lists = ContactList.objects.all().order_by('-id').prefetch_related('contacts_new')

    # Collect all unique contacts from all lists
    contacts = []
    for cl in contact_lists:
        # Force a fresh query for contacts in each list
        contacts.extend(cl.contacts_new.all())

    # Remove duplicates while preserving order (Python 3.7+)
    seen = set()
    unique_contacts = []
    for contact in contacts:
        if contact.id not in seen:
            seen.add(contact.id)
            unique_contacts.append(contact)

    # Serialize to JSON
    data = serialize('json', unique_contacts, fields=('name', 'email', 'mobile'))

    return JsonResponse(data, safe=False)



@require_GET
def placeholder_json(request):
    placeholders = list(Placeholder.objects.values('key', 'value'))
    return JsonResponse(placeholders, safe=False)

@csrf_exempt
@require_POST
def create_placeholder(request):
    try:
        data = json.loads(request.body)
        key = data.get('key')
        value = data.get('value')
        if not key or not value:
            return JsonResponse({'error': 'Key and value are required'}, status=400)
        Placeholder.objects.create(key=key, value=value)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



# views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import EmailRecipient
from django.utils import timezone


def track_email_open(request, tracking_id):
    print(f"Email tracking triggered for ID: {tracking_id}")
    print(f"Tracking open for {tracking_id} at {timezone.now()}")

    try:
        recipient = get_object_or_404(EmailRecipient, tracking_id=tracking_id)

        # Always update the opened_at time to track repeated opens
        recipient.opened_at = timezone.now()
        recipient.status = 'opened'
        recipient.save()

        print(f"Tracked email open for recipient ID: {recipient.id}, email: {recipient.contact.email}")

        # Also update the associated contact's status from 'data' to 'lead'
        contact = recipient.contact
        if contact and contact.status == 'data':
            contact.status = 'lead'
            contact.save()
            print(f"Updated contact {contact.id} status from 'data' to 'lead'")
    except Exception as e:
        print(f"Error in tracking pixel: {str(e)}")

    # Return transparent 1x1 pixel with anti-caching headers
    response = HttpResponse(
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type='image/gif'
    )

    # Add headers to prevent caching
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


# Link Tracking

@require_GET
def track_link_click(request, tracking_id):
    """
    Track when a link in an email is clicked and redirect to the original URL
    """
    try:
        recipient = get_object_or_404(EmailRecipient, tracking_id=tracking_id)
        original_url = unquote(request.GET.get('url', ''))

        if not original_url:
            print(f"No URL provided in tracking link (tracking_id: {tracking_id})")
            return redirect(settings.DOMAIN)  # Fallback redirect

        # Update recipient status to 'link' (clicked)
        recipient.status = 'link'
        recipient.save()

        # Update contact status to 'prospect' if it's currently 'data'
        if recipient.contact:
            recipient.contact.status = 'prospect'
            recipient.contact.save()

        print(f"Link clicked by {recipient.contact.email} - redirecting to {original_url}")

        return redirect(original_url)

    except Exception as e:
        print(f"Error tracking link click: {str(e)}")
        return redirect(settings.DOMAIN)  # Fallback redirect


# Unsubscribe

def unsubscribe(request, tracking_id):
    """
    Handle unsubscribe requests using the existing tracking_id
    """
    recipient = get_object_or_404(EmailRecipient, tracking_id=tracking_id)

    # Update contact status
    contact = recipient.contact
    contact.status = 'unsubscribed'
    contact.save()

    # Update recipient status
    recipient.status = 'unsubscribed'
    recipient.save()

    return render(request, 'emails/unsubscribe_success.html')


from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum, F, Case, When, IntegerField, FloatField
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from urllib.parse import unquote
import json
import logging
from rest_framework import generics, status, viewsets
from .models import (
    Partners, Contact, ContactList, EmailCampaign, EmailRecipient,
    EmailCronJob, CronJobExecution, Placeholder
)
from .serializers import CampaignAnalyticsSerializer, EmailCronJobSerializer, CronJobCreateSerializer

logger = logging.getLogger(__name__)


# Keep existing views...

def partner_contacts(request, partner_id):
    """View to get all contacts for a specific partner"""
    try:
        partner = Partners.objects.get(id=partner_id)
        contacts = Contact.objects.filter(partner=partner)

        data = {
            'partner': {
                'id': partner.id,
                'name': partner.user.username if partner.user else "Unknown",
            },
            'contacts': [
                {
                    'id': contact.id,
                    'name': contact.name,
                    'email': contact.email,
                    'status': contact.status,
                    'created_at': contact.created_at.isoformat(),
                }
                for contact in contacts
            ],
            'total': contacts.count()
        }

        return JsonResponse(data)
    except Partners.DoesNotExist:
        return JsonResponse({'error': 'Partner not found'}, status=404)


class CampaignAnalyticsView(View):
    """View to get campaign analytics for a specific partner"""

    def get(self, request, partner_id):
        try:
            partner = Partners.objects.get(id=partner_id)

            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            status = request.GET.get('status')

            # Base query - get campaigns for contacts added by this partner
            campaigns = EmailCampaign.objects.filter(
                contact_lists__contacts_new__partner=partner
            ).distinct()

            # Apply filters
            if start_date:
                campaigns = campaigns.filter(created_at__gte=start_date)
            if end_date:
                campaigns = campaigns.filter(created_at__lte=end_date)
            if status:
                campaigns = campaigns.filter(status=status)

            # Prepare response data
            campaign_data = []
            for campaign in campaigns:
                # Get recipients for this campaign from this partner
                recipients = EmailRecipient.objects.filter(
                    campaign=campaign,
                    contact__partner=partner
                )

                # Get execution data if this was from a cron job
                executions = CronJobExecution.objects.filter(campaign=campaign)
                cron_job = None
                if executions.exists():
                    cron_job = executions.first().cron_job

                campaign_data.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'status': campaign.status,
                    'delivery_status': campaign.delivery_status,
                    'created_at': campaign.created_at.isoformat(),
                    'total_recipients': recipients.count(),
                    'opened': recipients.filter(status='opened').count(),
                    'clicked': recipients.filter(status='link').count(),
                    'unsubscribed': recipients.filter(status='unsubscribed').count(),
                    'next_run': cron_job.next_run.isoformat() if cron_job and cron_job.next_run else None,
                    'last_run': cron_job.last_run.isoformat() if cron_job and cron_job.last_run else None,
                })

            return JsonResponse({
                'partner': {
                    'id': partner.id,
                    'name': partner.user.username if partner.user else "Unknown",
                },
                'campaigns': campaign_data,
                'total': len(campaign_data)
            })

        except Partners.DoesNotExist:
            return JsonResponse({'error': 'Partner not found'}, status=404)


class CompletedCampaignAnalyticsView(View):
    """View to get analytics for completed campaigns for a specific partner"""

    def get(self, request, partner_id):
        try:
            partner = Partners.objects.get(id=partner_id)

            # Get completed campaigns for this partner
            completed_campaigns = EmailCampaign.objects.filter(
                contact_lists__contacts_new__partner=partner,
                status='sent',
                delivery_status='campaign_sent'
            ).distinct()

            # Prepare detailed analytics
            campaign_analytics = []
            for campaign in completed_campaigns:
                # Get recipients for this campaign from this partner
                recipients = EmailRecipient.objects.filter(
                    campaign=campaign,
                    contact__partner=partner
                )

                total = recipients.count()
                opened = recipients.filter(status='opened').count()
                clicked = recipients.filter(status='link').count()
                unsubscribed = recipients.filter(status='unsubscribed').count()

                # Calculate rates
                open_rate = (opened / total * 100) if total > 0 else 0
                click_rate = (clicked / total * 100) if total > 0 else 0
                unsubscribe_rate = (unsubscribed / total * 100) if total > 0 else 0

                campaign_analytics.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'created_at': campaign.created_at.isoformat(),
                    'total_recipients': total,
                    'opened': opened,
                    'clicked': clicked,
                    'unsubscribed': unsubscribed,
                    'open_rate': round(open_rate, 2),
                    'click_rate': round(click_rate, 2),
                    'unsubscribe_rate': round(unsubscribe_rate, 2),
                })

            return JsonResponse({
                'partner': {
                    'id': partner.id,
                    'name': partner.user.username if partner.user else "Unknown",
                },
                'completed_campaigns': campaign_analytics,
                'total': len(campaign_analytics)
            })

        except Partners.DoesNotExist:
            return JsonResponse({'error': 'Partner not found'}, status=404)