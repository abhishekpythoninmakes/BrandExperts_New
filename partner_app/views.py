import json

from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pep_app .models import Partners, Contact
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from .serializers import ContactCreateSerializer
# Create your views here.


def is_admin_or_partner(user):
    return user.is_authenticated and (user.is_admin or user.is_partner)


# Home Page for Partner
#
# @user_passes_test(is_admin_or_partner, login_url='https://www.brandexperts.ae/login')
def home_partner(request):
    context = {'segment': 'index'}
    return render(request,'home/index.html',context)


# User Profile Page for Partner
def user_profile(request):
    context = {'segment': 'page-user'}
    return render(request,'home/page-user.html',context)


# Contacts list using user id

# views.py



class PartnerContactsAPIView(APIView):
    def get(self, request, user_id):
        try:
            # Get the partner associated with the user_id
            partner = Partners.objects.get(user_id=user_id)
        except Partners.DoesNotExist:
            return Response({"error": "Partner not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get all contacts for this partner with prefetched accounts
        contacts = Contact.objects.filter(partner=partner).prefetch_related('account')

        # Prepare the response data
        contacts_data = []
        for contact in contacts:
            # Get comma-separated string of account names
            accounts = contact.account.all()
            accounts_str = ", ".join([str(account) for account in accounts])

            contacts_data.append({
                "id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "number": contact.mobile,
                "accounts": accounts_str
            })

        return Response({
            "total_contacts": len(contacts_data),
            "contacts": contacts_data
        })


# Contacts delete

class ContactDeleteAPIView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                # Get contact with related user in a single query
                contact = Contact.objects.select_related('user').get(pk=pk)
                user = contact.user

                # Store contact details for response before deleting
                contact_name = contact.name if hasattr(contact, 'name') else "Contact"

                # Delete contact first
                contact.delete()

                # Delete associated user if it exists
                if user:
                    user.delete()

        except Contact.DoesNotExist:
            return Response({"error": "Contact not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"{contact_name} has been successfully deleted."}, status=status.HTTP_200_OK)


# Create Contact

class TextPlainJSONParser(JSONParser):
    media_type = 'text/plain'


class ContactCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, TextPlainJSONParser, FormParser]

    def post(self, request):
        # Manual content type handling
        content_type = request.content_type.split(';')[0].strip().lower()

        try:
            # Handle raw text/plain input
            if content_type == 'text/plain':
                data = json.loads(request.body)
            else:
                data = request.data
        except json.JSONDecodeError as e:
            return Response(
                {
                    "error": "Invalid JSON format",
                    "detail": str(e),
                    "example_request": {
                        "partner_user_id": 123,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "mobile": "+1234567890",
                        "accounts": ["Company A"],
                        "status": "lead"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ContactCreateSerializer(
            data=data,
            context={'request': request}
        )

        if serializer.is_valid():
            contact = serializer.save()
            return Response({
                'id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'mobile': contact.mobile,
                'status': contact.status,
                'partner': {
                    'user_id': contact.partner.user.id,
                    'username': contact.partner.user.username
                },
                'created_by': contact.created_by.username,
                'accounts': [account.name for account in contact.account.all()],
                'additional_data': contact.additional_data,
                'created_at': contact.created_at
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)