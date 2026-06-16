from datetime import datetime

class Leave:
    def __init__(self, leave_id=None, emp_id=None, reason=None, start_date=None, end_date=None, status='Pending', employee_name=None):
        self.leave_id = leave_id
        self.emp_id = emp_id
        self.reason = reason
        self.start_date = start_date  # YYYY-MM-DD
        self.end_date = end_date      # YYYY-MM-DD
        self.status = status          # 'Pending', 'Approved', 'Rejected'
        self.employee_name = employee_name  # Joined attribute

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        data = dict(row)
        return cls(
            leave_id=data.get('leave_id'),
            emp_id=data.get('emp_id'),
            reason=data.get('reason'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            status=data.get('status', 'Pending'),
            employee_name=data.get('employee_name')
        )

    def to_dict(self):
        return {
            'leave_id': self.leave_id,
            'emp_id': self.emp_id,
            'reason': self.reason,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'employee_name': self.employee_name
        }

    def validate(self):
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
        
        # Parse and validate start date format
        try:
            if len(self.start_date) != 10 or self.start_date[4] != '-' or self.start_date[7] != '-':
                raise ValueError()
            start_dt = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        except (ValueError, IndexError):
            errors['start_date'] = 'Start date must be a valid date in YYYY-MM-DD format.'
            
        # Parse and validate end date format
        try:
            if len(self.end_date) != 10 or self.end_date[4] != '-' or self.end_date[7] != '-':
                raise ValueError()
            end_dt = datetime.strptime(self.end_date, '%Y-%m-%d').date()
        except (ValueError, IndexError):
            errors['end_date'] = 'End date must be a valid date in YYYY-MM-DD format.'
            
        if errors:
            return errors
            
        # Validate unrealistic year bounds (e.g. 202666)
        if start_dt.year < current_year or start_dt.year > max_year:
            errors['start_date'] = f'Start date year must be between {current_year} and {max_year}.'
        if end_dt.year < current_year or end_dt.year > max_year:
            errors['end_date'] = f'End date year must be between {current_year} and {max_year}.'
            
        if errors:
            return errors
            
        # Validate start date is not in the past
        if start_dt < today:
            errors['start_date'] = 'Start date cannot be in the past.'
            
        # Validate end date is not before start date
        if end_dt < start_dt:
            errors['end_date'] = 'End date cannot be earlier than start date.'
            
        if not self.status or self.status not in ['Pending', 'Approved', 'Rejected']:
            errors['status'] = 'Status must be Pending, Approved, or Rejected.'
            
        return errors

