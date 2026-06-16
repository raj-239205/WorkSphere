from flask import Blueprint, render_template, session, redirect, url_for
from blueprints.auth import login_required
from services.employee_service import EmployeeService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.department_service import DepartmentService
from database.db import DB

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    role = session.get('role')
    emp_id = session.get('emp_id')
    
    if role in ['Admin', 'HR']:
        # Fetch Admin/HR Company-wide stats
        stats = AttendanceService.get_today_stats()
        pending_leaves = LeaveService.get_pending_count()
        recent_attendance = AttendanceService.get_recent_activity(5)
        recent_leaves = LeaveService.get_recent_requests(5)
        departments = DepartmentService.get_all_departments()
        
        # Aggregate Leave status distribution for charts
        leave_chart_query = "SELECT status, COUNT(*) as count FROM leaves GROUP BY status"
        leave_chart_rows = DB.execute_query(leave_chart_query, fetch_all=True)
        leave_stats = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
        for row in leave_chart_rows:
            if row['status'] in leave_stats:
                leave_stats[row['status']] = row['count']
                
        # Prepare charts data
        dept_labels = [d.department_name for d in departments]
        dept_counts = [d.employee_count for d in departments]
        
        return render_template(
            'dashboard.html',
            stats=stats,
            pending_leaves=pending_leaves,
            recent_attendance=recent_attendance,
            recent_leaves=recent_leaves,
            dept_labels=dept_labels,
            dept_counts=dept_counts,
            leave_stats=leave_stats
        )
        
    elif role == 'Employee':
        # Fetch Employee self-service stats
        if not emp_id:
            # Fallback if employee is not linked to profile
            return render_template(
                'dashboard.html',
                employee=None,
                attendance_rate=0,
                recent_attendance=[],
                recent_leaves=[]
            )
            
        employee = EmployeeService.get_employee_by_id(emp_id)
        my_attendance = AttendanceService.get_attendance_records(emp_id=emp_id)
        my_leaves = LeaveService.get_leave_requests(emp_id=emp_id)
        
        # Calculate personal attendance rate
        presents = sum(1 for a in my_attendance if a.status == 'Present')
        absents = sum(1 for a in my_attendance if a.status == 'Absent')
        total_tracked = presents + absents
        attendance_rate = round((presents / total_tracked * 100), 1) if total_tracked > 0 else 100.0
        
        return render_template(
            'dashboard.html',
            employee=employee,
            attendance_rate=attendance_rate,
            recent_attendance=my_attendance[:5],
            recent_leaves=my_leaves[:5]
        )
        
    return redirect(url_for('auth.login'))
