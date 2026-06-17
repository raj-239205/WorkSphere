import sys
import os
import unittest
from datetime import date, timedelta

# Dynamically resolve project root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.user_service import UserService
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from models.leave import Leave

class TestWorkSphereServices(unittest.TestCase):
    
    def test_user_authentication(self):
        # Admin authentication
        admin = UserService.authenticate_user("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, "Admin")
        
        # HR User authentication
        hr = UserService.authenticate_user("hr_user", "hr123")
        self.assertIsNotNone(hr)
        self.assertEqual(hr.role, "HR")
        
        # Employee authentication
        emp = UserService.authenticate_user("emp_user", "emp123")
        self.assertIsNotNone(emp)
        self.assertEqual(emp.role, "Employee")

    def test_employee_loading(self):
        employees = EmployeeService.get_all_employees()
        self.assertGreaterEqual(len(employees), 6)
        
        names = [e.name for e in employees]
        self.assertIn("Rajveer Choudhary", names)
        self.assertIn("Sudhanshu Sharma", names)

    def test_department_loading(self):
        depts = DepartmentService.get_all_departments()
        self.assertEqual(len(depts), 4)
        
        dept_names = [d.department_name for d in depts]
        self.assertIn("Software Engineering", dept_names)
        self.assertIn("Human Resources", dept_names)

    def test_leave_validations(self):
        today_str = date.today().strftime('%Y-%m-%d')
        past_str = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        future_str = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
        far_future_str = "20266-01-01"
        
        # 1. Test valid leave model
        valid_leave = Leave(emp_id=1, reason="Test", start_date=today_str, end_date=future_str)
        self.assertEqual(len(valid_leave.validate()), 0)
        
        # 2. Test past date rejection
        past_leave = Leave(emp_id=1, reason="Test", start_date=past_str, end_date=future_str)
        errors = past_leave.validate()
        self.assertIn('start_date', errors)
        
        # 3. Test end date before start date
        reversed_leave = Leave(emp_id=1, reason="Test", start_date=future_str, end_date=today_str)
        errors = reversed_leave.validate()
        self.assertIn('end_date', errors)

        # 4. Test invalid year length
        bad_year_leave = Leave(emp_id=1, reason="Test", start_date=far_future_str, end_date=future_str)
        errors = bad_year_leave.validate()
        self.assertIn('start_date', errors)

    def test_overlapping_leaves(self):
        employees = EmployeeService.get_all_employees()
        emp_map = {e.email: e.emp_id for e in employees}
        rajveer_id = emp_map["rajveer@worksphere.com"]
        
        # Seeded leave range in init_db is from today+2 to today+5.
        # Let's request an overlapping leave range from today+3 to today+4.
        overlapping_start = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')
        overlapping_end = (date.today() + timedelta(days=4)).strftime('%Y-%m-%d')
        
        with self.assertRaises(ValueError):
            LeaveService.apply_leave(
                emp_id=rajveer_id,
                reason="Overlapping exam preparation",
                start_date=overlapping_start,
                end_date=overlapping_end
            )

if __name__ == '__main__':
    unittest.main()
