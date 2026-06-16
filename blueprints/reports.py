from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.auth import login_required, role_required
from services.department_service import DepartmentService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from database.db import DB
from collections import defaultdict
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@role_required(['Admin', 'HR'])
def index():
    # 1. Department Salaries and Headcount Report
    dept_query = """
        SELECT d.department_name, COUNT(e.emp_id) as headcount, IFNULL(AVG(e.salary), 0) as avg_salary
        FROM departments d
        LEFT JOIN employees e ON d.department_id = e.department_id
        GROUP BY d.department_id
    """
    dept_rows = DB.execute_query(dept_query, fetch_all=True)
    
    # 2. Leave Summary Data
    leave_query = "SELECT status, COUNT(*) as count FROM leaves GROUP BY status"
    leave_rows = DB.execute_query(leave_query, fetch_all=True)
    leave_summary = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
    for row in leave_rows:
        if row['status'] in leave_summary:
            leave_summary[row['status']] = row['count']
            
    # 3. Monthly Attendance Trends (last 6 months)
    # Get attendance status grouped by month
    trends_query = """
        SELECT STRFTIME('%Y-%m', date) as month, status, COUNT(*) as count
        FROM attendance
        GROUP BY month, status
        ORDER BY month ASC
        LIMIT 50
    """
    trends_rows = DB.execute_query(trends_query, fetch_all=True)
    
    # Process trends data for Chart.js
    monthly_data = defaultdict(lambda: {'Present': 0, 'Absent': 0, 'Leave': 0})
    for r in trends_rows:
        month = r['month']
        status = r['status']
        monthly_data[month][status] = r['count']
        
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
    # Optional filters
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    dept_id = request.args.get('department_id', '')
    
    # Default to past 30 days if dates not set
    if not start_date or not end_date:
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
    params = [start_date, end_date]
    dept_filter_sql = ""
    
    if dept_id and dept_id.isdigit():
        dept_filter_sql = " AND e.department_id = ?"
        params.append(int(dept_id))
        
    query = f"""
        SELECT e.name, e.designation, d.department_name,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
               SUM(CASE WHEN a.status = 'Leave' THEN 1 ELSE 0 END) as leave_days,
               COUNT(a.attendance_id) as total_days
        FROM employees e
        JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN attendance a ON e.emp_id = a.emp_id AND a.date BETWEEN ? AND ?
        WHERE 1=1 {dept_filter_sql}
        GROUP BY e.emp_id
        ORDER BY d.department_name, e.name
    """
    rows = DB.execute_query(query, params, fetch_all=True)
    departments = DepartmentService.get_all_departments()
    
    # Process rates
    processed_rows = []
    for row in rows:
        r = dict(row)
        total = r['present_days'] + r['absent_days']
        r['attendance_rate'] = round((r['present_days'] / total * 100), 1) if total > 0 else 100.0
        processed_rows.append(r)
        
    return render_template(
        'reports/attendance.html',
        rows=processed_rows,
        departments=departments,
        start_date=start_date,
        end_date=end_date,
        selected_dept=int(dept_id) if dept_id.isdigit() else None
    )
