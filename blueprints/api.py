from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from extensions import limiter
from services.employee_service import EmployeeService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.department_service import DepartmentService
from services.user_service import UserService
from exceptions.custom_exceptions import WorkSphereException
import json

# Setup API Blueprint version 1
api_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Initialize services
employee_service = EmployeeService()
attendance_service = AttendanceService()
leave_service = LeaveService()
department_service = DepartmentService()
user_service = UserService()

def get_pagination_params():
    page = request.args.get('page', 1)
    limit = request.args.get('limit', 10)
    try:
        page = max(1, int(page))
        limit = max(1, min(100, int(limit)))
    except ValueError:
        page, limit = 1, 10
    return page, limit


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    User authentication endpoint.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: admin123
    responses:
      200:
        description: Successful login, returns JWT token.
      401:
        description: Invalid credentials.
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
        
    user = user_service.authenticate_user(username, password, ip_address=request.remote_addr)
    if user:
        access_token = create_access_token(identity=json.dumps({
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role
        }))
        return jsonify({
            "access_token": access_token,
            "role": user.role,
            "username": user.username
        }), 200
        
    return jsonify({"error": "Invalid username or password."}), 401


# ==========================================================
# EMPLOYEE ENDPOINTS
# ==========================================================

@api_bp.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():
    """
    Get paginated and filtered active employees.
    ---
    tags:
      - Employees
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: limit
        in: query
        type: integer
        default: 10
      - name: search
        in: query
        type: string
      - name: department_id
        in: query
        type: integer
    responses:
      200:
        description: List of employees.
    """
    page, limit = get_pagination_params()
    search = request.args.get('search', '').strip()
    dept_id = request.args.get('department_id')
    dept_id = int(dept_id) if dept_id and dept_id.isdigit() else None
    
    # Query using EmployeeService
    employees = employee_service.get_all_employees(search_query=search, department_id=dept_id, include_inactive=False)
    
    # Simple manual pagination
    total_count = len(employees)
    start = (page - 1) * limit
    end = start + limit
    paginated_employees = employees[start:end]
    
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
    
    return jsonify({
        "results": [emp.to_dict() for emp in paginated_employees],
        "metadata": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_count": total_count
        }
    }), 200


@api_bp.route('/employees/<int:emp_id>', methods=['GET'])
@jwt_required()
def get_employee(emp_id):
    """Get employee by ID."""
    emp = employee_service.get_employee_by_id(emp_id)
    if emp and emp.is_active:
        return jsonify(emp.to_dict()), 200
    return jsonify({"error": "Employee not found."}), 404


@api_bp.route('/employees', methods=['POST'])
@jwt_required()
def create_employee():
    """Create new employee."""
    data = request.get_json() or {}
    try:
        emp = employee_service.create_employee(
            name=data.get('name', '').strip(),
            email=data.get('email', '').strip(),
            phone=data.get('phone', '').strip(),
            department_id=data.get('department_id'),
            salary=float(data.get('salary', 0.0)),
            designation=data.get('designation', '').strip(),
            username=data.get('username'),
            password=data.get('password')
        )
        return jsonify(emp.to_dict()), 210
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/employees/<int:emp_id>', methods=['PUT'])
@jwt_required()
def update_employee(emp_id):
    """Update employee details."""
    data = request.get_json() or {}
    try:
        employee_service.update_employee(
            emp_id=emp_id,
            name=data.get('name', '').strip(),
            email=data.get('email', '').strip(),
            phone=data.get('phone', '').strip(),
            department_id=data.get('department_id'),
            salary=float(data.get('salary', 0.0)),
            designation=data.get('designation', '').strip()
        )
        return jsonify({"message": "Employee updated successfully."}), 200
    except (ValueError, WorkSphereException) as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/employees/<int:emp_id>', methods=['DELETE'])
@jwt_required()
def delete_employee(emp_id):
    """Soft delete employee."""
    try:
        employee_service.delete_employee(emp_id)
        return jsonify({"message": "Employee soft-deleted successfully."}), 200
    except WorkSphereException as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/employees/<int:emp_id>/restore', methods=['POST'])
@jwt_required()
def restore_employee(emp_id):
    """Restore soft-deleted employee."""
    try:
        employee_service.restore_employee(emp_id)
        return jsonify({"message": "Employee restored successfully."}), 200
    except WorkSphereException as e:
        return jsonify({"error": str(e)}), 400


# ==========================================================
# DEPARTMENT ENDPOINTS
# ==========================================================

@api_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """Get active departments."""
    depts = department_service.get_all_departments(include_inactive=False)
    return jsonify([d.to_dict() for d in depts]), 200


@api_bp.route('/departments', methods=['POST'])
@jwt_required()
def create_department():
    """Create department."""
    data = request.get_json() or {}
    try:
        dept = department_service.create_department(
            department_name=data.get('department_name', '').strip(),
            manager_name=data.get('manager_name', '').strip()
        )
        return jsonify(dept.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@jwt_required()
def delete_department(dept_id):
    """Soft delete department."""
    try:
        department_service.delete_department(dept_id)
        return jsonify({"message": "Department soft-deleted successfully."}), 200
    except (ValueError, WorkSphereException) as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/departments/<int:dept_id>/restore', methods=['POST'])
@jwt_required()
def restore_department(dept_id):
    """Restore soft-deleted department."""
    try:
        department_service.restore_department(dept_id)
        return jsonify({"message": "Department restored successfully."}), 200
    except WorkSphereException as e:
        return jsonify({"error": str(e)}), 400


# ==========================================================
# ATTENDANCE ENDPOINTS
# ==========================================================

@api_bp.route('/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    """Get attendance records."""
    date = request.args.get('date')
    emp_id = request.args.get('emp_id')
    emp_id = int(emp_id) if emp_id and emp_id.isdigit() else None
    
    records = attendance_service.get_attendance_records(date=date, emp_id=emp_id)
    return jsonify([r.to_dict() for r in records]), 200


@api_bp.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    """Mark/Upsert attendance."""
    data = request.get_json() or {}
    try:
        attendance_id = attendance_service.mark_attendance(
            emp_id=int(data.get('emp_id')),
            date=data.get('date'),
            status=data.get('status')
        )
        return jsonify({"attendance_id": attendance_id, "message": "Attendance marked successfully."}), 200
    except (ValueError, WorkSphereException) as e:
        return jsonify({"error": str(e)}), 400


# ==========================================================
# LEAVE ENDPOINTS
# ==========================================================

@api_bp.route('/leaves', methods=['GET'])
@jwt_required()
def get_leaves():
    """Get leave requests."""
    status = request.args.get('status')
    emp_id = request.args.get('emp_id')
    emp_id = int(emp_id) if emp_id and emp_id.isdigit() else None
    
    requests = leave_service.get_leave_requests(status=status, emp_id=emp_id)
    return jsonify([r.to_dict() for r in requests]), 200


@api_bp.route('/leaves', methods=['POST'])
@jwt_required()
def apply_leave():
    """Apply for leave."""
    data = request.get_json() or {}
    try:
        leave = leave_service.apply_leave(
            emp_id=int(data.get('emp_id')),
            reason=data.get('reason'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
        )
        return jsonify(leave.to_dict()), 201
    except WorkSphereException as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/leaves/<int:leave_id>/status', methods=['PUT'])
@jwt_required()
def update_leave_status(leave_id):
    """Approve or reject leave request."""
    data = request.get_json() or {}
    try:
        leave_service.update_leave_status(
            leave_id=leave_id,
            status=data.get('status')
        )
        return jsonify({"message": f"Leave status updated to {data.get('status')} successfully."}), 200
    except WorkSphereException as e:
        return jsonify({"error": str(e)}), 400
