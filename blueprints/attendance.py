from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from blueprints.auth import login_required, role_required
from services.attendance_service import AttendanceService
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from models.attendance import Attendance
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

attendance_service = AttendanceService()
employee_service = EmployeeService()
department_service = DepartmentService()

@attendance_bp.route('/attendance')
@attendance_bp.route('/attendance/records')
@login_required
def list_attendance():
    role = session.get('role')
    emp_id = session.get('emp_id')
    
    date_filter = request.args.get('date', '').strip()
    dept_filter = request.args.get('department_id', '')
    
    dept_id = int(dept_filter) if dept_filter.isdigit() else None
    
    if role in ['Admin', 'HR']:
        records = attendance_service.get_attendance_records(
            date=date_filter if date_filter else None,
            department_id=dept_id
        )
        departments = department_service.get_all_departments()
        return render_template(
            'attendance/records.html', 
            records=records, 
            departments=departments,
            selected_date=date_filter,
            selected_dept=dept_id
        )
    elif role == 'Employee':
        if not emp_id:
            flash("Employee profile not linked.", "warning")
            return redirect(url_for('dashboard.index'))
            
        records = attendance_service.get_attendance_records(
            date=date_filter if date_filter else None,
            emp_id=emp_id
        )
        return render_template(
            'attendance/records.html',
            records=records,
            selected_date=date_filter
        )
        
    return redirect(url_for('auth.login'))

@attendance_bp.route('/attendance/mark', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'HR'])
def mark_attendance():
    date_str = request.args.get('date', '').strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    employees = employee_service.get_all_employees()
    
    existing_records = attendance_service.get_attendance_records(date=date_str)
    existing_map = {r.emp_id: r.status for r in existing_records}
    
    if request.method == 'POST':
        post_date = request.form.get('date', date_str)
        try:
            datetime.strptime(post_date, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for('attendance.mark_attendance', date=date_str))
            
        success_count = 0
        for emp in employees:
            status = request.form.get(f"status_{emp.user_id}")
            if status in ['Present', 'Absent', 'Leave']:
                attendance_service.mark_attendance(emp.user_id, post_date, status)
                success_count += 1
                
        flash(f"Logged attendance for {success_count} employees on {post_date}.", "success")
        return redirect(url_for('attendance.list_attendance', date=post_date))
        
    return render_template(
        'attendance/mark.html',
        employees=employees,
        date_str=date_str,
        existing_map=existing_map
    )

@attendance_bp.route('/attendance/edit/<int:attendance_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'HR'])
def edit_attendance(attendance_id):
    record = attendance_service.get_attendance_by_id(attendance_id)
    if not record:
        abort(404, description="Attendance record not found.")
        
    if request.method == 'POST':
        status = request.form.get('status')
        if status in ['Present', 'Absent', 'Leave']:
            attendance_service.update_attendance(attendance_id, status)
            flash("Attendance record updated successfully.", "success")
            return redirect(url_for('attendance.list_attendance', date=record.date))
        else:
            flash("Invalid status selection.", "danger")
            
    return render_template('attendance/edit.html', record=record)
