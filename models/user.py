from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, user_id=None, username=None, password=None, role=None, emp_id=None):
        self.user_id = user_id
        self.username = username
        self.password = password  # This will store the hashed password
        self.role = role          # 'Admin', 'HR', 'Employee'
        self.emp_id = emp_id      # Links to employee if role is 'Employee'

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        data = dict(row)
        return cls(
            user_id=data.get('user_id'),
            username=data.get('username'),
            password=data.get('password'),
            role=data.get('role'),
            emp_id=data.get('emp_id')
        )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if not self.password:
            return False
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'emp_id': self.emp_id
        }

    def validate(self):
        errors = {}
        if not self.username or not self.username.strip():
            errors['username'] = 'Username is required.'
        if not self.role or self.role not in ['Admin', 'HR', 'Employee']:
            errors['role'] = 'Role must be Admin, HR, or Employee.'
        return errors
