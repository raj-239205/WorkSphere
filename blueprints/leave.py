from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from blueprints.auth import login_required, role_required
from services.leave_service import LeaveService
from services.employee_service import EmployeeService
from models.leave import LeaveRequest as Leave

leave_bp = Blueprint('leave', __name__)
leave_service = LeaveService()
employee_service = EmployeeService()

@leave_bp.route('/leaves')
@leave_bp.route('/leave/requests')
@login_required
def list_leaves():
    role = session.get('role')
    emp_id = session.get('emp_id')
    status_filter = request.args.get('status', '').strip()
    
    if role in ['Admin', 'HR']:
        requests = leave_service.get_leave_requests(status=status_filter if status_filter else None)
        return render_template('leave/requests.html', requests=requests, selected_status=status_filter)
    elif role == 'Employee':
        if not emp_id:
            flash("Employee profile not linked.", "warning")
            return redirect(url_for('dashboard.index'))
            
        requests = leave_service.get_leave_requests(
            status=status_filter if status_filter else None, 
            emp_id=emp_id
        )
        return render_template('leave/requests.html', requests=requests, selected_status=status_filter)
        
    return redirect(url_for('auth.login'))

@leave_bp.route('/leave/apply', methods=['GET', 'POST'])
@login_required
def apply_leave():
    from datetime import date
    role = session.get('role')
    emp_id = session.get('emp_id')
    today_str = date.today().strftime('%Y-%m-%d')
    
    employees = []
    if role in ['Admin', 'HR']:
        employees = employee_service.get_all_employees()
        
    if request.method == 'POST':
        if role in ['Admin', 'HR']:
            target_emp_id = request.form.get('emp_id')
            target_emp_id = int(target_emp_id) if target_emp_id and target_emp_id.isdigit() else None
        else:
            target_emp_id = emp_id
            
        reason = request.form.get('reason', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        
        leave_req = Leave(emp_id=target_emp_id, reason=reason, start_date=start_date, end_date=end_date)
        errors = leave_req.validate()
        
        if errors:
            for field, error in errors.items():
                flash(error, "danger")
            return render_template('leave/apply.html', employees=employees, form=request.form, today_str=today_str)
            
        try:
            leave_service.apply_leave(target_emp_id, reason, start_date, end_date)
            flash("Leave request submitted successfully!", "success")
            return redirect(url_for('leave.list_leaves'))
        except Exception as e:
            flash(f"Error submitting request: {e}", "danger")
            return render_template('leave/apply.html', employees=employees, form=request.form, today_str=today_str)
            
    return render_template('leave/apply.html', employees=employees, form={}, today_str=today_str)

@leave_bp.route('/leave/approve/<int:leave_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'HR'])
def approve_leave(leave_id):
    leave = leave_service.get_leave_by_id(leave_id)
    if not leave:
        abort(404, description="Leave request not found.")
        
    try:
        leave_service.update_leave_status(leave_id, 'Approved')
        flash(f"Leave request for {leave.employee.name if leave.employee else 'Employee'} approved. Attendance updated.", "success")
    except Exception as e:
        flash(f"Failed to approve: {e}", "danger")
        
    return redirect(url_for('leave.list_leaves'))

@leave_bp.route('/leave/reject/<int:leave_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'HR'])
def reject_leave(leave_id):
    leave = leave_service.get_leave_by_id(leave_id)
    if not leave:
        abort(404, description="Leave request not found.")
        
    try:
        leave_service.update_leave_status(leave_id, 'Rejected')
        flash(f"Leave request for {leave.employee.name if leave.employee else 'Employee'} rejected.", "success")
    except Exception as e:
        flash(f"Failed to reject: {e}", "danger")
        
    return redirect(url_for('leave.list_leaves'))

@leave_bp.route('/leave/delete/<int:leave_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'HR'])
def delete_leave(leave_id):
    leave = leave_service.get_leave_by_id(leave_id)
    if not leave:
        abort(404, description="Leave request not found.")
        
    leave_service.delete_leave(leave_id)
    flash("Leave request deleted successfully.", "success")
    return redirect(url_for('leave.list_leaves'))
