import os
import subprocess
import gzip
import shutil
import sys
import django

# ================================
# ⚙️ Setup Django environment
# ================================
PROJECT_ROOT = r"D:\BExpertsNewProject\BrandExpertsEcommerce\BrandExperts_New"
sys.path.append(PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrandExpertsEcommerce.settings')
django.setup()

from django.conf import settings

# ================================
# 🔧 Load DB config from Django
# ================================
db_config = settings.DATABASES['default']
DB_NAME = db_config['NAME']
DB_USER = db_config['USER']
DB_PASSWORD = db_config['PASSWORD']
DB_HOST = db_config['HOST']
DB_PORT = db_config['PORT']

# ================================
# 🛠️ Path to MySQL client
# ================================
MYSQL_PATH = r'D:\tools\mysql_dump\mysql-8.0.42-winx64\bin\mysql.exe'

# ================================
# 📦 Restore file configuration
# ================================
# Example: 'db_backups/mydb_backup_2025-11-08_15-30-00.sql.gz'
BACKUP_FILE = r"D:\BExpertsNewProject\BrandExpertsEcommerce\BrandExperts_New\db_backups\MYBE_backup_2025-11-08_17-32-44.sql.gz"

# ================================
# 🧩 Prepare file
# ================================
if not os.path.exists(BACKUP_FILE):
    raise FileNotFoundError(f"Backup file not found: {BACKUP_FILE}")

# If the file is compressed (.gz), decompress first
if BACKUP_FILE.endswith(".gz"):
    print("🔓 Decompressing backup file...")
    decompressed_file = BACKUP_FILE.replace(".gz", "")
    with gzip.open(BACKUP_FILE, 'rb') as f_in:
        with open(decompressed_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
else:
    decompressed_file = BACKUP_FILE

# ================================
# 🚀 Restore process
# ================================
try:
    print(f"🚀 Restoring database '{DB_NAME}' on RDS host '{DB_HOST}'...")

    # Construct mysql restore command
    command = [
        MYSQL_PATH,
        f'-h{DB_HOST}',
        f'-P{DB_PORT}',
        f'-u{DB_USER}',
        f'-p{DB_PASSWORD}',
        DB_NAME
    ]

    with open(decompressed_file, 'r', encoding='utf-8') as f:
        process = subprocess.Popen(command, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

    if process.returncode == 0:
        print("✅ Database restored successfully to AWS RDS!")
    else:
        raise Exception(f"MySQL restore failed: {stderr.strip()}")

finally:
    # Optionally remove decompressed file
    if decompressed_file != BACKUP_FILE and os.path.exists(decompressed_file):
        os.remove(decompressed_file)
        print("🧹 Cleaned up temporary decompressed file.")

