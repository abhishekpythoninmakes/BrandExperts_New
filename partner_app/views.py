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
                "accounts": accounts_str,
                "email_deliverability": contact.email_deliverability,
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
                        "partner_user_id": 253,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "mobile": "+1234567890",
                        "accounts": ["Company A"],
                        "status": "data"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email validation is requested (default to True)
        validate_email_flag = data.pop('validate_email', True)

        serializer = ContactCreateSerializer(
            data=data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                # Save the contact
                contact = serializer.save()

                # Trigger email validation if requested and email exists
                if validate_email_flag and contact.email:
                    validate_email.delay(contact.id)
                    validation_status = "Scheduled"
                else:
                    validation_status = "Skipped" if contact.email else "No email provided"

                # Prepare response
                response_data = {
                    'id': contact.id,
                    'name': contact.name,
                    'email': contact.email,
                    'mobile': contact.mobile,
                    'status': contact.status,
                    'partner': {
                        'user_id': contact.partner.user.id,
                        'username': contact.partner.user.username,
                        'partner_id': contact.partner.id
                    },
                    'created_by': contact.created_by.username,
                    'accounts': [account.name for account in contact.account.all()],
                    'additional_data': contact.additional_data,
                    'created_at': contact.created_at,
                    'email_validation': {
                        'status': validation_status,
                        'deliverability': contact.email_deliverability or "Not checked yet"
                    }
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response(
                    {"error": "Failed to create contact", "detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Partner Details commission

class PartnerStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            # Get the partner associated with the user_id
            partner = Partners.objects.get(user_id=user_id)
            print("partner  ======",partner)
            # Get total number of contacts associated with this partner
            total_contacts = Contact.objects.filter(partner=partner).count()

            # Get the partner's commission
            commission = partner.get_commission()

            response_data = {
                'success': True,
                'partner_id': partner.id,
                'partner_name': partner.user.username if partner.user else None,
                'total_contacts': total_contacts,
                'total_commission': float(commission),
                'status_code': status.HTTP_200_OK
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Partners.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Partner not found',
                'status_code': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e),
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)


# Partner Contact adding through excel




# class ContactImportAPIView(APIView):
#     def post(self, request):
#         # Debug print
#         print("Received import request with data:", request.data)
#
#         # Get user_id and file from request
#         user_id = request.data.get('user_id')
#         excel_file = request.FILES.get('excel_file')
#
#         if not user_id or not excel_file:
#             print("Missing required fields - user_id:", user_id, "excel_file:", bool(excel_file))
#             return Response({
#                 'success': False,
#                 'message': 'Both user_id and excel_file are required',
#                 'status_code': status.HTTP_400_BAD_REQUEST
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         # Get partner instance
#         try:
#             partner = Partners.objects.get(user_id=user_id)
#             print("Found partner:", partner.user.username)
#         except Partners.DoesNotExist:
#             print("Partner not found for user_id:", user_id)
#             return Response({
#                 'success': False,
#                 'message': 'Partner not found for the given user_id',
#                 'status_code': status.HTTP_404_NOT_FOUND
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         # Validate file extension
#         if not excel_file.name.endswith(('.xlsx', '.xls')):
#             print("Invalid file format:", excel_file.name)
#             return Response({
#                 'success': False,
#                 'message': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)',
#                 'status_code': status.HTTP_400_BAD_REQUEST
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             # Read Excel file
#             df = pd.read_excel(excel_file)
#             print("Excel file read successfully. Columns:", df.columns.tolist())
#
#             # Normalize column names
#             df.columns = [str(col).strip().lower() for col in df.columns]
#             print("Normalized columns:", df.columns.tolist())
#
#             # Define required columns
#             required_columns = {'name', 'email', 'mobile', 'company'}
#             available_columns = set(df.columns)
#
#             # Check for missing required columns
#             missing_columns = required_columns - available_columns
#             if missing_columns:
#                 print("Missing required columns:", missing_columns)
#                 return Response({
#                     'success': False,
#                     'message': f"Missing required columns: {', '.join(missing_columns)}",
#                     'required_columns': list(required_columns),
#                     'suggestion': 'Please download the sample file for reference',
#                     'status_code': status.HTTP_400_BAD_REQUEST
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             # Process each row
#             created_count = 0
#             updated_count = 0
#             skipped_count = 0
#             errors = []
#
#             for index, row in df.iterrows():
#                 try:
#                     # Get required fields
#                     name = str(row.get('name', '')).strip()
#                     email = str(row.get('email', '')).strip()
#                     mobile = str(row.get('mobile', '')).strip()
#                     company = str(row.get('company', '')).strip()
#
#                     # Skip if required fields are empty
#                     if not email or not company:
#                         skipped_count += 1
#                         errors.append(f"Row {index + 2}: Skipped - Missing email or company")
#                         continue
#
#                     # Get or create account
#                     account, _ = Accounts.objects.get_or_create(name=company)
#                     print(f"Processing row {index + 2}: {email} - {company}")
#
#                     # Prepare contact data
#                     contact_data = {
#                         'name': name if name else email.split('@')[0],
#                         'email': email,
#                         'mobile': mobile,
#                         'partner': partner,
#                         'created_by': partner.user,
#                         'status': 'data'
#                     }
#
#                     # Create or update contact
#                     contact, created = Contact.objects.update_or_create(
#                         email=email,
#                         defaults=contact_data
#                     )
#
#                     # Add account relationship
#                     if account not in contact.account.all():
#                         contact.account.add(account)
#
#                     if created:
#                         created_count += 1
#                     else:
#                         updated_count += 1
#
#                 except Exception as e:
#                     skipped_count += 1
#                     error_msg = f"Row {index + 2}: Error - {str(e)}"
#                     errors.append(error_msg)
#                     print(error_msg)
#
#             # Prepare response
#             response_data = {
#                 'success': True,
#                 'message': f"Import completed. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}",
#                 'created_count': created_count,
#                 'updated_count': updated_count,
#                 'skipped_count': skipped_count,
#                 'status_code': status.HTTP_200_OK
#             }
#
#             if errors:
#                 response_data['errors'] = errors[:10]  # Return first 10 errors to avoid huge response
#                 if len(errors) > 10:
#                     response_data['error_message'] = f"Showing first 10 of {len(errors)} errors"
#
#             print("Import completed:", response_data['message'])
#             return Response(response_data, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             print("Unexpected error during import:", str(e))
#             return Response({
#                 'success': False,
#                 'message': f"Error processing Excel file: {str(e)}",
#                 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#     def get(self, request):
#         # Sample file download endpoint
#         print("Received request for sample file")
#
#         # Create a simple Excel file in memory
#         from io import BytesIO
#         import pandas as pd
#
#         sample_data = {
#             'Name': ['John Doe', 'Jane Smith'],
#             'Email': ['john@example.com', 'jane@example.com'],
#             'Mobile': ['+1234567890', '+1987654321'],
#             'Company': ['ABC Corp', 'XYZ Inc']
#         }
#         df = pd.DataFrame(sample_data)
#
#         output = BytesIO()
#         writer = pd.ExcelWriter(output, engine='xlsxwriter')
#         df.to_excel(writer, sheet_name='Contacts', index=False)
#         writer.close()
#         output.seek(0)
#
#         response = HttpResponse(
#             output.getvalue(),
#             content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#         )
#         response['Content-Disposition'] = 'attachment; filename=contact_import_sample.xlsx'
#         return response


import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from pep_app.models import Partners, Contact, Accounts
from .tasks import bulk_validate_emails, validate_email
import io
import os


class ContactImportAPIView(APIView):
    def post(self, request):
        # Debug print
        print("Received import request with data:", request.data)

        # Get user_id and file from request
        user_id = request.data.get('user_id')
        excel_file = request.FILES.get('excel_file')
        validate_emails = request.data.get('validate_emails', True)  # Default to True

        if not user_id or not excel_file:
            print("Missing required fields - user_id:", user_id, "excel_file:", bool(excel_file))
            return Response({
                'success': False,
                'message': 'Both user_id and excel_file are required',
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get partner instance
        try:
            partner = Partners.objects.get(user_id=user_id)
            print("Found partner:", partner.user.username)
        except Partners.DoesNotExist:
            print("Partner not found for user_id:", user_id)
            return Response({
                'success': False,
                'message': 'Partner not found for the given user_id',
                'status_code': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate file extension
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            print("Invalid file format:", excel_file.name)
            return Response({
                'success': False,
                'message': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)',
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read Excel file
            df = pd.read_excel(excel_file)
            print("Excel file read successfully. Columns:", df.columns.tolist())

            # Normalize column names
            df.columns = [str(col).strip().lower() for col in df.columns]
            print("Normalized columns:", df.columns.tolist())

            # Define required columns
            required_columns = {'name', 'email', 'mobile', 'company'}
            available_columns = set(df.columns)

            # Check for missing required columns
            missing_columns = required_columns - available_columns
            if missing_columns:
                print("Missing required columns:", missing_columns)
                return Response({
                    'success': False,
                    'message': f"Missing required columns: {', '.join(missing_columns)}",
                    'required_columns': list(required_columns),
                    'suggestion': 'Please download the sample file for reference',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            # Process each row
            created_count = 0
            updated_count = 0
            skipped_count = 0
            errors = []
            contact_ids_for_validation = []

            for index, row in df.iterrows():
                try:
                    # Get required fields
                    name = str(row.get('name', '')).strip()
                    email = str(row.get('email', '')).strip()
                    mobile = str(row.get('mobile', '')).strip()
                    company = str(row.get('company', '')).strip()

                    # Skip if required fields are empty
                    if not email or not company:
                        skipped_count += 1
                        errors.append(f"Row {index + 2}: Skipped - Missing email or company")
                        continue

                    # Get or create account
                    account, _ = Accounts.objects.get_or_create(name=company)
                    print(f"Processing row {index + 2}: {email} - {company}")

                    # Prepare contact data
                    contact_data = {
                        'name': name if name else email.split('@')[0],
                        'email': email,
                        'mobile': mobile,
                        'partner': partner,
                        'created_by': partner.user,
                        'status': 'data'
                    }

                    # Create or update contact
                    contact, created = Contact.objects.update_or_create(
                        email=email,
                        defaults=contact_data
                    )

                    # Add account relationship
                    if account not in contact.account.all():
                        contact.account.add(account)

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # Add to list for email validation
                    contact_ids_for_validation.append(contact.id)

                except Exception as e:
                    skipped_count += 1
                    error_msg = f"Row {index + 2}: Error - {str(e)}"
                    errors.append(error_msg)
                    print(error_msg)

            # Trigger email validation as a background task if requested
            if validate_emails and contact_ids_for_validation:
                print(f"Scheduling email validation for {len(contact_ids_for_validation)} contacts")
                # Use the bulk task for efficiency
                if len(contact_ids_for_validation) > 1:
                    bulk_validate_emails.delay(contact_ids_for_validation)
                else:
                    validate_email.delay(contact_ids_for_validation[0])

            # Prepare response
            response_data = {
                'success': True,
                'message': f"Import completed. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}",
                'created_count': created_count,
                'updated_count': updated_count,
                'skipped_count': skipped_count,
                'email_validation': 'Scheduled' if validate_emails else 'Skipped',
                'status_code': status.HTTP_200_OK
            }

            if errors:
                response_data['errors'] = errors[:10]  # Return first 10 errors to avoid huge response
                if len(errors) > 10:
                    response_data['error_message'] = f"Showing first 10 of {len(errors)} errors"

            print("Import completed:", response_data['message'])
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print("Unexpected error during import:", str(e))
            return Response({
                'success': False,
                'message': f"Error processing Excel file: {str(e)}",
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        # Sample file download endpoint
        print("Received request for sample file")

        # Create a simple Excel file in memory
        from io import BytesIO
        import pandas as pd

        sample_data = {
            'Name': ['John Doe', 'Jane Smith'],
            'Email': ['john@example.com', 'jane@example.com'],
            'Mobile': ['+1234567890', '+1987654321'],
            'Company': ['ABC Corp', 'XYZ Inc']
        }
        df = pd.DataFrame(sample_data)

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Contacts', index=False)
        writer.close()
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=contact_import_sample.xlsx'
        return response


class ValidateEmailAPIView(APIView):
    """API endpoint to manually validate a single contact's email"""

    def post(self, request, contact_id):
        try:
            # Check if contact exists
            try:
                contact = Contact.objects.get(id=contact_id)
            except Contact.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Contact not found',
                    'status_code': status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            # Validate the email asynchronously
            task = validate_email.delay(contact_id)

            return Response({
                'success': True,
                'message': 'Email validation scheduled',
                'task_id': task.id,
                'contact_id': contact_id,
                'status_code': status.HTTP_202_ACCEPTED
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error scheduling email validation: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkValidateEmailsAPIView(APIView):
    """API endpoint to validate emails for multiple contacts"""

    def post(self, request):
        contact_ids = request.data.get('contact_ids', [])

        if not contact_ids:
            return Response({
                'success': False,
                'message': 'No contact IDs provided',
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate the existence of all contacts first
            existing_contact_ids = Contact.objects.filter(id__in=contact_ids).values_list('id', flat=True)
            missing_ids = set(contact_ids) - set(existing_contact_ids)

            if missing_ids:
                return Response({
                    'success': False,
                    'message': f'Some contacts not found: {missing_ids}',
                    'status_code': status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            # Schedule the bulk validation task
            task = bulk_validate_emails.delay(list(existing_contact_ids))

            return Response({
                'success': True,
                'message': f'Email validation scheduled for {len(existing_contact_ids)} contacts',
                'task_id': task.id,
                'contact_count': len(existing_contact_ids),
                'status_code': status.HTTP_202_ACCEPTED
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error scheduling bulk email validation: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)