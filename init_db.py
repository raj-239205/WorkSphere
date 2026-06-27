from app import create_app
from database.db_manager import db
from services.department_service import DepartmentService
from services.employee_service import EmployeeService
from services.user_service import UserService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from datetime import datetime, timedelta

def create_default_admin():
    """Seeds the default Admin user credentials if not present."""
    from services.user_service import UserService
    user_service = UserService()
    try:
        admin = user_service.create_user("admin", "Admin", "admin123")
        print("Seeded default Admin user.")
        return admin
    except ValueError as e:
        print(f"Default Admin user already exists: {e}")
        return user_service.get_user_by_username("admin")

def create_default_hr(hr_dept_id):
    """Seeds the default HR employee and user credentials if not present."""
    from services.employee_service import EmployeeService
    from services.user_service import UserService
    employee_service = EmployeeService()
    user_service = UserService()
    try:
        hr_emp = employee_service.create_employee(
            name="Sudhanshu Sharma",
            email="hr@worksphere.com",
            phone="9876543210",
            department_id=hr_dept_id,
            salary=95000.0,
            designation="HR Manager",
            username="hr_user",
            password="hr1234"
        )
        with db.session.no_autoflush:
            user = user_service.get_user_by_id(hr_emp.user_id)
            if user:
                user.role = 'HR'
                db.session.add(user)
                db.session.commit()
        print("Seeded default HR user.")
        return hr_emp
    except Exception as e:
        print(f"Default HR user already exists/skipped: {e}")
        return employee_service.get_employee_by_email("hr@worksphere.com")

def seed_data():
    print("Seeding database using SQLAlchemy ORM...")
    
    # 1. Seed Departments
    dept_service = DepartmentService()
    departments = [
        ("Administration", "Alok Verma"),
        ("Software Engineering", "Amit Patel"),
        ("Human Resources", "Sudhanshu Sharma"),
        ("Sales & Marketing", "Vikram Malhotra")
    ]
    
    dept_map = {}
    for name, mgr in departments:
        try:
            dept = dept_service.create_department(name, mgr)
            dept_map[name] = dept.department_id
            print(f"Seeded Department: {name}")
        except ValueError as e:
            # Fallback/Already exists check
            dept = dept_service.get_department_by_name(name)
            if dept:
                dept_map[name] = dept.department_id
            print(f"Department exists: {name}")

    # 2. Seed Users & Employees
    # Seed Default Admin
    create_default_admin()
    
    # Seed Default HR
    hr_dept_id = dept_map.get("Human Resources")
    hr_emp = create_default_hr(hr_dept_id)
    
    emp_map = {}
    if hr_emp:
        emp_map["hr@worksphere.com"] = hr_emp.user_id
        
    employee_service = EmployeeService()
    user_service = UserService()
    
    # Seed other Employees (excluding HR)
    employees_to_seed = [
        # (name, email, phone, department, salary, designation, username, password, role)
        ("Rajveer Choudhary", "rajveer@worksphere.com", "1234567890", "Software Engineering", 35000.0, "Software Engineering Intern", "emp_user", "emp123", "Employee"),
        ("Amit Patel", "amit@worksphere.com", "5551234567", "Software Engineering", 120000.0, "Lead Software Architect", "amit", "WorkSphere123", "Employee"),
        ("Neha Sharma", "neha@worksphere.com", "4445556666", "Software Engineering", 85000.0, "Senior UI Designer", "neha", "WorkSphere123", "Employee"),
        ("Vikram Malhotra", "vikram@worksphere.com", "7778889999", "Sales & Marketing", 110000.0, "VP of Sales", "vikram", "WorkSphere123", "Employee"),
        ("Alok Verma", "alok@worksphere.com", "8889990000", "Administration", 80000.0, "Operations Specialist", "alok", "WorkSphere123", "Employee")
    ]
    
    for name, email, phone, dept_name, salary, desig, uname, passwd, role in employees_to_seed:
        try:
            dept_id = dept_map.get(dept_name)
            emp = employee_service.create_employee(
                name=name,
                email=email,
                phone=phone,
                department_id=dept_id,
                salary=salary,
                designation=desig,
                username=uname,
                password=passwd
            )
            # Update role to 'HR' or 'Admin' if applicable (since create_employee defaults to role 'Employee')
            if role != 'Employee':
                with db.session.no_autoflush:
                    user = user_service.get_user_by_id(emp.user_id)
                    if user:
                        user.role = role
                        db.session.add(user)
                        db.session.commit()
            
            emp_map[email] = emp.user_id
            print(f"Seeded Employee: {name} as {role}")
        except Exception as e:
            emp = employee_service.get_employee_by_email(email)
            if emp:
                emp_map[email] = emp.user_id
            print(f"Employee seeding skipped/exists for {name}: {e}")

    # 3. Seed Attendance Records (past 3 days)
    attendance_service = AttendanceService()
    today = datetime.now()
    
    print("Seeding dummy attendance records...")
    for i in range(1, 4):
        date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        for email, emp_id in emp_map.items():
            # Present on most days, absent on some
            status = 'Present' if (emp_id % 2 == 0 or i != 2) else 'Absent'
            try:
                attendance_service.mark_attendance(emp_id, date_str, status)
            except Exception as e:
                print(f"Attendance seed skipped: {e}")

    # 4. Seed a Leave request for Rajveer
    leave_service = LeaveService()
    try:
        rajveer_id = emp_map.get("rajveer@worksphere.com")
        if rajveer_id:
            start_leave = (today + timedelta(days=2)).strftime('%Y-%m-%d')
            end_leave = (today + timedelta(days=5)).strftime('%Y-%m-%d')
            leave_service.apply_leave(
                emp_id=rajveer_id,
                reason="Semester end exam preparation leave",
                start_date=start_leave,
                end_date=end_leave
            )
            print("Seeded pending leave request.")
    except Exception as e:
        print(f"Leave seeding skipped: {e}")

    print("Database seeding completed successfully.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_data()
