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
from rest_framework.decorators import action, permission_classes, api_view


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
from .serializers import CampaignAnalyticsSerializer, EmailCronJobSerializer, CronJobCreateSerializer, \
    CampaignAnalyticsSerializerNew

logger = logging.getLogger(__name__)


# Keep existing views...

def partner_contacts(request, partner_id):
    """View to get all contacts for a specific partner"""
    try:
        partner = Partners.objects.get(user_id=partner_id)
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
                    'email_deliverability': contact.email_deliverability,
                }
                for contact in contacts
            ],
            'total': contacts.count()
        }

        return JsonResponse(data)
    except Partners.DoesNotExist:
        return JsonResponse({'error': 'Partner not found'}, status=404)

def partner_contacts_partner_id(request, partner_id):
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
                    'email_deliverability': contact.email_deliverability,
                }
                for contact in contacts
            ],
            'total': contacts.count()
        }

        return JsonResponse(data)
    except Partners.DoesNotExist:
        return JsonResponse({'error': 'Partner not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def partner_contacts_new(request):
    """View to get all contacts for the logged-in partner"""
    try:
        # Get the partner associated with the logged-in user
        partner = get_object_or_404(Partners, user=request.user)

        # Get query parameters for filtering
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))

        # Start with all contacts for this partner
        contacts = Contact.objects.filter(partner=partner)

        # Apply search filter
        if search:
            contacts = contacts.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search)
            )

        # Apply status filter
        if status_filter:
            contacts = contacts.filter(status=status_filter)

        # Get total count before pagination
        total_count = contacts.count()

        # Apply pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_contacts = contacts.order_by('-created_at')[start_index:end_index]

        # Prepare response data
        data = {
            'partner': {
                'id': partner.id,
                'name': partner.user.get_full_name() or partner.user.username,
                'username': partner.user.username,
                'email': partner.user.email,
            },
            'contacts': [
                {
                    'id': contact.id,
                    'name': contact.name,
                    'email': contact.email,
                    'mobile': contact.mobile,
                    'status': contact.status,
                    'email_deliverability': contact.email_deliverability,
                    'created_at': contact.created_at.isoformat(),
                    'accounts': [account.name for account in contact.account.all()] if contact.account.exists() else []
                }
                for contact in paginated_contacts
            ],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'has_next': end_index < total_count,
                'has_previous': page > 1
            },
            'stats': {
                'total_contacts': total_count,
                'status_counts': {
                    'lead': contacts.filter(status='lead').count(),
                    'client': contacts.filter(status='client').count(),
                    'data': contacts.filter(status='data').count(),
                    'prospect': contacts.filter(status='prospect').count(),
                    'unsubscribed': contacts.filter(status='unsubscribed').count(),
                }
            }
        }

        return Response(data)

    except Partners.DoesNotExist:
        return Response({'error': 'Partner profile not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


class CampaignAnalyticsView(View):
    """View to get campaign analytics for a specific partner"""

    def get(self, request, partner_id):
        try:
            partner = Partners.objects.get(user_id=partner_id)

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
            partner = Partners.objects.get(user_id=partner_id)

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

from rest_framework.views import APIView

class PartnerCampaignAnalyticsView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the partner_id from the URL path parameter
        partner_id = kwargs.get('partner_id')
        if not partner_id:
            return Response({"error": "partner_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the partner object using user_id
            partner = Partners.objects.get(user_id=partner_id)
        except Partners.DoesNotExist:
            return Response({"error": "Partner not found"}, status=status.HTTP_404_NOT_FOUND)

        # Filter campaigns associated with the partner
        campaigns = EmailCampaign.objects.filter(
            contact_lists__contacts_new__partner=partner
        ).distinct()

        # Total campaigns
        total_campaigns = campaigns.count()

        # Total recipients (calculated dynamically from EmailRecipient)
        total_recipients = EmailRecipient.objects.filter(
            campaign__in=campaigns
        ).count()

        # Total earnings (calculated based on commission and total recipients)
        total_earnings = total_recipients * float(partner.commission)

        # Total sent campaigns
        total_sent_campaigns = campaigns.filter(status='sent').count()

        # Total completed campaigns
        total_completed_campaigns = campaigns.filter(delivery_status='campaign_sent').count()

        # Total failed campaigns
        total_queued_campaigns = campaigns.filter(status='queued').count()
        total_failed_campaigns = campaigns.filter(status='failed').count()

        # Total opened emails
        total_opened_emails = EmailRecipient.objects.filter(
            campaign__in=campaigns, status='opened'
        ).count()

        # Total link clicked
        total_link_clicked = EmailRecipient.objects.filter(
            campaign__in=campaigns, status='link'
        ).count()

        # Get email deliverability status counts (valid/invalid emails)
        valid_email_contacts = Contact.objects.filter(
            email_deliverability="Email is valid and deliverable"
        ).count()

        invalid_email_contacts = Contact.objects.filter(
            email_deliverability="Invalid email"
        ).count()

        # Prepare the response data
        data = {
            "total_campaigns": total_campaigns,
            "total_recipients": total_recipients,
            "total_earnings": total_earnings,
            "total_sent_campaigns": total_sent_campaigns,
            "total_completed_campaigns": total_completed_campaigns,
            "total_failed_campaigns": total_failed_campaigns,
            "total_queued_campaigns": total_queued_campaigns,
            "total_opened_emails": total_opened_emails,
            "total_link_clicked": total_link_clicked,
            "valid_email_contacts": valid_email_contacts,
            "invalid_email_contacts": invalid_email_contacts,
        }

        # Serialize the data
        serializer = CampaignAnalyticsSerializerNew(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from .models import Partners, Contact, EmailCampaign, EmailRecipient
from .serializers import (
    PartnerSerializer, PartnerCreateSerializer,
    PartnerUpdateSerializer, PartnerDetailSerializer
)


class PartnerListView(generics.ListAPIView):
    """
    List all partners with optional filtering and search
    """
    serializer_class = PartnerDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Partners.objects.select_related('user').all()

        # Search filter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(mobile_number__icontains=search)
            )

        # Status filter
        status = self.request.query_params.get('status', None)
        if status == 'active':
            queryset = queryset.filter(user__is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(user__is_active=False)

        return queryset.order_by('-created_at')


class PartnerCreateView(generics.CreateAPIView):
    """
    Create a new partner
    """
    serializer_class = PartnerCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class PartnerDetailView(generics.RetrieveAPIView):
    """
    Retrieve partner details
    """
    serializer_class = PartnerDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Partners.objects.select_related('user').all()


class PartnerUpdateView(generics.UpdateAPIView):
    """
    Update partner details
    """
    serializer_class = PartnerUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Partners.objects.select_related('user').all()


class PartnerDeleteView(generics.DestroyAPIView):
    """
    Delete a partner (soft delete by deactivating user)
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Partners.objects.select_related('user').all()

    def perform_destroy(self, instance):
        # Soft delete by deactivating the user
        instance.user.is_active = False
        instance.user.save()

class PartnerHardDeleteView(generics.DestroyAPIView):
    """
    Permanently delete a partner and associated user (USE WITH CAUTION)
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Partners.objects.select_related('user').all()

    def perform_destroy(self, instance):
        # Delete the user first, then the partner
        user = instance.user
        instance.delete()
        user.delete()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def partner_stats(request, partner_id):
    """
    Get detailed statistics for a specific partner
    """
    partner = get_object_or_404(Partners, id=partner_id)

    # Contact statistics
    contacts = Contact.objects.filter(partner=partner)
    total_contacts = contacts.count()
    contact_status_stats = contacts.values('status').annotate(count=Count('id'))

    # Campaign statistics
    campaigns = EmailCampaign.objects.filter(
        contact_lists__contacts_new__partner=partner
    ).distinct()
    total_campaigns = campaigns.count()

    # Email recipient statistics
    recipients = EmailRecipient.objects.filter(contact__partner=partner)
    recipient_status_stats = recipients.values('status').annotate(count=Count('id'))

    # Calculate total earnings (based on commission and sent emails)
    sent_emails = recipients.filter(status__in=['sent', 'opened', 'link']).count()
    total_earnings = sent_emails * float(partner.commission)

    data = {
        'partner': PartnerDetailSerializer(partner).data,
        'stats': {
            'total_contacts': total_contacts,
            'contact_status_distribution': list(contact_status_stats),
            'total_campaigns': total_campaigns,
            'email_stats': {
                'total_sent': recipients.filter(status='sent').count(),
                'total_opened': recipients.filter(status='opened').count(),
                'total_clicked': recipients.filter(status='link').count(),
                'total_unsubscribed': recipients.filter(status='unsubscribed').count(),
                'total_failed': recipients.filter(status='failed').count(),
            },
            'recipient_status_distribution': list(recipient_status_stats),
            'total_earnings': total_earnings,
            'sent_emails': sent_emails,
        }
    }

    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_partner_status(request, partner_id):
    """
    Activate/Deactivate a partner
    """
    partner = get_object_or_404(Partners, id=partner_id)
    partner.user.is_active = not partner.user.is_active
    partner.user.save()

    action = "activated" if partner.user.is_active else "deactivated"
    return Response({
        'message': f'Partner {action} successfully',
        'is_active': partner.user.is_active
    })
