import os
import subprocess
import datetime
import gzip
import shutil

# Database connection details


# Path to mysqldump.exe (update if needed)
MYSQLDUMP_PATH = r'D:\tools\mysql_dump\mysql-8.0.42-winx64\bin\mysqldump.exe'

# Backup directory configuration
BACKUP_DIR = 'db_backups'
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# Generate timestamp for filename
timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
backup_filename = f'{DB_NAME}_backup_{timestamp}.sql'
backup_path = os.path.join(BACKUP_DIR, backup_filename)
compressed_backup_path = f'{backup_path}.gz'

try:
    print(f"Starting backup of database {DB_NAME}...")

    # Run mysqldump command
    command = [
        MYSQLDUMP_PATH,
        '--login-path=backupdb',
        f'-h{DB_HOST}',
        '--single-transaction',
        '--skip-add-locks',  # <-- Add this
        '--no-autocommit',  # <-- Add this
        '--routines',
        '--triggers',
        '--events',
        '--set-gtid-purged=OFF',
        DB_NAME
    ]

    with open(backup_path, 'w') as f:
        process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE)
        _, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"mysqldump failed: {stderr.decode('utf-8')}")

    print(f"Database dumped to {backup_path}")

    # Compress the backup file
    print("Compressing backup file...")
    with open(backup_path, 'rb') as f_in:
        with gzip.open(compressed_backup_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Remove the uncompressed file
    os.remove(backup_path)

    print(f"Backup completed successfully! Compressed backup saved to {compressed_backup_path}")

except Exception as e:
    print(f"Error during backup: {str(e)}")
    # Clean up if something went wrong
    if os.path.exists(backup_path):
        os.remove(backup_path)
    if os.path.exists(compressed_backup_path):
        os.remove(compressed_backup_path)
