import os
import sys
import sqlite3
from datetime import datetime
from app import create_app
from database.db_manager import db

def migrate():
    # 1. Validate environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        sys.exit(1)

    print("Starting SQLite to PostgreSQL migration...")
    
    # 2. Initialize Flask App and Database schemas in PostgreSQL
    app = create_app()
    with app.app_context():
        print("Creating table schemas in PostgreSQL...")
        db.create_all()
        print("Schemas initialized successfully.")

    # 3. Connect to source SQLite database
    sqlite_db_path = os.environ.get('SQLITE_DB_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'erp.db'))
    if not os.path.exists(sqlite_db_path):
        print(f"ERROR: SQLite database file not found at {sqlite_db_path}")
        sys.exit(1)

    print(f"Connecting to SQLite source: {sqlite_db_path}")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # 4. Connect to destination PostgreSQL database using psycopg2
    print("Connecting to PostgreSQL destination...")
    import psycopg2
    # Sanitize schema for psycopg2
    conn_url = database_url
    if conn_url.startswith("postgres://"):
        conn_url = conn_url.replace("postgres://", "postgresql://", 1)
    
    pg_conn = psycopg2.connect(conn_url)
    pg_cursor = pg_conn.cursor()

    # Tables to migrate in correct dependency order
    tables = [
        {
            "name": "departments",
            "columns": ["department_id", "department_name", "manager_name", "is_active"],
            "pk": "department_id"
        },
        {
            "name": "users",
            "columns": ["user_id", "username", "password", "role", "is_active"],
            "pk": "user_id"
        },
        {
            "name": "employees",
            "columns": ["user_id", "name", "email", "phone", "department_id", "salary", "designation"],
            "pk": "user_id"
        },
        {
            "name": "attendance",
            "columns": ["attendance_id", "emp_id", "date", "status", "is_active"],
            "pk": "attendance_id"
        },
        {
            "name": "leaves",
            "columns": ["leave_id", "emp_id", "reason", "start_date", "end_date", "status", "is_active"],
            "pk": "leave_id"
        },
        {
            "name": "activity_logs",
            "columns": ["log_id", "user_id", "action_type", "timestamp", "ip_address", "old_value", "new_value"],
            "pk": "log_id"
        }
    ]

    try:
        for table in tables:
            tname = table["name"]
            cols = table["columns"]
            pk = table["pk"]
            
            print(f"\nMigrating table: {tname}...")
            
            # Fetch all rows from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {tname}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"No records found in SQLite table {tname}. Skipping copy.")
                continue

            print(f"Found {len(rows)} records in SQLite. Inserting into PostgreSQL...")
            
            # Clear target table in PostgreSQL (cascade to avoid foreign key blocks)
            # Use TRUNCATE for quick cleanup if needed, but since it is a migration of existing data, 
            # we delete to overwrite existing seed values.
            pg_cursor.execute(f"DELETE FROM {tname} CASCADE")
            
            # Build placeholders
            col_list = ", ".join(cols)
            val_placeholders = ", ".join(["%s"] * len(cols))
            insert_query = f"INSERT INTO {tname} ({col_list}) VALUES ({val_placeholders})"
            
            for row in rows:
                # Extract values in correct column order
                values = []
                for col in cols:
                    val = row[col]
                    # Handle boolean conversion
                    if col in ["is_active"]:
                        val = bool(val) if val is not None else True
                    values.append(val)
                
                pg_cursor.execute(insert_query, values)
            
            pg_conn.commit()
            print(f"Successfully migrated {len(rows)} rows to PostgreSQL table {tname}.")

            # Update serial sequence to prevent nextval() primary key collisions
            if tname not in ["employees"]: # employees table PK is user_id, which is tied to the users sequence
                print(f"Updating sequence for table: {tname}...")
                seq_query = f"SELECT setval(pg_get_serial_sequence('{tname}', '{pk}'), coalesce(max({pk}), 1)) FROM {tname}"
                pg_cursor.execute(seq_query)
                pg_conn.commit()

        print("\nAll tables migrated successfully!")

    except Exception as e:
        pg_conn.rollback()
        print(f"\nFATAL ERROR during migration: {e}")
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    migrate()
