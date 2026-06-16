import re

class Employee:
    def __init__(self, emp_id=None, name=None, email=None, phone=None, department_id=None, salary=0.0, designation=None, department_name=None):
        self.emp_id = emp_id
        self.name = name
        self.email = email
        self.phone = phone
        self.department_id = department_id
        self.salary = salary
        self.designation = designation
        self.department_name = department_name  # Joined attribute for display convenience

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        data = dict(row)
        return cls(
            emp_id=data.get('emp_id'),
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            department_id=data.get('department_id'),
            salary=data.get('salary', 0.0),
            designation=data.get('designation'),
            department_name=data.get('department_name')
        )

    def to_dict(self):
        return {
            'emp_id': self.emp_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department_id': self.department_id,
            'salary': self.salary,
            'designation': self.designation,
            'department_name': self.department_name
        }

    def validate(self):
        errors = {}
        if not self.name or not self.name.strip():
            errors['name'] = 'Name is required.'
        if not self.email or not self.email.strip():
            errors['email'] = 'Email is required.'
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            errors['email'] = 'Invalid email address format.'
        if self.salary is not None:
            try:
                val = float(self.salary)
                if val < 0:
                    errors['salary'] = 'Salary must be a non-negative number.'
            except ValueError:
                errors['salary'] = 'Salary must be a valid number.'
        if not self.department_id:
            errors['department_id'] = 'Department is required.'
        return errors
