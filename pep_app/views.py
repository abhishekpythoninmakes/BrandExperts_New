from django.shortcuts import render , HttpResponse
from products_app .models import CustomUser
from .models import *
# Create your views here.

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


