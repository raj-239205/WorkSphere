from flask import Blueprint, render_template, request, session, redirect, url_for, send_file
from blueprints.auth import login_required, role_required
from services.department_service import DepartmentService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.employee_service import EmployeeService
from services.analytics_service import AnalyticsService
from utils.exporters import Exporters
from collections import defaultdict
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

department_service = DepartmentService()
attendance_service = AttendanceService()
leave_service = LeaveService()
employee_service = EmployeeService()
analytics_service = AnalyticsService()

@reports_bp.route('/reports')
@login_required
@role_required(['Admin', 'HR'])
def index():
    # 1. Department Salaries and Headcount Report using ORM
    dept_rows = []
    for dept in department_service.get_all_departments():
        active_emps = [e for e in dept.employees if e.is_active]
        headcount = len(active_emps)
        avg_salary = sum(e.salary for e in active_emps) / headcount if headcount > 0 else 0.0
        dept_rows.append({
            'department_name': dept.department_name,
            'headcount': headcount,
            'avg_salary': avg_salary
        })
        
    # 2. Leave Summary Data using Analytics Service
    analytics_data = analytics_service.get_workforce_analytics()
    leave_summary = analytics_data.get('leave_stats', {'Pending': 0, 'Approved': 0, 'Rejected': 0})
            
    # 3. Monthly Attendance Trends (last 6 months)
    all_attendance = attendance_service.get_attendance_records()
    monthly_data = defaultdict(lambda: {'Present': 0, 'Absent': 0, 'Leave': 0})
    for record in all_attendance:
        if record.date:
            month = record.date[:7]  # Extract YYYY-MM
            if record.status in monthly_data[month]:
                monthly_data[month][record.status] += 1
        
    months_labels = sorted(list(monthly_data.keys()))
    attendance_rates = []
    
    for m in months_labels:
        data = monthly_data[m]
        presents = data['Present']
        absents = data['Absent']
        total = presents + absents
        rate = round((presents / total * 100), 1) if total > 0 else 100.0
        attendance_rates.append(rate)
        
    # Formatting month labels (e.g. 2026-06 to Jun 2026)
    formatted_months = []
    for m in months_labels:
        try:
            dt = datetime.strptime(m, '%Y-%m')
            formatted_months.append(dt.strftime('%b %Y'))
        except ValueError:
            formatted_months.append(m)

    return render_template(
        'reports/analytics.html',
        dept_rows=dept_rows,
        leave_summary=leave_summary,
        months_labels=formatted_months,
        attendance_rates=attendance_rates
    )

@reports_bp.route('/reports/attendance')
@login_required
@role_required(['Admin', 'HR'])
def attendance_report():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    dept_id = request.args.get('department_id', '')
    
    # Default to past 30 days
    if not start_date or not end_date:
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
    selected_dept_id = int(dept_id) if dept_id and dept_id.isdigit() else None
    employees = employee_service.get_all_employees(department_id=selected_dept_id)
    departments = department_service.get_all_departments()
    
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
        
    return render_template(
        'reports/attendance.html',
        rows=processed_rows,
        departments=departments,
        start_date=start_date,
        end_date=end_date,
        selected_dept=selected_dept_id
    )

@reports_bp.route('/reports/export/pdf')
@login_required
@role_required(['Admin', 'HR'])
def export_pdf():
    """Generates PDF report of workforce summary."""
    employees = [e.to_dict() for e in employee_service.get_all_employees()]
    stats = analytics_service.get_workforce_analytics()
    pdf_buf = Exporters.generate_pdf_report(employees, stats)
    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"WorkSphere_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

@reports_bp.route('/reports/export/excel')
@login_required
@role_required(['Admin', 'HR'])
def export_excel():
    """Generates Excel directory download of workforce."""
    employees = [e.to_dict() for e in employee_service.get_all_employees()]
    excel_buf = Exporters.generate_excel_report(employees)
    return send_file(
        excel_buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"WorkSphere_Directory_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )
