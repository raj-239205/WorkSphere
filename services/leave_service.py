from services.base_service import BaseService
from repositories.leave_repository import LeaveRepository
from repositories.activity_log_repository import ActivityLogRepository
from exceptions.custom_exceptions import LeaveValidationException, UnauthorizedAccessException
from models.leave import LeaveRequest
from models.activity_log import ActivityLog
from database.db_manager import DatabaseManager
from services.attendance_service import AttendanceService
from utils.security import check_permission, get_current_user_details, has_permission, log_auth_event
from flask import has_request_context, request
from datetime import datetime, timedelta
from typing import List, Optional
import json
from sqlalchemy import case

class LeaveService(BaseService):
    """Leave request business logic service layer."""

    def __init__(self, leave_repo: LeaveRepository = None, 
                 activity_log_repo: ActivityLogRepository = None,
                 attendance_service: AttendanceService = None):
        self.leave_repo = leave_repo or LeaveRepository()
        self.activity_log_repo = activity_log_repo or ActivityLogRepository()
        self.attendance_service = attendance_service or AttendanceService()
        self.db_manager = DatabaseManager()

    def get_leave_requests(self, status: str = None, emp_id: int = None) -> List[LeaveRequest]:
        """Retrieves leave requests, optionally filtered by status and employee, sorted by pending first."""
        from database.db_manager import db
        from models.user import Employee
        
        user_details = get_current_user_details()
        if user_details:
            role = user_details.get('role')
            user_id = user_details.get('user_id')
            if not has_permission(role, 'can_view_leaves'):
                if has_permission(role, 'can_view_own_leaves') and (emp_id is None or int(emp_id) == int(user_id)):
                    # Restrict to own user ID
                    emp_id = user_id
                else:
                    log_auth_event(
                        user_id, user_details.get('username'), role, 
                        'can_view_leaves', "View Leave Requests List", 'Denied', 
                        request.remote_addr if has_request_context() else '127.0.0.1'
                    )
                    raise UnauthorizedAccessException("You do not have permission to view other employee leave requests.")

        query = db.session.query(LeaveRequest).join(Employee, LeaveRequest.emp_id == Employee.user_id)
        query = query.filter(LeaveRequest.is_active == True, Employee.is_active == True)
        
        if status:
            query = query.filter(LeaveRequest.status == status)
        if emp_id:
            query = query.filter(LeaveRequest.emp_id == emp_id)
            
        order_case = case(
            (LeaveRequest.status == 'Pending', 1),
            else_=2
        )
        return query.order_by(order_case, LeaveRequest.start_date.desc()).all()

    def get_leave_by_id(self, leave_id: int) -> Optional[LeaveRequest]:
        record = self.leave_repo.get_by_id(leave_id)
        if record:
            user_details = get_current_user_details()
            if user_details:
                role = user_details.get('role')
                user_id = user_details.get('user_id')
                if not has_permission(role, 'can_view_leaves'):
                    if has_permission(role, 'can_view_own_leaves') and int(record.emp_id) == int(user_id):
                        pass
                    else:
                        log_auth_event(
                            user_id, user_details.get('username'), role, 
                            'can_view_leaves', f"View Leave request ID {leave_id}", 'Denied', 
                            request.remote_addr if has_request_context() else '127.0.0.1'
                        )
                        raise UnauthorizedAccessException("You do not have permission to access this leave request.")
        return record

    def apply_leave(self, emp_id: int, reason: str, start_date: str, end_date: str) -> LeaveRequest:
        """Applies for a new leave request. Performs range checks and overlap validations."""
        user_details = get_current_user_details()
        if user_details:
            role = user_details.get('role')
            user_id = user_details.get('user_id')
            if int(emp_id) == int(user_id):
                check_permission('can_view_own_leaves', f"Apply Leave for own account (ID {emp_id})")
            else:
                check_permission('can_approve_leave', f"Apply Leave on behalf of Employee ID {emp_id}")

        with self.db_manager.session_scope():
            req = LeaveRequest(emp_id=emp_id, reason=reason, start_date=start_date, end_date=end_date)
            errors = req.validate()
            if errors:
                err_msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
                raise LeaveValidationException(err_msg)
                
            overlaps = self.leave_repo.get_overlapping_requests(emp_id, start_date, end_date)
            if overlaps:
                raise LeaveValidationException("You have an overlapping leave request during this period.")
                
            created = self.leave_repo.create(req)
            
            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Leave Applied",
                new_value=json.dumps(created.to_dict())
            )
            self.activity_log_repo.create(log)
            return created

    def update_leave_status(self, leave_id: int, status: str) -> None:
        """Approves or rejects a leave request. Automatically logs 'Leave' attendance on approval."""
        check_permission('can_approve_leave', f"Update Leave Status for ID {leave_id} to {status} Attempt")
        if status not in ['Approved', 'Rejected', 'Pending']:
            raise LeaveValidationException("Invalid status value.")
            
        with self.db_manager.session_scope():
            leave = self.leave_repo.get_by_id(leave_id)
            if not leave:
                raise LeaveValidationException(f"Leave request with ID {leave_id} not found.")
                
            old_status = leave.status
            leave.status = status
            self.leave_repo.update(leave)
            
            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type=f"Leave {status}",
                old_value=json.dumps({"leave_id": leave_id, "status": old_status}),
                new_value=json.dumps({"leave_id": leave_id, "status": status})
            )
            self.activity_log_repo.create(log)
            
            # Automatically populate attendance as 'Leave' for the dates
            if status == 'Approved':
                start = datetime.strptime(leave.start_date, '%Y-%m-%d')
                end = datetime.strptime(leave.end_date, '%Y-%m-%d')
                curr = start
                while curr <= end:
                    date_str = curr.strftime('%Y-%m-%d')
                    self.attendance_service.mark_attendance(leave.emp_id, date_str, 'Leave')
                    curr += timedelta(days=1)

    def get_pending_count(self) -> int:
        check_permission('can_view_leaves', "Get Pending Leaves Count")
        return self.leave_repo.get_pending_count()

    def get_recent_requests(self, limit: int = 5) -> List[LeaveRequest]:
        check_permission('can_view_leaves', "Get Recent Leave Requests")
        return self.leave_repo.get_recent(limit)

    def delete_leave(self, leave_id: int) -> None:
        check_permission('can_approve_leave', f"Delete Leave ID {leave_id} Attempt")
        with self.db_manager.session_scope():
            leave = self.leave_repo.get_by_id(leave_id)
            if not leave:
                raise LeaveValidationException(f"Leave request with ID {leave_id} not found.")
                
            old_state = json.dumps(leave.to_dict())
            self.leave_repo.delete(leave_id)
            
            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Leave Deleted",
                old_value=old_state
            )
            self.activity_log_repo.create(log)
