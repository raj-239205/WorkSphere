import pytest
from utils.security import SecurityContext, check_permission
from exceptions.custom_exceptions import UnauthorizedAccessException
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.user_service import UserService
from services.analytics_service import AnalyticsService
from services.report_service import ReportService
from flask import session
import json

def test_service_layer_direct_calls_rbac(session):
    employee_service = EmployeeService()
    department_service = DepartmentService()
    user_service = UserService()
    attendance_service = AttendanceService()
    leave_service = LeaveService()
    analytics_service = AnalyticsService()
    report_service = ReportService()

    # 1. Admin direct calls should all succeed
    with SecurityContext(user_id=1, username="admin", role="Admin"):
        assert employee_service.get_all_employees() is not None
        assert department_service.get_all_departments() is not None
        assert user_service.get_all_users() is not None

    # 2. HR direct calls
    with SecurityContext(user_id=2, username="hr_user", role="HR"):
        # HR can view employees and departments
        assert employee_service.get_all_employees() is not None
        assert department_service.get_all_departments() is not None
        
        # HR cannot create/edit/delete departments
        with pytest.raises(UnauthorizedAccessException):
            department_service.create_department("Marketing", "Vikram")
            
        with pytest.raises(UnauthorizedAccessException):
            department_service.update_department(1, "Marketing New", "Vikram")
            
        with pytest.raises(UnauthorizedAccessException):
            department_service.delete_department(1)
            
        # HR cannot manage users
        with pytest.raises(UnauthorizedAccessException):
            user_service.get_all_users()
            
        with pytest.raises(UnauthorizedAccessException):
            user_service.create_user("temp_user", "Employee")

    # 3. Employee direct calls
    with SecurityContext(user_id=3, username="emp_user", role="Employee"):
        # Employees cannot access management lists
        with pytest.raises(UnauthorizedAccessException):
            employee_service.get_all_employees()
            
        with pytest.raises(UnauthorizedAccessException):
            department_service.get_all_departments()
            
        # Employee can only view own profile
        assert employee_service.get_employee_by_id(3) is not None
        with pytest.raises(UnauthorizedAccessException):
            employee_service.get_employee_by_id(2) # cannot view HR profile
            
        # Employee can only view own attendance
        assert attendance_service.get_attendance_records(emp_id=3) == []
        with pytest.raises(UnauthorizedAccessException):
            attendance_service.get_attendance_records(emp_id=2) # cannot view HR attendance

def test_web_routes_rbac(session, app):
    client = app.test_client()

    # 1. Test Employee access to protected management routes (should return 403)
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['username'] = 'emp_user'
        sess['role'] = 'Employee'
        
    response = client.get('/departments')
    assert response.status_code == 403
    
    response = client.get('/employees')
    assert response.status_code == 403
    
    response = client.get('/dashboard/audit-logs')
    assert response.status_code == 403

    # 2. Test HR access to Department modifications & Users/Roles (should return 403)
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = 'hr_user'
        sess['role'] = 'HR'
        
    response = client.get('/department/add')
    assert response.status_code == 403
    
    response = client.post('/department/delete/1')
    assert response.status_code == 403
    
    response = client.get('/dashboard/audit-logs')
    assert response.status_code == 403

def test_rest_apis_rbac(session, app):
    client = app.test_client()

    # 1. Login as Employee to get access token
    login_data = {"username": "emp_user", "password": "emp123"}
    resp = client.post('/api/v1/auth/login', json=login_data)
    assert resp.status_code == 200
    token = resp.get_json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Employees cannot access corporate employee list
    resp = client.get('/api/v1/employees', headers=headers)
    assert resp.status_code == 403

    # 3. Employees cannot view other employee details
    resp = client.get('/api/v1/employees/2', headers=headers) # ID 2 is HR
    assert resp.status_code == 403

    # 4. Employees can access own details
    resp = client.get('/api/v1/employees/3', headers=headers) # ID 3 is self
    assert resp.status_code == 200

    # 5. Employees cannot modify departments
    resp = client.post('/api/v1/departments', json={"department_name": "QA", "manager_name": "John"}, headers=headers)
    assert resp.status_code == 403
