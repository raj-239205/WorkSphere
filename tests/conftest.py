import pytest
import os
import sys

# Add project root to sys.path to allow clean imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db_manager import db
from config.testing import TestingConfig
from services.user_service import UserService
from services.employee_service import EmployeeService
from services.department_service import DepartmentService

@pytest.fixture(scope='session')
def app():
    # Force testing configuration
    app = create_app(TestingConfig)
    return app

@pytest.fixture(scope='function')
def session(app):
    """Establishes application context and resets database tables for each test function."""
    with app.app_context():
        db.create_all()
        
        # Instantiate services for seeding
        dept_service = DepartmentService()
        user_service = UserService()
        employee_service = EmployeeService()
        
        # Seed departments
        admin_dept = dept_service.create_department("Administration", "Alok Verma")
        se_dept = dept_service.create_department("Software Engineering", "Amit Patel")
        hr_dept = dept_service.create_department("Human Resources", "Sudhanshu Sharma")
        dept_service.create_department("Sales & Marketing", "Vikram Malhotra")
        
        # Seed users
        user_service.create_user("admin", "Admin", "admin123")
        
        # Seed HR profile
        hr_emp = employee_service.create_employee(
            name="Sudhanshu Sharma",
            email="sudhanshu@worksphere.com",
            phone="9876543210",
            department_id=hr_dept.department_id,
            salary=95000.0,
            designation="HR Manager",
            username="hr_user",
            password="hr1234"
        )
        
        # Manually verify/set polymorphic JTI role
        from models.user import User
        user = db.session.get(User, hr_emp.user_id)
        user.role = 'HR'
        db.session.commit()
        
        # Seed Employee profile
        employee_service.create_employee(
            name="Rajveer Choudhary",
            email="rajveer@worksphere.com",
            phone="1234567890",
            department_id=se_dept.department_id,
            salary=35000.0,
            designation="Software Engineering Intern",
            username="emp_user",
            password="emp123"
        )
        
        yield db.session
        
        db.session.remove()
        db.drop_all()
