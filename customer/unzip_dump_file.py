import gzip
import shutil

with gzip.open('db_backups/MYBE_backup_2025-06-10_11-58-37.sql.gz', 'rb') as f_in:
    with open('restored_backup.sql', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)