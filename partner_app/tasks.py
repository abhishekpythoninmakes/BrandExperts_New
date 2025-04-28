from celery import shared_task
from django.db import transaction
import re
import requests
import time
import logging

logger = logging.getLogger(__name__)


@shared_task
def validate_email(contact_id):
    """
    Validate a single contact's email using Clearout API and update email_deliverability
    """
    # Import here to avoid circular imports
    from pep_app.models import Contact

    try:
        contact = Contact.objects.get(id=contact_id)

        # Skip if no email or already validated
        if not contact.email:
            contact.email_deliverability = "No email provided"
            contact.save(update_fields=['email_deliverability'])
            return "No email provided"

        # Basic email format validation
        if not is_valid_email_format(contact.email):
            contact.email_deliverability = "Invalid email format"
            contact.save(update_fields=['email_deliverability'])
            return "Invalid email format"

        # Verify with Clearout API
        verification_result = verify_email_with_clearout(contact.email)

        # Update contact with readable verification result
        reason = get_readable_verification_result(verification_result)
        #contact.email_deliverability = reason
        contact.save(update_fields=['email_deliverability'])

        return reason

    except Exception as e:
        logger.error(f"Error validating email for contact {contact_id}: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def bulk_validate_emails(contact_ids):
    """
    Validate multiple contacts' emails in bulk
    """
    results = {}
    for contact_id in contact_ids:
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)
        results[contact_id] = validate_email(contact_id)

    return results


def is_valid_email_format(email):
    """
    Validate email format using regex.
    Returns True if the email is valid, otherwise False.
    """
    if not email:
        return False
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(regex, email))


def verify_email_with_clearout(email):
    """
    Verify an email address using Clearout API
    Returns the verification result as a JSON object
    """
    api_token = "d76a021401e30d309b555852abc93f8d:a90554ff4db286085eed5b66a5eb611f70e4c474c37298cc6fad8a156451687d"
    url = "https://api.clearout.io/v2/email_verify/instant"

    headers = {
        "Authorization": api_token,
        "Content-Type": "application/json"
    }

    payload = {
        "email": email
    }

    try:
        logger.info(f"Sending request to Clearout API for email: {email}")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result.get('data', {})
        else:
            error_message = f"API Error ({response.status_code}): {response.text}"
            logger.error(error_message)
            return {"status": "Unknown", "sub_status": "API Error", "error": response.text}
    except Exception as e:
        error_message = f"Exception during email verification: {str(e)}"
        logger.error(error_message)
        return {"status": "Unknown", "sub_status": "Exception", "error": str(e)}


def get_readable_verification_result(verification_result):
    """
    Convert verification result to human-readable format
    """
    status = verification_result.get("status", "Unknown")

    if status == "valid":
        return "Email is valid and deliverable"

    elif status == "invalid":
        sub_status = verification_result.get("sub_status", {})
        desc = sub_status.get("desc", "Unknown reason")
        ai_verdict = verification_result.get("ai_verdict", "")

        reason = f"Invalid email: {desc}"
        if ai_verdict:
            reason += f". {ai_verdict}"

        return reason

    elif status == "Unknown":
        error = verification_result.get("error", "Unknown error")
        sub_status = verification_result.get("sub_status", "Unknown")

        if sub_status == "Invalid Format":
            return "Invalid email format"
        else:
            return f"Verification failed: {sub_status}. {error}"

    else:
        return f"Email status: {status}. Unable to determine deliverability."