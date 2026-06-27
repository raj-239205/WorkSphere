from flask import Blueprint, render_template, session, redirect, url_for, request
from blueprints.auth import login_required
from utils.security import permission_required
from repositories.activity_log_repository import ActivityLogRepository

activity_log_repo = ActivityLogRepository()
from services.employee_service import EmployeeService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.department_service import DepartmentService
from services.analytics_service import AnalyticsService

dashboard_bp = Blueprint('dashboard', __name__)

employee_service = EmployeeService()
attendance_service = AttendanceService()
leave_service = LeaveService()
department_service = DepartmentService()
analytics_service = AnalyticsService()

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    role = session.get('role')
    emp_id = session.get('emp_id')
    
    if role in ['Admin', 'HR']:
        try:
            # Fetch Admin/HR Company-wide stats
            stats = attendance_service.get_today_stats()
            pending_leaves = leave_service.get_pending_count()
            recent_attendance = attendance_service.get_recent_activity(5)
            recent_leaves = leave_service.get_recent_requests(5)
            departments = department_service.get_all_departments()
            
            # Trigger dynamic charts generation using Pandas/NumPy/Matplotlib
            analytics_service.generate_charts()
            
            # Load live workforce analytics summary
            workforce_data = analytics_service.get_workforce_analytics()
            leave_stats = workforce_data.get('leave_stats', {'Pending': 0, 'Approved': 0, 'Rejected': 0})
            
            # Prepare charts data
            dept_labels = [d.department_name for d in departments]
            dept_counts = [d.employee_count for d in departments]
        except Exception as e:
            from flask import current_app, flash
            current_app.logger.error(f"Error loading dashboard data: {str(e)}", exc_info=True)
            flash("Some dashboard metrics failed to load correctly.", "warning")
            
            # Safe fallback values
            stats = {'Present': 0, 'Absent': 0, 'Leave': 0, 'TotalEmployees': 0, 'Unmarked': 0, 'AttendanceRate': 0.0}
            pending_leaves = 0
            recent_attendance = []
            recent_leaves = []
            dept_labels = []
            dept_counts = []
            workforce_data = {
                "headcount": 0, "avg_salary": 0.0, "median_salary": 0.0, "std_salary": 0.0,
                "dept_distribution": {},
                "attendance_stats": {"mean_rate": 0.0, "median_rate": 0.0, "std_rate": 0.0},
                "leave_stats": {'Pending': 0, 'Approved': 0, 'Rejected': 0}
            }
            leave_stats = workforce_data['leave_stats']
            
        return render_template(
            'dashboard.html',
            stats=stats,
            pending_leaves=pending_leaves,
            recent_attendance=recent_attendance,
            recent_leaves=recent_leaves,
            dept_labels=dept_labels,
            dept_counts=dept_counts,
            leave_stats=leave_stats,
            workforce_data=workforce_data
        )
        
    elif role == 'Employee':
        # Fetch Employee self-service stats
        if not emp_id:
            return render_template(
                'dashboard.html',
                employee=None,
                attendance_rate=0,
                recent_attendance=[],
                recent_leaves=[]
            )
            
        try:
            employee = employee_service.get_employee_by_id(emp_id)
            my_attendance = attendance_service.get_attendance_records(emp_id=emp_id)
            my_leaves = leave_service.get_leave_requests(emp_id=emp_id)
            
            # Calculate personal attendance rate
            presents = sum(1 for a in my_attendance if a.status == 'Present')
            absents = sum(1 for a in my_attendance if a.status == 'Absent')
            total_tracked = presents + absents
            attendance_rate = round((presents / total_tracked * 100), 1) if total_tracked > 0 else 100.0
        except Exception as e:
            from flask import current_app, flash
            current_app.logger.error(f"Error loading employee dashboard: {str(e)}", exc_info=True)
            flash("Failed to load your personal dashboard details.", "warning")
            employee = None
            my_attendance = []
            my_leaves = []
            attendance_rate = 0.0
            
        return render_template(
            'dashboard.html',
            employee=employee,
            attendance_rate=attendance_rate,
            recent_attendance=my_attendance[:5],
            recent_leaves=my_leaves[:5]
        )
        
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard/audit-logs')
@permission_required('can_view_audit_logs')
def audit_logs():
    page_str = request.args.get('page', '1')
    search_query = request.args.get('search', '').strip()
    try:
        page = max(1, int(page_str))
    except ValueError:
        page = 1
        
    limit = 20
    logs, total = activity_log_repo.get_paginated(page=page, limit=limit, search_query=search_query)
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return render_template(
        'dashboard/audit_logs.html',
        logs=logs,
        current_page=page,
        total_pages=total_pages,
        search_query=search_query
    )
