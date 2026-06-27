from services.base_service import BaseService
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.analytics_service import AnalyticsService
from utils.exporters import Exporters
from utils.security import check_permission
from datetime import datetime, timedelta

class ReportService(BaseService):
    """Report business logic service layer protecting and formatting data exports."""

    def __init__(self):
        self.employee_service = EmployeeService()
        self.department_service = DepartmentService()
        self.attendance_service = AttendanceService()
        self.leave_service = LeaveService()
        self.analytics_service = AnalyticsService()

    def get_salaries_report_data(self):
        """Fetches department headcount and salary summary. Requires can_view_reports."""
        check_permission('can_view_reports', "Generate Salaries Report")
        dept_rows = []
        for dept in self.department_service.get_all_departments():
            active_emps = [e for e in dept.employees if e.is_active]
            headcount = len(active_emps)
            avg_salary = sum(e.salary for e in active_emps) / headcount if headcount > 0 else 0.0
            dept_rows.append({
                'department_name': dept.department_name,
                'headcount': headcount,
                'avg_salary': avg_salary
            })
        return dept_rows

    def get_attendance_report_data(self, start_date, end_date, selected_dept_id=None):
        """Fetches attendance metrics. Requires can_view_reports."""
        check_permission('can_view_reports', "Generate Attendance Report")
        employees = self.employee_service.get_all_employees(department_id=selected_dept_id)
        
        processed_rows = []
        for emp in employees:
            emp_att = [a for a in emp.attendances if start_date <= a.date <= end_date and a.is_active]
            present_days = sum(1 for a in emp_att if a.status == 'Present')
            absent_days = sum(1 for a in emp_att if a.status == 'Absent')
            leave_days = sum(1 for a in emp_att if a.status == 'Leave')
            total_days = len(emp_att)
            
            total_active = present_days + absent_days
            attendance_rate = round((present_days / total_active * 100), 1) if total_active > 0 else 100.0
            
            processed_rows.append({
                'name': emp.name,
                'designation': emp.designation,
                'department_name': emp.department.department_name if emp.department else 'Unassigned',
                'present_days': present_days,
                'absent_days': absent_days,
                'leave_days': leave_days,
                'total_days': total_days,
                'attendance_rate': attendance_rate
            })
        return processed_rows

    def export_pdf(self):
        """Generates PDF of workforce records. Requires can_view_reports."""
        check_permission('can_view_reports', "Export PDF Report")
        employees = [e.to_dict() for e in self.employee_service.get_all_employees()]
        stats = self.analytics_service.get_workforce_analytics()
        return Exporters.generate_pdf_report(employees, stats)

    def export_excel(self):
        """Generates Excel spreadsheet directory. Requires can_view_reports."""
        check_permission('can_view_reports', "Export Excel Directory")
        employees = [e.to_dict() for e in self.employee_service.get_all_employees()]
        return Exporters.generate_excel_report(employees)
