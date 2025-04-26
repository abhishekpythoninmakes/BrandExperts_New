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

@require_GET
def partner_contacts(request, partner_id):
    """
    API endpoint to get all contacts for a specific partner with email deliverability status
    """
    partner = get_object_or_404(Partners, id=partner_id)
    contacts = Contact.objects.filter(partner=partner).order_by('-created_at')

    # Prepare contact data with email deliverability status
    contact_data = []
    for contact in contacts:
        # Get email campaign status for this contact
        recipient_statuses = EmailRecipient.objects.filter(contact=contact).values('status').annotate(count=Count('id'))
        campaign_status = {status['status']: status['count'] for status in recipient_statuses}

        # Get email deliverability status
        deliverability_status = "Unknown"
        if contact.email_deliverability:
            try:
                data = json.loads(contact.email_deliverability)
                deliverability_status = data.get('status', 'Unknown')
            except json.JSONDecodeError:
                pass

        contact_data.append({
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'mobile': contact.mobile,
            'status': contact.status,
            'created_at': contact.created_at.isoformat() if contact.created_at else None,
            'email_deliverability': deliverability_status,
            'campaign_status': campaign_status,
            'accounts': [{'id': acc.id, 'name': acc.name} for acc in contact.account.all()]
        })

    return JsonResponse({
        'partner': {
            'id': partner.id,
            'name': partner.user.username if partner.user else "Unknown",
            'commission': float(partner.commission)
        },
        'contacts': contact_data
    })


class CampaignAnalyticsView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving campaign analytics for a partner
    """
    serializer_class = CampaignAnalyticsSerializer

    def get_object(self):
        partner_id = self.kwargs.get('partner_id')
        partner = get_object_or_404(Partners, id=partner_id)

        # Get all contacts for this partner
        partner_contacts = Contact.objects.filter(partner=partner)

        # Get all recipients for these contacts
        recipients = EmailRecipient.objects.filter(contact__in=partner_contacts)

        # Get all campaigns for these recipients
        campaign_ids = recipients.values_list('campaign_id', flat=True).distinct()
        campaigns = EmailCampaign.objects.filter(id__in=campaign_ids)

        # Calculate analytics
        total_campaigns = campaigns.count()

        # Get recipient stats
        recipient_stats = recipients.aggregate(
            total_sent=Count(Case(When(status='sent', then=1), output_field=IntegerField())),
            total_opened=Count(Case(When(status='opened', then=1), output_field=IntegerField())),
            total_clicked=Count(Case(When(status='link', then=1), output_field=IntegerField())),
            total_failed=Count(Case(When(status='failed', then=1), output_field=IntegerField())),
            total_unsubscribed=Count(Case(When(status='unsubscribed', then=1), output_field=IntegerField()))
        )

        total_sent = recipient_stats.get('total_sent', 0)
        total_opened = recipient_stats.get('total_opened', 0)
        total_clicked = recipient_stats.get('total_clicked', 0)
        total_failed = recipient_stats.get('total_failed', 0)
        total_unsubscribed = recipient_stats.get('total_unsubscribed', 0)

        # Calculate rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0

        # Get last campaign date
        last_campaign = campaigns.order_by('-created_at').first()
        last_campaign_date = last_campaign.created_at if last_campaign else None

        # Get upcoming campaigns from cron jobs
        now = timezone.now()
        upcoming_cron_jobs = EmailCronJob.objects.filter(
            status='active',
            next_run__gt=now,
            partners=partner
        ).order_by('next_run')[:5]

        upcoming_campaigns = []
        for job in upcoming_cron_jobs:
            upcoming_campaigns.append({
                'id': str(job.id),
                'name': job.name,
                'template': job.email_template.name if job.email_template else "No template",
                'scheduled_time': job.next_run.isoformat() if job.next_run else None,
                'start_date': job.start_date.isoformat() if job.start_date else None,
                'end_date': job.end_date.isoformat() if job.end_date else None
            })

        # Get recent campaigns
        recent_campaigns = []
        for campaign in campaigns.order_by('-created_at')[:5]:
            campaign_recipients = recipients.filter(campaign=campaign)
            recent_campaigns.append({
                'id': campaign.id,
                'name': campaign.name,
                'sent_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'status': campaign.status,
                'recipients': campaign_recipients.count(),
                'opened': campaign_recipients.filter(status='opened').count(),
                'clicked': campaign_recipients.filter(status='link').count(),
                'failed': campaign_recipients.filter(status='failed').count(),
                'unsubscribed': campaign_recipients.filter(status='unsubscribed').count()
            })

        # Get new contacts count (added in the last 7 days)
        seven_days_ago = now - timezone.timedelta(days=7)
        new_contacts_count = partner_contacts.filter(created_at__gte=seven_days_ago).count()

        # Get total contacts
        total_contacts = partner_contacts.count()

        # Get contact status distribution
        contact_status_distribution = list(partner_contacts.values('status').annotate(
            count=Count('status')
        ).order_by('-count'))

        # Get partner earnings (commission)
        partner_earnings = float(partner.commission) if partner.commission else 0.0

        # Get partner tasks
        today = timezone.now().date()
        partner_tasks = partner.tasks.filter(
            start_date__lte=today,
            end_date__gte=today
        ).count()

        # Prepare the result
        result = {
            'total_campaigns': total_campaigns,
            'total_sent': total_sent,
            'total_failed': total_failed,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_unsubscribed': total_unsubscribed,
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'last_campaign_date': last_campaign_date,
            'upcoming_campaigns': upcoming_campaigns,
            'recent_campaigns': recent_campaigns,
            'new_contacts_count': new_contacts_count,
            'total_contacts': total_contacts,
            'contact_status_distribution': contact_status_distribution,
            'partner_name': partner.user.username if partner.user else "Unknown Partner",
            'partner_earnings': partner_earnings,
            'partner_tasks': partner_tasks
        }

        return result


class EmailCronJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing email cron jobs
    """
    queryset = EmailCronJob.objects.all()
    serializer_class = EmailCronJobSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CronJobCreateSerializer
        return EmailCronJobSerializer

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Manually execute a cron job
        """
        cron_job = self.get_object()
        execute_email_cron_job.delay(str(cron_job.id))
        return Response({'status': 'Cron job execution scheduled'})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Pause a cron job
        """
        cron_job = self.get_object()
        cron_job.status = 'paused'
        cron_job.save()
        return Response({'status': 'Cron job paused'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        Resume a paused cron job
        """
        cron_job = self.get_object()
        cron_job.status = 'active'
        cron_job.save()
        return Response({'status': 'Cron job resumed'})