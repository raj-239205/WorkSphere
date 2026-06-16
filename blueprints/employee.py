from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from blueprints.auth import login_required, role_required
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from models.employee import Employee

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employees')
@login_required
@role_required(['Admin', 'HR'])
def list_employees():
    search_query = request.args.get('search', '').strip()
    department_id = request.args.get('department_id', '')
    
    # Convert department_id to int if present
    dept_id = int(department_id) if department_id.isdigit() else None
    
    employees = EmployeeService.get_all_employees(search_query=search_query, department_id=dept_id)
    departments = DepartmentService.get_all_departments()
    
    return render_template(
        'employee/list.html', 
        employees=employees, 
        departments=departments,
        search_query=search_query,
        selected_dept=dept_id
    )

@employee_bp.route('/employee/profile')
@login_required
def profile():
    emp_id = session.get('emp_id')
    role = session.get('role')
    
    if not emp_id:
        flash("You are not linked to an employee profile.", "warning")
        return redirect(url_for('dashboard.index'))
        
    employee = EmployeeService.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee profile not found.")
        
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/employee/view/<int:emp_id>')
@login_required
def view_employee(emp_id):
    role = session.get('role')
    my_emp_id = session.get('emp_id')
    
    # Secure access check
    if role == 'Employee' and my_emp_id != emp_id:
        return render_template('access_denied.html'), 403
        
    employee = EmployeeService.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee not found.")
        
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'HR'])
def add_employee():
    departments = DepartmentService.get_all_departments()
    
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
            EmployeeService.create_employee(
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
@login_required
@role_required(['Admin', 'HR'])
def edit_employee(emp_id):
    employee = EmployeeService.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee not found.")
        
    departments = DepartmentService.get_all_departments()
    
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
            EmployeeService.update_employee(
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
@login_required
@role_required(['Admin', 'HR'])
def delete_employee(emp_id):
    employee = EmployeeService.get_employee_by_id(emp_id)
    if not employee:
        abort(404, description="Employee not found.")
        
    EmployeeService.delete_employee(emp_id)
    flash(f"Employee '{employee.name}' deleted successfully.", "success")
    return redirect(url_for('employee.list_employees'))
