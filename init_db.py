import sqlite3
import os
from config import Config
from database.db import DB
from services.user_service import UserService

def initialize_database():
    print("Initializing Database...")
    db_path = Config.DATABASE_PATH
    db_dir = os.path.dirname(db_path)
    
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created directory: {db_dir}")

    # Connect directly to perform schema migrations
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Departments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL UNIQUE,
            manager_name TEXT
        );
    """)
    
    # 2. Employees Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            department_id INTEGER,
            salary REAL DEFAULT 0.0,
            designation TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
        );
    """)
    
    # 3. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'HR', 'Employee')),
            emp_id INTEGER UNIQUE,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE SET NULL
        );
    """)
    
    # 4. Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Leave')),
            UNIQUE(emp_id, date),
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
        );
    """)
    
    # 5. Leaves Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            reason TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
        );
    """)
    
    # Create Indexes on Foreign Keys for Join Optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_employee ON users(emp_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance(emp_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leaves_employee ON leaves(emp_id);")
    
    conn.commit()
    conn.close()
    print("Database tables and performance indexes created successfully.")

def seed_data():
    print("Seeding default data...")
    
    # Seed Departments
    departments = [
        ("Administration", "Alok Verma"),
        ("Software Engineering", "Amit Patel"),
        ("Human Resources", "Sudhanshu Sharma"),
        ("Sales & Marketing", "Vikram Malhotra")
    ]
    
    with DB.session() as conn:
        for dept_name, mgr in departments:
            try:
                conn.execute(
                    "INSERT INTO departments (department_name, manager_name) VALUES (?, ?)", 
                    (dept_name, mgr)
                )
            except sqlite3.IntegrityError:
                pass # Already seeded
                
    # Get department IDs
    depts = DB.execute_query("SELECT department_id, department_name FROM departments", fetch_all=True)
    dept_map = {d['department_name']: d['department_id'] for d in depts}
    
    # Seed Employees
    employees = [
        ("Sudhanshu Sharma", "sudhanshu@worksphere.com", "9876543210", dept_map["Human Resources"], 95000.0, "HR Manager"),
        ("Rajveer Choudhary", "rajveer@worksphere.com", "1234567890", dept_map["Software Engineering"], 35000.0, "Software Engineering Intern"),
        ("Amit Patel", "amit@worksphere.com", "5551234567", dept_map["Software Engineering"], 120000.0, "Lead Software Architect"),
        ("Neha Sharma", "neha@worksphere.com", "4445556666", dept_map["Software Engineering"], 85000.0, "Senior UI Designer"),
        ("Vikram Malhotra", "vikram@worksphere.com", "7778889999", dept_map["Sales & Marketing"], 110000.0, "VP of Sales"),
        ("Alok Verma", "alok@worksphere.com", "8889990000", dept_map["Administration"], 80000.0, "Operations Specialist")
    ]
    
    with DB.session() as conn:
        for name, email, phone, dept_id, salary, desig in employees:
            try:
                conn.execute("""
                    INSERT INTO employees (name, email, phone, department_id, salary, designation)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, email, phone, dept_id, salary, desig))
            except sqlite3.IntegrityError:
                pass # Already seeded
                
    # Get employee IDs
    emps = DB.execute_query("SELECT emp_id, email FROM employees", fetch_all=True)
    emp_map = {e['email']: e['emp_id'] for e in emps}
    
    # Seed Users
    # Admin is not linked to an employee
    try:
        UserService.create_user("admin", "admin123", "Admin")
        print("Admin user seeded.")
    except ValueError as e:
        print(f"Admin seeding skipped: {e}")
        
    # HR User linked to Sudhanshu Sharma
    try:
        UserService.create_user("hr_user", "hr123", "HR", emp_id=emp_map["sudhanshu@worksphere.com"])
        print("HR user seeded.")
    except ValueError as e:
        print(f"HR user seeding skipped: {e}")
        
    # Employee User linked to Rajveer Choudhary
    try:
        UserService.create_user("emp_user", "emp123", "Employee", emp_id=emp_map["rajveer@worksphere.com"])
        print("Employee user seeded.")
    except ValueError as e:
        print(f"Employee user seeding skipped: {e}")

    # Seed some dummy attendance & leaves for demo/analytics
    try:
        # Employees are Present for last 3 days
        from datetime import datetime, timedelta
        today = datetime.now()
        with DB.session() as conn:
            for i in range(1, 4):
                date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                for email, emp_id in emp_map.items():
                    # Seed random-ish attendance
                    status = 'Present' if (emp_id % 2 == 0 or i != 2) else 'Absent'
                    try:
                        conn.execute(
                            "INSERT INTO attendance (emp_id, date, status) VALUES (?, ?, ?)",
                            (emp_id, date_str, status)
                        )
                    except sqlite3.IntegrityError:
                        pass
                        
            # Seed a pending leave for Rajveer Choudhary
            start_leave = (today + timedelta(days=2)).strftime('%Y-%m-%d')
            end_leave = (today + timedelta(days=5)).strftime('%Y-%m-%d')
            try:
                conn.execute("""
                    INSERT INTO leaves (emp_id, reason, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, 'Pending')
                """, (emp_map["rajveer@worksphere.com"], "Semester end exam preparation leave", start_leave, end_leave))
            except sqlite3.IntegrityError:
                pass
        print("Dummy attendance and leave records seeded.")
    except Exception as e:
        print(f"Dummy data seeding failed: {e}")
        
    print("Seeding completed successfully.")

if __name__ == "__main__":
    initialize_database()
    seed_data()
