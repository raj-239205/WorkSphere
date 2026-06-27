from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from utils.security import permission_required, has_permission
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from models.user import Employee

employee_bp = Blueprint('employee', __name__)
employee_service = EmployeeService()
department_service = DepartmentService()

@employee_bp.route('/employees')
@permission_required('can_view_employees')
def list_employees():
    search_query = request.args.get('search', '').strip()
    department_id = request.args.get('department_id', '')
    
    # Convert department_id to int if present
    dept_id = int(department_id) if department_id.isdigit() else None
    
    employees = employee_service.get_all_employees(search_query=search_query, department_id=dept_id)
    departments = department_service.get_all_departments()
    
    return render_template(
        'employee/list.html', 
        employees=employees, 
        departments=departments,
        search_query=search_query,
        selected_dept=dept_id
    )

@employee_bp.route('/employee/profile')
@permission_required('can_view_own_profile')
def profile():
    emp_id = session.get('user_id') # user_id matches emp_id
    if not emp_id:
        flash("You are not linked to an employee profile.", "warning")
        return redirect(url_for('dashboard.index'))
        
    employee = employee_service.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee profile not found.")
        
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/employee/view/<int:emp_id>')
@permission_required('can_view_own_profile')
def view_employee(emp_id):
    role = session.get('role')
    my_emp_id = session.get('user_id')
    
    # Secure access check
    if not has_permission(role, 'can_view_employees'):
        if not (has_permission(role, 'can_view_own_profile') and int(my_emp_id) == int(emp_id)):
            return render_template('access_denied.html'), 403
        
    employee = employee_service.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee not found.")
        
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/employee/add', methods=['GET', 'POST'])
@permission_required('can_add_employee')
def add_employee():
    departments = department_service.get_all_departments()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department_id = request.form.get('department_id', '')
        salary = request.form.get('salary', '0.0')
        designation = request.form.get('designation', '').strip()
        
        dept_id = int(department_id) if department_id.isdigit() else None
        
        # Instantiate model for validation
        emp = Employee(
            name=name, email=email, phone=phone, 
            department_id=dept_id, salary=salary, designation=designation
        )
        
        errors = emp.validate()
        if errors:
            for field, error in errors.items():
                flash(error, "danger")
            return render_template('employee/add.html', departments=departments, form=request.form)
            
        try:
            employee_service.create_employee(
                name=name, email=email, phone=phone, 
                department_id=dept_id, salary=float(salary), designation=designation
            )
            flash("Employee added successfully!", "success")
            return redirect(url_for('employee.list_employees'))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('employee/add.html', departments=departments, form=request.form)
            
    return render_template('employee/add.html', departments=departments, form={})

@employee_bp.route('/employee/edit/<int:emp_id>', methods=['GET', 'POST'])
@permission_required('can_edit_employee')
def edit_employee(emp_id):
    employee = employee_service.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee not found.")
        
    departments = department_service.get_all_departments()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department_id = request.form.get('department_id', '')
        salary = request.form.get('salary', '0.0')
        designation = request.form.get('designation', '').strip()
        
        dept_id = int(department_id) if department_id.isdigit() else None
        
        emp = Employee(
            emp_id=emp_id, name=name, email=email, phone=phone, 
            department_id=dept_id, salary=salary, designation=designation
        )
        
        errors = emp.validate()
        if errors:
            for field, error in errors.items():
                flash(error, "danger")
            return render_template('employee/edit.html', employee=employee, departments=departments)
            
        try:
            employee_service.update_employee(
                emp_id=emp_id, name=name, email=email, phone=phone, 
                department_id=dept_id, salary=float(salary), designation=designation
            )
            flash("Employee details updated successfully!", "success")
            return redirect(url_for('employee.list_employees'))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('employee/edit.html', employee=employee, departments=departments)
            
    return render_template('employee/edit.html', employee=employee, departments=departments)

@employee_bp.route('/employee/delete/<int:emp_id>', methods=['POST'])
@permission_required('can_delete_employee')
def delete_employee(emp_id):
    employee = employee_service.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee not found.")
        
    employee_service.delete_employee(emp_id)
    flash(f"Employee '{employee.name}' deleted successfully.", "success")
    return redirect(url_for('employee.list_employees'))
