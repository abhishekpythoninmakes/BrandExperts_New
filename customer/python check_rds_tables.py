import mysql.connector

# ======================================
# 🔗 RDS Connection Configuration
# ======================================
NEW_DB_HOST = "host"
NEW_DB_PORT = 3306
NEW_DB_USER = "username"
NEW_DB_PASSWORD = "password"
NEW_DB_NAME = "database name"

try:
    print("🔗 Connecting to AWS RDS...")
    conn = mysql.connector.connect(
        host=NEW_DB_HOST,
        port=NEW_DB_PORT,
        user=NEW_DB_USER,
        password=NEW_DB_PASSWORD,
        database=NEW_DB_NAME
    )

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()

    print("\n📋 Tables found in database:")
    if not tables:
        print("⚠️ No tables found — restore may have failed or wrong DB selected.")
    else:
        for (table_name,) in tables:
            print("✅", table_name)

    print(f"\nTotal tables: {len(tables)}")

except mysql.connector.Error as err:
    print(f"❌ Database error: {err}")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()
