from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from utils.security import permission_required
from services.department_service import DepartmentService
from models.department import Department

department_bp = Blueprint('department', __name__)
department_service = DepartmentService()

@department_bp.route('/departments')
@permission_required('can_view_departments')
def list_departments():
    departments = department_service.get_all_departments()
    return render_template('department/list.html', departments=departments)

@department_bp.route('/department/add', methods=['GET', 'POST'])
@permission_required('can_add_department')
def add_department():
    if request.method == 'POST':
        name = request.form.get('department_name', '').strip()
        manager = request.form.get('manager_name', '').strip()
        
        dept = Department(department_name=name, manager_name=manager)
        errors = dept.validate()
        
        if errors:
            for field, error in errors.items():
                flash(error, "danger")
            return render_template('department/add.html', form=request.form)
            
        try:
            department_service.create_department(name, manager)
            flash("Department created successfully!", "success")
            return redirect(url_for('department.list_departments'))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('department/add.html', form=request.form)
            
    return render_template('department/add.html', form={})

@department_bp.route('/department/edit/<int:department_id>', methods=['GET', 'POST'])
@permission_required('can_edit_department')
def edit_department(department_id):
    department = department_service.get_department_by_id(department_id)
    if not department:
        abort(404, description="Department not found.")
        
    if request.method == 'POST':
        name = request.form.get('department_name', '').strip()
        manager = request.form.get('manager_name', '').strip()
        
        dept = Department(department_id=department_id, department_name=name, manager_name=manager)
        errors = dept.validate()
        
        if errors:
            for field, error in errors.items():
                flash(error, "danger")
            return render_template('department/edit.html', department=department)
            
        try:
            department_service.update_department(department_id, name, manager)
            flash("Department updated successfully!", "success")
            return redirect(url_for('department.list_departments'))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('department/edit.html', department=department)
            
    return render_template('department/edit.html', department=department)

@department_bp.route('/department/delete/<int:department_id>', methods=['POST'])
@permission_required('can_delete_department')
def delete_department(department_id):
    department = department_service.get_department_by_id(department_id)
    if not department:
        abort(404, description="Department not found.")
        
    try:
        department_service.delete_department(department_id)
        flash(f"Department '{department.department_name}' deleted successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for('department.list_departments'))
