class Department:
    def __init__(self, department_id=None, department_name=None, manager_name=None, employee_count=0):
        self.department_id = department_id
        self.department_name = department_name
        self.manager_name = manager_name
        self.employee_count = employee_count

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # Support both sqlite3.Row and dict
        data = dict(row)
        return cls(
            department_id=data.get('department_id'),
            department_name=data.get('department_name'),
            manager_name=data.get('manager_name'),
            employee_count=data.get('employee_count', 0)
        )

    def to_dict(self):
        return {
            'department_id': self.department_id,
            'department_name': self.department_name,
            'manager_name': self.manager_name,
            'employee_count': self.employee_count
        }

    def validate(self):
        errors = {}
        if not self.department_name or not self.department_name.strip():
            errors['department_name'] = 'Department name is required.'
        return errors
