import os
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.management import call_command
from datetime import datetime
import logging
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)
import subprocess
# Backup Function

@shared_task
def backup_database():
    """
    Task to create a backup of the database and send the backup link via email.
    It also deletes backups older than 4 weeks to prevent overloading the system.
    """
    # Set the path for the backup
    backup_dir = os.path.join(settings.BASE_DIR, 'media', 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Create a timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_filename = f"db_backup_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Example backup command for MySQL database
    command = f"/usr/bin/mysqldump --host={settings.DATABASES['default']['HOST']} --user={settings.DATABASES['default']['USER']} --password={settings.DATABASES['default']['PASSWORD']} {settings.DATABASES['default']['NAME']} > {backup_path}"

    try:
        # Delete backups older than 4 weeks (28 days)
        delete_old_backups(backup_dir)

        # Execute the backup command and capture the output
        result = subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        # Check if there was an error in the command
        if result.returncode != 0:
            raise Exception(f"Backup failed: {result.stderr.decode()}")

        # Check if the backup file was created and is not empty
        if os.path.getsize(backup_path) == 0:
            raise Exception(f"Backup failed: The file {backup_filename} is empty.")

        # Capture the current timestamp of the backup completion
        completed_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create the full URL for the backup file (include your domain name)
        backup_url = f"https://dash.brandexperts.ae/media/backups/{backup_filename}"

        # Prepare the email message
        subject = 'Database Backup Completed'
        message = (
            f'The database backup has been completed successfully on {completed_time}. '
            f'You can download the backup from the following link:\n\n{backup_url}\n\n'
        )
        from_email = settings.DEFAULT_FROM_EMAIL

        # Send the email with the log and error output
        send_mail(subject, message, from_email, [settings.BACKUP_NOTIFICATION_EMAIL])

        return f"Backup successful: {backup_path} at {completed_time} and email sent to {', '.join([settings.BACKUP_NOTIFICATION_EMAIL])}"

    except Exception as e:
        # In case of an error, return the error message and send the error email
        error_message = str(e)

        # Send email with error details for debugging
        subject = 'Database Backup Failed'
        message = (
            f'The database backup failed at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. '
            f'Error details:\n\n{error_message}'
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [settings.BACKUP_NOTIFICATION_EMAIL])

        return f"Backup failed: {error_message}"

def delete_old_backups(backup_dir):
    """
    Delete backup files older than 4 weeks (28 days).
    """
    # Calculate the date 4 weeks ago
    four_weeks_ago = datetime.now() - timedelta(weeks=4)

    try:
        # Loop through the files in the backup directory
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)

            # Only check .sql files for backup
            if filename.endswith('.sql'):
                # Get the file's last modified time
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                # If the file is older than 4 weeks, delete it
                if file_modified_time < four_weeks_ago:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Deleted old backup: {file_path}")
    except Exception as e:
        print(f"Error during cleanup of old backups: {str(e)}")

