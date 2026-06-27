import pytest
from datetime import date, timedelta
from services.user_service import UserService
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from services.leave_service import LeaveService
from models.leave import LeaveRequest as Leave
from exceptions.custom_exceptions import LeaveValidationException

def test_user_authentication(session):
    user_service = UserService()
    # Admin authentication
    admin = user_service.authenticate_user("admin", "admin123")
    assert admin is not None
    assert admin.role == "Admin"
    
    # HR User authentication
    hr = user_service.authenticate_user("hr_user", "hr1234")
    assert hr is not None
    assert hr.role == "HR"
    
    # Employee authentication
    emp = user_service.authenticate_user("emp_user", "emp123")
    assert emp is not None
    assert emp.role == "Employee"

def test_employee_loading(session):
    employee_service = EmployeeService()
    employees = employee_service.get_all_employees()
    assert len(employees) >= 2
    
    names = [e.name for e in employees]
    assert "Rajveer Choudhary" in names
    assert "Sudhanshu Sharma" in names

def test_department_loading(session):
    department_service = DepartmentService()
    depts = department_service.get_all_departments()
    assert len(depts) == 4
    
    dept_names = [d.department_name for d in depts]
    assert "Software Engineering" in dept_names
    assert "Human Resources" in dept_names

def test_leave_validations(session):
    today_str = date.today().strftime('%Y-%m-%d')
    past_str = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
    future_str = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
    far_future_str = "20266-01-01"
    
    # 1. Test valid leave model
    valid_leave = Leave(emp_id=1, reason="Test", start_date=today_str, end_date=future_str)
    assert len(valid_leave.validate()) == 0
    
    # 2. Test past date rejection
    past_leave = Leave(emp_id=1, reason="Test", start_date=past_str, end_date=future_str)
    errors = past_leave.validate()
    assert 'start_date' in errors
    
    # 3. Test end date before start date
    reversed_leave = Leave(emp_id=1, reason="Test", start_date=future_str, end_date=today_str)
    errors = reversed_leave.validate()
    assert 'end_date' in errors

    # 4. Test invalid year length
    bad_year_leave = Leave(emp_id=1, reason="Test", start_date=far_future_str, end_date=future_str)
    errors = bad_year_leave.validate()
    assert 'start_date' in errors

def test_overlapping_leaves(session):
    employee_service = EmployeeService()
    leave_service = LeaveService()
    
    employees = employee_service.get_all_employees()
    emp_map = {e.email: e.user_id for e in employees}
    rajveer_id = emp_map["rajveer@worksphere.com"]
    
    # Apply first leave
    today = date.today()
    start1 = (today + timedelta(days=2)).strftime('%Y-%m-%d')
    end1 = (today + timedelta(days=5)).strftime('%Y-%m-%d')
    leave_service.apply_leave(rajveer_id, "Seeded exam leave", start1, end1)
    
    # Try overlapping leave range from today+3 to today+4
    overlapping_start = (today + timedelta(days=3)).strftime('%Y-%m-%d')
    overlapping_end = (today + timedelta(days=4)).strftime('%Y-%m-%d')
    
    with pytest.raises(LeaveValidationException):
        leave_service.apply_leave(
            emp_id=rajveer_id,
            reason="Overlapping exam preparation",
            start_date=overlapping_start,
            end_date=overlapping_end
        )

def test_model_properties_and_fallback(session):
    from models.department import Department
    from models.user import Employee
    from models.attendance import Attendance
    from services.analytics_service import AnalyticsService
    
    # 1. Department employee count
    dept = Department.query.filter_by(department_name="Software Engineering").first()
    assert dept is not None
    assert dept.employee_count >= 1
    
    # 2. Employee department name
    emp = Employee.query.filter_by(email="rajveer@worksphere.com").first()
    assert emp is not None
    assert emp.department_name == "Software Engineering"
    
    # 3. Attendance properties
    att = Attendance(emp_id=emp.user_id, date="2026-06-19", status="Present")
    session.add(att)
    session.commit()
    
    assert att.employee_name == "Rajveer Choudhary"
    assert att.department_name == "Software Engineering"
    
    # 4. LeaveRequest properties
    leave = Leave(emp_id=emp.user_id, reason="Vacation", start_date="2026-07-01", end_date="2026-07-05")
    session.add(leave)
    session.commit()
    
    assert leave.employee_name == "Rajveer Choudhary"
    assert leave.department_name == "Software Engineering"

def test_analytics_service_empty_db_and_error(app):
    from database.db_manager import db
    from services.analytics_service import AnalyticsService
    from unittest.mock import patch
    
    analytics_service = AnalyticsService()
    
    # Run in a clean app context with totally empty database
    with app.app_context():
        # Drop all tables to guarantee empty database state
        db.drop_all()
        db.create_all()
        
        # Test empty database behavior
        stats = analytics_service.get_workforce_analytics()
        assert stats["headcount"] == 0
        assert stats["avg_salary"] == 0.0
        assert stats["attendance_stats"]["mean_rate"] == 0.0
        assert stats["leave_stats"]["Pending"] == 0
        
        # Test generate_charts returns empty dictionary or doesn't crash
        charts = analytics_service.generate_charts()
        assert isinstance(charts, dict)
        
        # Force an exception (e.g. mock DB session query to throw error)
        with patch('database.db_manager.db.session.query') as mock_query:
            mock_query.side_effect = Exception("Database error simulation")
            err_stats = analytics_service.get_workforce_analytics()
            assert err_stats["headcount"] == 0
            assert err_stats["avg_salary"] == 0.0
            
            err_charts = analytics_service.generate_charts()
            assert err_charts == {}
