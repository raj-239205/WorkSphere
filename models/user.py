from database.db_manager import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """
    Base User class representing system credentials.
    Implements Joined Table Inheritance for different user roles.
    """
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password = db.Column('password', db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'User'
    }

    def __init__(self, username: str, role: str, is_active: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.role = role
        self.is_active = is_active

    @property
    def emp_id(self) -> int:
        """Compatibility property for legacy code expecting user.emp_id."""
        return self.user_id if self.role in ['Employee', 'HR', 'Admin'] else None

    @property
    def password(self) -> str:
        """Getter for password (encapsulation)."""
        return self._password

    @password.setter
    def password(self, plain_password: str) -> None:
        """Setter for password that enforces hashing on set."""
        if not plain_password or len(plain_password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        self._password = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """Verification method for hashed password."""
        return check_password_hash(self._password, plain_password)

    def generate_dashboard(self) -> dict:
        """Polymorphic dashboard generation (to be overridden)."""
        raise NotImplementedError("Subclasses must implement this method")


class Employee(User):
    """
    Employee model holding profile metrics.
    Inherits user properties (credentials) via Joined Table Inheritance.
    """
    __tablename__ = 'employees'
    
    # ForeignKey links back to users primary key (polymorphic relation)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id', ondelete='SET NULL'), nullable=True)
    _salary = db.Column('salary', db.Float, default=0.0, nullable=False)
    designation = db.Column(db.String(100), nullable=True)

    # Relationship linkage to Department
    department = db.relationship('Department', back_populates='employees', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Employee'
    }

    def __init__(self, username: str = None, name: str = None, email: str = None, phone: str = None, 
                 department_id: int = None, salary: float = 0.0, designation: str = None, role: str = 'Employee', **kwargs):
        if not username and email:
            username = email.split('@')[0]
        super().__init__(username or '', role, **kwargs)
        self.name = name
        self.email = email
        self.phone = phone
        self.department_id = department_id
        self.salary = salary  # Utilizes setter validation
        self.designation = designation

    def validate(self) -> dict:
        """Domain validations for Employee fields."""
        import re
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
                    errors['salary'] = 'Salary details must be a non-negative number.'
            except (ValueError, TypeError):
                errors['salary'] = 'Salary must be a valid float value.'
        if not self.department_id:
            errors['department_id'] = 'Department is required.'
        return errors

    @property
    def salary(self) -> float:
        """Getter for private salary (encapsulation)."""
        return self._salary

    @salary.setter
    def salary(self, value: float) -> None:
        """Setter for salary that enforces bounds check."""
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Salary must be a valid float value.")
        if val < 0:
            raise ValueError("Salary details must be a non-negative number.")
        self._salary = val

    def generate_dashboard(self) -> dict:
        """Overrides base class to compile personal metrics (polymorphism)."""
        from services.attendance_service import AttendanceService
        from services.leave_service import LeaveService
        
        attendance_service = AttendanceService()
        leave_service = LeaveService()
        
        my_attendance = attendance_service.get_attendance_records(emp_id=self.user_id)
        my_leaves = leave_service.get_leave_requests(emp_id=self.user_id)
        
        presents = sum(1 for a in my_attendance if a.status == 'Present')
        absents = sum(1 for a in my_attendance if a.status == 'Absent')
        total = presents + absents
        attendance_rate = round((presents / total * 100), 1) if total > 0 else 100.0
        
        return {
            "role": "Employee",
            "role_display": "Employee",
            "employee": self,
            "attendance_rate": attendance_rate,
            "recent_attendance": my_attendance[:5],
            "recent_leaves": my_leaves[:5]
        }
        
    @property
    def department_name(self) -> str:
        """Helper to get department name as a string safely."""
        return self.department.department_name if self.department else 'Unassigned'

    def to_dict(self) -> dict:
        """Serialize employee object to dict."""
        return {
            'emp_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department_id': self.department_id,
            'department_name': self.department_name,
            'salary': self.salary,
            'designation': self.designation,
            'role': self.role,
            'username': self.username,
            'is_active': self.is_active
        }


class Admin(Employee):
    """Admin user role."""
    __mapper_args__ = {
        'polymorphic_identity': 'Admin'
    }

    def __init__(self, username: str, name: str = "System Administrator", email: str = "admin@worksphere.com", **kwargs):
        super().__init__(username=username, name=name, email=email, role='Admin', **kwargs)

    def generate_dashboard(self) -> dict:
        """Overrides base class to compile Admin metrics (polymorphism)."""
        from services.attendance_service import AttendanceService
        from services.leave_service import LeaveService
        from services.department_service import DepartmentService
        
        attendance_service = AttendanceService()
        leave_service = LeaveService()
        department_service = DepartmentService()
        
        return {
            "role": "Admin",
            "role_display": "System Administrator",
            "stats": attendance_service.get_today_stats(),
            "pending_leaves": leave_service.get_pending_count(),
            "recent_attendance": attendance_service.get_recent_activity(5),
            "recent_leaves": leave_service.get_recent_requests(5),
            "departments": department_service.get_all_departments()
        }


class HR(Employee):
    """HR user role."""
    __mapper_args__ = {
        'polymorphic_identity': 'HR'
    }

    def __init__(self, username: str, name: str = "HR Manager", email: str = "hr@worksphere.com", **kwargs):
        super().__init__(username=username, name=name, email=email, role='HR', **kwargs)

    def generate_dashboard(self) -> dict:
        """Overrides base class to compile HR metrics (polymorphism)."""
        from services.attendance_service import AttendanceService
        from services.leave_service import LeaveService
        from services.department_service import DepartmentService
        
        attendance_service = AttendanceService()
        leave_service = LeaveService()
        department_service = DepartmentService()
        
        return {
            "role": "HR",
            "role_display": "HR Manager",
            "stats": attendance_service.get_today_stats(),
            "pending_leaves": leave_service.get_pending_count(),
            "recent_attendance": attendance_service.get_recent_activity(5),
            "recent_leaves": leave_service.get_recent_requests(5),
            "departments": department_service.get_all_departments()
        }
