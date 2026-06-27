from database.db_manager import db
from datetime import datetime

class LeaveRequest(db.Model):
    """Leave Request entity."""
    __tablename__ = 'leaves'
    
    leave_id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer, db.ForeignKey('employees.user_id', ondelete='CASCADE'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    end_date = db.Column(db.String(10), nullable=False)    # YYYY-MM-DD
    status = db.Column(db.String(20), default='Pending', nullable=False)  # 'Pending', 'Approved', 'Rejected'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationship to Employee
    employee = db.relationship('Employee', backref=db.backref('leaves', cascade='all, delete-orphan', lazy=True))

    def __init__(self, emp_id: int, reason: str, start_date: str, end_date: str, 
                 status: str = 'Pending', is_active: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.emp_id = emp_id
        self.reason = reason
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.is_active = is_active

    def validate(self) -> dict:
        """Domain validations for dates and parameters."""
        errors = {}
        if not self.emp_id:
            errors['emp_id'] = 'Employee ID is required.'
        if not self.start_date:
            errors['start_date'] = 'Start date is required.'
        if not self.end_date:
            errors['end_date'] = 'End date is required.'
        
        if errors:
            return errors
            
        from datetime import date
        today = date.today()
        current_year = today.year
        max_year = current_year + 2
        
        start_dt = None
        end_dt = None
        
        try:
            if len(self.start_date) != 10 or self.start_date[4] != '-' or self.start_date[7] != '-':
                raise ValueError()
            start_dt = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        except (ValueError, IndexError):
            errors['start_date'] = 'Start date must be a valid date in YYYY-MM-DD format.'
            
        try:
            if len(self.end_date) != 10 or self.end_date[4] != '-' or self.end_date[7] != '-':
                raise ValueError()
            end_dt = datetime.strptime(self.end_date, '%Y-%m-%d').date()
        except (ValueError, IndexError):
            errors['end_date'] = 'End date must be a valid date in YYYY-MM-DD format.'
            
        if errors:
            return errors
            
        if start_dt.year < current_year or start_dt.year > max_year:
            errors['start_date'] = f'Start date year must be between {current_year} and {max_year}.'
        if end_dt.year < current_year or end_dt.year > max_year:
            errors['end_date'] = f'End date year must be between {current_year} and {max_year}.'
            
        if errors:
            return errors
            
        if start_dt < today:
            errors['start_date'] = 'Start date cannot be in the past.'
            
        if end_dt < start_dt:
            errors['end_date'] = 'End date cannot be earlier than start date.'
            
        if self.status not in ['Pending', 'Approved', 'Rejected']:
            errors['status'] = 'Status must be Pending, Approved, or Rejected.'
            
        return errors

    @property
    def employee_name(self) -> str:
        """Returns the name of the requesting employee safely."""
        return self.employee.name if self.employee else None

    @property
    def department_name(self) -> str:
        """Returns the name of the employee's department safely."""
        return self.employee.department.department_name if self.employee and self.employee.department else 'Unassigned'

    def to_dict(self) -> dict:
        return {
            'leave_id': self.leave_id,
            'emp_id': self.emp_id,
            'employee_name': self.employee_name,
            'department_name': self.department_name,
            'reason': self.reason,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'is_active': self.is_active
        }
