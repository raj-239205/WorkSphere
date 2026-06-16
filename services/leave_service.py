from database.db import DB
from models.leave import Leave
from services.attendance_service import AttendanceService
from datetime import datetime, timedelta

class LeaveService:
    @staticmethod
    def get_leave_requests(status=None, emp_id=None):
        """
        Retrieves leave requests, optionally filtered by status and employee.
        """
        query = """
            SELECT l.*, e.name as employee_name, d.department_name
            FROM leaves l
            JOIN employees e ON l.emp_id = e.emp_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND l.status = ?"
            params.append(status)
        if emp_id:
            query += " AND l.emp_id = ?"
            params.append(emp_id)
            
        query += " ORDER BY CASE WHEN l.status = 'Pending' THEN 1 ELSE 2 END, l.start_date DESC"
        rows = DB.execute_query(query, params, fetch_all=True)
        return [Leave.from_row(row) for row in rows]

    @staticmethod
    def get_leave_by_id(leave_id):
        query = """
            SELECT l.*, e.name as employee_name
            FROM leaves l
            JOIN employees e ON l.emp_id = e.emp_id
            WHERE l.leave_id = ?
        """
        row = DB.execute_query(query, (leave_id,), fetch_one=True)
        return Leave.from_row(row) if row else None

    @staticmethod
    def apply_leave(emp_id, reason, start_date, end_date):
        # Check for overlapping leave requests (Pending or Approved)
        overlap_query = """
            SELECT COUNT(*) as count 
            FROM leaves 
            WHERE emp_id = ? 
              AND status != 'Rejected'
              AND ? <= end_date 
              AND ? >= start_date
        """
        result = DB.execute_query(overlap_query, (emp_id, start_date, end_date), fetch_one=True)
        if result and result['count'] > 0:
            raise ValueError("You have an overlapping leave request during this period.")

        query = """
            INSERT INTO leaves (emp_id, reason, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """
        return DB.execute_query(query, (emp_id, reason, start_date, end_date))

    @staticmethod
    def update_leave_status(leave_id, status):
        """
        Approves or rejects a leave request.
        If approved, automatically logs 'Leave' in the attendance table for the date range.
        """
        if status not in ['Approved', 'Rejected', 'Pending']:
            raise ValueError("Invalid status value.")
            
        query = "UPDATE leaves SET status = ? WHERE leave_id = ?"
        DB.execute_query(query, (status, leave_id))
        
        # If approved, automatically populate attendance as 'Leave' for the dates
        if status == 'Approved':
            leave = LeaveService.get_leave_by_id(leave_id)
            if leave:
                start = datetime.strptime(leave.start_date, '%Y-%m-%d')
                end = datetime.strptime(leave.end_date, '%Y-%m-%d')
                curr = start
                while curr <= end:
                    date_str = curr.strftime('%Y-%m-%d')
                    # Mark attendance as Leave
                    AttendanceService.mark_attendance(leave.emp_id, date_str, 'Leave')
                    curr += timedelta(days=1)

    @staticmethod
    def get_pending_count():
        query = "SELECT COUNT(*) as count FROM leaves WHERE status = 'Pending'"
        row = DB.execute_query(query, fetch_one=True)
        return row['count'] if row else 0

    @staticmethod
    def get_recent_requests(limit=5):
        query = """
            SELECT l.*, e.name as employee_name
            FROM leaves l
            JOIN employees e ON l.emp_id = e.emp_id
            ORDER BY l.leave_id DESC
            LIMIT ?
        """
        rows = DB.execute_query(query, (limit,), fetch_all=True)
        return [Leave.from_row(row) for row in rows]
        
    @staticmethod
    def delete_leave(leave_id):
        query = "DELETE FROM leaves WHERE leave_id = ?"
        DB.execute_query(query, (leave_id,))
