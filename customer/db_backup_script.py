import os
import subprocess
import datetime
import gzip
import shutil
import sys
import django

# ================================
# ⚙️ Setup Django environment
# ================================
PROJECT_ROOT = r"D:\BExpertsNewProject\BrandExpertsEcommerce\BrandExperts_New"
sys.path.append(PROJECT_ROOT)

# 👇 your actual settings file lives here:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrandExpertsEcommerce.settings')

django.setup()

from django.conf import settings

# ================================
# 🔧 Load database configuration
# ================================
db_config = settings.DATABASES['default']
DB_NAME = db_config['NAME']
DB_USER = db_config['USER']
DB_PASSWORD = db_config['PASSWORD']
DB_HOST = db_config['HOST']
DB_PORT = db_config['PORT']

# ================================
# 🛠️ Path to mysqldump.exe
# ================================
MYSQLDUMP_PATH = r'D:\tools\mysql_dump\mysql-8.0.42-winx64\bin\mysqldump.exe'

# ================================
# 🗂️ Backup directory
# ================================
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'db_backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
backup_filename = f'{DB_NAME}_backup_{timestamp}.sql'
backup_path = os.path.join(BACKUP_DIR, backup_filename)
compressed_backup_path = f'{backup_path}.gz'

try:
    print(f"🚀 Starting backup of database '{DB_NAME}'...")

    command = [
        MYSQLDUMP_PATH,
        f'-h{DB_HOST}',
        f'-P{DB_PORT}',
        f'-u{DB_USER}',
        f'-p{DB_PASSWORD}',
        '--single-transaction',
        '--skip-add-locks',
        '--no-autocommit',
        '--routines',
        '--triggers',
        '--events',
        '--set-gtid-purged=OFF',
        DB_NAME
    ]

    # Run backup
    with open(backup_path, 'w', encoding='utf-8') as f:
        process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE, text=True)
        _, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"mysqldump failed: {stderr.strip()}")

    print(f"✅ Database dump created at: {backup_path}")

    # Compress backup
    print("🗜️ Compressing backup file...")
    with open(backup_path, 'rb') as f_in:
        with gzip.open(compressed_backup_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    os.remove(backup_path)
    print(f"🎉 Backup completed successfully! Compressed file: {compressed_backup_path}")

except Exception as e:
    print(f"❌ Error during backup: {str(e)}")
    if os.path.exists(backup_path):
        os.remove(backup_path)
    if os.path.exists(compressed_backup_path):
        os.remove(compressed_backup_path)
