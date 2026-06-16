from database.db import DB
from models.attendance import Attendance
from datetime import datetime

class AttendanceService:
    @staticmethod
    def get_attendance_records(date=None, emp_id=None, department_id=None):
        """
        Retrieves attendance records with optional filters for date, employee, and department.
        """
        query = """
            SELECT a.*, e.name as employee_name, d.department_name
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if date:
            query += " AND a.date = ?"
            params.append(date)
        if emp_id:
            query += " AND a.emp_id = ?"
            params.append(emp_id)
        if department_id:
            query += " AND e.department_id = ?"
            params.append(department_id)
            
        query += " ORDER BY a.date DESC, e.name ASC"
        rows = DB.execute_query(query, params, fetch_all=True)
        return [Attendance.from_row(row) for row in rows]

    @staticmethod
    def get_attendance_by_id(attendance_id):
        query = """
            SELECT a.*, e.name as employee_name
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.attendance_id = ?
        """
        row = DB.execute_query(query, (attendance_id,), fetch_one=True)
        return Attendance.from_row(row) if row else None

    @staticmethod
    def mark_attendance(emp_id, date, status):
        """
        Marks attendance for an employee on a given date.
        If a record already exists, it updates it. (Upsert behavior)
        """
        # Check if record already exists
        check_query = "SELECT attendance_id FROM attendance WHERE emp_id = ? AND date = ?"
        existing = DB.execute_query(check_query, (emp_id, date), fetch_one=True)
        
        if existing:
            query = "UPDATE attendance SET status = ? WHERE attendance_id = ?"
            DB.execute_query(query, (status, existing['attendance_id']))
            return existing['attendance_id']
        else:
            query = "INSERT INTO attendance (emp_id, date, status) VALUES (?, ?, ?)"
            return DB.execute_query(query, (emp_id, date, status))

    @staticmethod
    def update_attendance(attendance_id, status):
        query = "UPDATE attendance SET status = ? WHERE attendance_id = ?"
        DB.execute_query(query, (status, attendance_id))

    @staticmethod
    def delete_attendance(attendance_id):
        query = "DELETE FROM attendance WHERE attendance_id = ?"
        DB.execute_query(query, (attendance_id,))

    @staticmethod
    def get_today_stats():
        """
        Returns stats for today's attendance.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get count of total active employees
        emp_count_query = "SELECT COUNT(*) as count FROM employees"
        total_emp_row = DB.execute_query(emp_count_query, fetch_one=True)
        total_employees = total_emp_row['count'] if total_emp_row else 0
        
        # Get attendance status counts for today
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM attendance 
            WHERE date = ? 
            GROUP BY status
        """
        rows = DB.execute_query(status_query, (today,), fetch_all=True)
        
        stats = {'Present': 0, 'Absent': 0, 'Leave': 0}
        for row in rows:
            if row['status'] in stats:
                stats[row['status']] = row['count']
                
        # Employees who haven't been marked are considered "Unmarked" or "Absent" by default,
        # but let's just show counts of explicit marks.
        # To make it realistic, unmarked = total_employees - sum(marked)
        marked_count = sum(stats.values())
        unmarked = max(0, total_employees - marked_count)
        
        # Let's count unmarked as absent for attendance calculation if appropriate,
        # but for visual dashboard:
        stats['TotalEmployees'] = total_employees
        stats['Unmarked'] = unmarked
        
        # Calculate attendance percentage
        # Present / (Present + Absent) * 100
        present = stats['Present']
        absent = stats['Absent'] + unmarked # Treat unmarked as absent/not present
        total_active_for_attendance = present + absent
        
        stats['AttendanceRate'] = round((present / total_active_for_attendance * 100), 1) if total_active_for_attendance > 0 else 0.0
        
        return stats

    @staticmethod
    def get_recent_activity(limit=5):
        query = """
            SELECT a.*, e.name as employee_name
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            ORDER BY a.attendance_id DESC
            LIMIT ?
        """
        rows = DB.execute_query(query, (limit,), fetch_all=True)
        return [Attendance.from_row(row) for row in rows]
