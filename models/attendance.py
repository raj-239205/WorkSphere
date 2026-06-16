class Attendance:
    def __init__(self, attendance_id=None, emp_id=None, date=None, status=None, employee_name=None):
        self.attendance_id = attendance_id
        self.emp_id = emp_id
        self.date = date  # YYYY-MM-DD
        self.status = status  # 'Present', 'Absent', 'Leave'
        self.employee_name = employee_name  # Joined attribute

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        data = dict(row)
        return cls(
            attendance_id=data.get('attendance_id'),
            emp_id=data.get('emp_id'),
            date=data.get('date'),
            status=data.get('status'),
            employee_name=data.get('employee_name')
        )

    def to_dict(self):
        return {
            'attendance_id': self.attendance_id,
            'emp_id': self.emp_id,
            'date': self.date,
            'status': self.status,
            'employee_name': self.employee_name
        }

    def validate(self):
        errors = {}
        if not self.emp_id:
            errors['emp_id'] = 'Employee ID is required.'
        if not self.date:
            errors['date'] = 'Date is required.'
        if not self.status or self.status not in ['Present', 'Absent', 'Leave']:
            errors['status'] = 'Status must be Present, Absent, or Leave.'
        return errors
