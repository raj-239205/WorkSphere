from services.base_service import BaseService
from repositories.attendance_repository import AttendanceRepository
from repositories.employee_repository import EmployeeRepository
from repositories.activity_log_repository import ActivityLogRepository
from exceptions.custom_exceptions import AttendanceValidationException
from models.attendance import Attendance
from models.activity_log import ActivityLog
from database.db_manager import DatabaseManager
from datetime import datetime
from typing import List, Optional
import json

class AttendanceService(BaseService):
    """Attendance business logic service layer."""

    def __init__(self, attendance_repo: AttendanceRepository = None, 
                 employee_repo: EmployeeRepository = None, 
                 activity_log_repo: ActivityLogRepository = None):
        self.attendance_repo = attendance_repo or AttendanceRepository()
        self.employee_repo = employee_repo or EmployeeRepository()
        self.activity_log_repo = activity_log_repo or ActivityLogRepository()
        self.db_manager = DatabaseManager()

    def get_attendance_records(self, date: str = None, emp_id: int = None, department_id: int = None) -> List[Attendance]:
        """Retrieves attendance records with optional filters for date, employee, and department."""
        from database.db_manager import db
        from models.user import Employee
        
        query = db.session.query(Attendance).join(Employee, Attendance.emp_id == Employee.user_id)
        query = query.filter(Attendance.is_active == True, Employee.is_active == True)
        
        if date:
            query = query.filter(Attendance.date == date)
        if emp_id:
            query = query.filter(Attendance.emp_id == emp_id)
        if department_id:
            query = query.filter(Employee.department_id == department_id)
            
        return query.order_by(Attendance.date.desc(), Employee.name.asc()).all()

    def get_attendance_by_id(self, attendance_id: int) -> Optional[Attendance]:
        return self.attendance_repo.get_by_id(attendance_id)

    def mark_attendance(self, emp_id: int, date: str, status: str) -> int:
        """Marks attendance for an employee on a given date (with upsert behavior)."""
        if status not in ['Present', 'Absent', 'Leave']:
            raise AttendanceValidationException("Status must be 'Present', 'Absent', or 'Leave'")
            
        with self.db_manager.session_scope():
            # Verify employee exists and is active
            emp = self.employee_repo.get_by_id(emp_id)
            if not emp or not emp.is_active:
                raise AttendanceValidationException(f"Active employee with ID {emp_id} not found.")

            existing = self.attendance_repo.get_by_emp_and_date(emp_id, date)
            if existing:
                old_status = existing.status
                existing.status = status
                self.attendance_repo.update(existing)
                
                # Log audit trail
                log = ActivityLog(
                    user_id=None,
                    action_type="Attendance Marked (Updated)",
                    old_value=json.dumps({"emp_id": emp_id, "date": date, "status": old_status}),
                    new_value=json.dumps({"emp_id": emp_id, "date": date, "status": status})
                )
                self.activity_log_repo.create(log)
                return existing.attendance_id
            else:
                record = Attendance(emp_id=emp_id, date=date, status=status)
                created = self.attendance_repo.create(record)
                
                # Log audit trail
                log = ActivityLog(
                    user_id=None,
                    action_type="Attendance Marked (Created)",
                    new_value=json.dumps({"emp_id": emp_id, "date": date, "status": status})
                )
                self.activity_log_repo.create(log)
                return created.attendance_id

    def update_attendance(self, attendance_id: int, status: str) -> None:
        if status not in ['Present', 'Absent', 'Leave']:
            raise AttendanceValidationException("Status must be 'Present', 'Absent', or 'Leave'")
            
        with self.db_manager.session_scope():
            record = self.attendance_repo.get_by_id(attendance_id)
            if not record:
                raise AttendanceValidationException(f"Attendance record with ID {attendance_id} not found.")
                
            old_status = record.status
            record.status = status
            self.attendance_repo.update(record)
            
            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Attendance Updated",
                old_value=json.dumps({"attendance_id": attendance_id, "status": old_status}),
                new_value=json.dumps({"attendance_id": attendance_id, "status": status})
            )
            self.activity_log_repo.create(log)

    def delete_attendance(self, attendance_id: int) -> None:
        with self.db_manager.session_scope():
            record = self.attendance_repo.get_by_id(attendance_id)
            if not record:
                raise AttendanceValidationException(f"Attendance record with ID {attendance_id} not found.")
                
            old_state = json.dumps(record.to_dict())
            self.attendance_repo.delete(attendance_id)
            
            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Attendance Deleted",
                old_value=old_state
            )
            self.activity_log_repo.create(log)

    def get_today_stats(self) -> dict:
        """Returns statistical counts and rate for today's attendance."""
        today = datetime.now().strftime('%Y-%m-%d')
        active_employees = self.employee_repo.get_all(include_inactive=False)
        total_employees = len(active_employees)
        
        today_records = self.get_attendance_records(date=today)
        stats = {'Present': 0, 'Absent': 0, 'Leave': 0}
        for record in today_records:
            if record.status in stats:
                stats[record.status] += 1
                
        marked_count = sum(stats.values())
        unmarked = max(0, total_employees - marked_count)
        
        stats['TotalEmployees'] = total_employees
        stats['Unmarked'] = unmarked
        
        present = stats['Present']
        absent = stats['Absent'] + unmarked
        total_active_for_attendance = present + absent
        
        stats['AttendanceRate'] = round((present / total_active_for_attendance * 100), 1) if total_active_for_attendance > 0 else 0.0
        return stats

    def get_recent_activity(self, limit: int = 5) -> List[Attendance]:
        return self.attendance_repo.get_recent(limit)
