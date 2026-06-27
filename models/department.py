from database.db_manager import db

class Department(db.Model):
    """Department domain entity."""
    __tablename__ = 'departments'
    
    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(80), unique=True, nullable=False)
    manager_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # One-to-Many relationship (back_populates matches Employee.department)
    employees = db.relationship('Employee', back_populates='department', lazy=True)

    def __init__(self, department_name: str, manager_name: str = None, is_active: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.department_name = department_name
        self.manager_name = manager_name
        self.is_active = is_active

    def validate(self) -> dict:
        """Domain validations for Department fields."""
        errors = {}
        if not self.department_name or not self.department_name.strip():
            errors['department_name'] = 'Department name is required.'
        return errors

    @property
    def employee_count(self) -> int:
        """Returns the count of active employees in the department."""
        return len([e for e in self.employees if e.is_active])

    def to_dict(self) -> dict:
        return {
            'department_id': self.department_id,
            'department_name': self.department_name,
            'manager_name': self.manager_name,
            'is_active': self.is_active,
            'employee_count': self.employee_count
        }
