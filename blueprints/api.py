from flask import Blueprint, jsonify, request
from services.employee_service import EmployeeService
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/employees')
def get_employees():
    dept_id = request.args.get('department_id')
    search = request.args.get('search')
    
    dept_id = int(dept_id) if dept_id and dept_id.isdigit() else None
    employees = EmployeeService.get_all_employees(search_query=search, department_id=dept_id)
    
    return jsonify([emp.to_dict() for emp in employees])

@api_bp.route('/attendance')
def get_attendance():
    date = request.args.get('date')
    emp_id = request.args.get('emp_id')
    
    emp_id = int(emp_id) if emp_id and emp_id.isdigit() else None
    records = AttendanceService.get_attendance_records(date=date, emp_id=emp_id)
    
    return jsonify([rec.to_dict() for rec in records])

@api_bp.route('/leaves')
def get_leaves():
    status = request.args.get('status')
    emp_id = request.args.get('emp_id')
    
    emp_id = int(emp_id) if emp_id and emp_id.isdigit() else None
    requests = LeaveService.get_leave_requests(status=status, emp_id=emp_id)
    
    return jsonify([req.to_dict() for req in requests])
