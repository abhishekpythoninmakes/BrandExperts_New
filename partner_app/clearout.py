import requests
import json
import re
import time


def is_valid_email(email):
    """
    Validate email format using regex.
    Returns True if the email is valid, otherwise False.
    """
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)


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
        print(f"Sending request to Clearout API for email: {email}")
        response = requests.post(url, headers=headers, json=payload)

        # Debugging: Print raw response details
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"Parsed JSON Response: {json.dumps(result, indent=4)}")
            return result.get('data', {})
        else:
            error_message = f"Error verifying email {email}: {response.status_code} - {response.text}"
            print(error_message)
            return {"status": "Unknown", "sub_status": "API Error", "error": response.text}
    except Exception as e:
        error_message = f"Exception during email verification for {email}: {str(e)}"
        print(error_message)
        return {"status": "Unknown", "sub_status": "Exception", "error": str(e)}


if __name__ == "__main__":
    # Test cases
    test_emails = [
        "test@example.com",  # Valid email format
        "invalid-email@",  # Invalid email format
        "nonexistent@domain.xyz",  # Non-existent domain
        "",  # Empty string
        None  # None value
    ]

    results = {}

    for email in test_emails:
        print(f"\n=== Testing Email: {email} ===")

        # Skip invalid or None values early
        if not email or not is_valid_email(email):
            print(f"Skipping invalid email: {email}")
            results[email] = {"status": "Invalid", "sub_status": "Invalid Format"}
            continue

        # Add a small delay to avoid rate limiting
        time.sleep(1)  # Delay of 1 second

        # Verify the email
        results[email] = verify_email_with_clearout(email)

    print("\n=== Final Results ===")
    for email, result in results.items():
        print(f"Email: {email}")
        print(f"Result: {json.dumps(result, indent=4)}")