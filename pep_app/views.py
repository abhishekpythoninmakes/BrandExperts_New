from django.shortcuts import render , HttpResponse
from products_app .models import CustomUser
from .models import *
import json
# Create your views here.
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers import serialize
from .models import ContactList


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
    recipient = get_object_or_404(EmailRecipient, tracking_id=tracking_id)
    if not recipient.opened_at:
        recipient.opened_at = timezone.now()
        recipient.status = 'opened'
        recipient.save()
    # Return transparent 1x1 pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return HttpResponse(pixel, content_type='image/gif')




