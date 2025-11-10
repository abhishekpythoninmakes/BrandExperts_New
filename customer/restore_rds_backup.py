import os
import subprocess
import gzip
import sys

# ======================================
# 🧠 1. Configuration (edit these values)
# ======================================
MYSQL_PATH = r"D:\tools\mysql_dump\mysql-8.0.42-winx64\bin\mysql.exe"  # Path to mysql.exe

# --- 🔁 New AWS RDS connection details ---
NEW_DB_HOST = "host"
NEW_DB_PORT = 3306
NEW_DB_USER = "username"
NEW_DB_PASSWORD = "password"
NEW_DB_NAME = "database name"


# --- 📦 Path to your backup file (.sql or .gz) ---
BACKUP_FILE = r"D:\BExpertsNewProject\BrandExpertsEcommerce\BrandExperts_New\customer\db_backups\MYBE_backup_2025-06-10_11-58-37.sql.gz"

if not os.path.exists(BACKUP_FILE):
    print(f"❌ Backup file not found: {BACKUP_FILE}")
    sys.exit(1)


# ======================================
# ⚙️ 2. Decompress if gzipped
# ======================================
if BACKUP_FILE.endswith(".gz"):
    print("🗜️ Decompressing .gz backup file...")
    decompressed_file = BACKUP_FILE[:-3]  # remove .gz extension

    with gzip.open(BACKUP_FILE, "rb") as f_in:
        with open(decompressed_file, "wb") as f_out:
            f_out.write(f_in.read())

    print(f"✅ Decompressed SQL file: {decompressed_file}")
else:
    decompressed_file = BACKUP_FILE

# ======================================
# 🚀 3. Restore (undump) into new RDS
# ======================================
print(f"🚀 Restoring backup into new RDS: {NEW_DB_HOST}/{NEW_DB_NAME}")

try:
    command = [
        MYSQL_PATH,
        f"-h{NEW_DB_HOST}",
        f"-P{NEW_DB_PORT}",
        f"-u{NEW_DB_USER}",
        f"-p{NEW_DB_PASSWORD}",
        NEW_DB_NAME
    ]

    with open(decompressed_file, "r", encoding="utf-8") as f:
        process = subprocess.Popen(command, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"MySQL restore failed:\n{stderr.strip()}")

    print("🎉 Restore completed successfully! Your new RDS now has all data and structure.")
    print("🧭 Next step: Update your Django DATABASES setting to point to this new RDS.")
except Exception as e:
    print(f"❌ Error during restore: {e}")
