from database.db_manager import db

class Attendance(db.Model):
    """Attendance log entity."""
    __tablename__ = 'attendance'
    
    attendance_id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer, db.ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    status = db.Column(db.String(20), nullable=False)  # 'Present', 'Absent', 'Leave'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationship linkage to Employee
    employee = db.relationship('Employee', backref=db.backref('attendances', cascade='all, delete-orphan', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('emp_id', 'date', name='_emp_date_uc'),
    )

    def __init__(self, emp_id: int, date: str, status: str, is_active: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.emp_id = emp_id
        self.date = date
        self.status = status
        self.is_active = is_active

    @property
    def employee_name(self) -> str:
        """Returns the name of the employee safely."""
        return self.employee.name if self.employee else None

    @property
    def department_name(self) -> str:
        """Returns the name of the employee's department safely."""
        return self.employee.department.department_name if self.employee and self.employee.department else 'Unassigned'

    def to_dict(self) -> dict:
        return {
            'attendance_id': self.attendance_id,
            'emp_id': self.emp_id,
            'employee_name': self.employee_name,
            'department_name': self.department_name,
            'date': self.date,
            'status': self.status,
            'is_active': self.is_active
        }
