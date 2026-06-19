class WorkSphereException(Exception):
    """Base exception class for the WorkSphere platform."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class EmployeeNotFoundException(WorkSphereException):
    def __init__(self, message: str = "Employee record not found"):
        super().__init__(message, 404)

class DepartmentNotFoundException(WorkSphereException):
    def __init__(self, message: str = "Department record not found"):
        super().__init__(message, 404)

class LeaveValidationException(WorkSphereException):
    def __init__(self, message: str = "Invalid leave dates or overlap detected"):
        super().__init__(message, 400)

class AttendanceValidationException(WorkSphereException):
    def __init__(self, message: str = "Invalid attendance parameters"):
        super().__init__(message, 400)

class UnauthorizedAccessException(WorkSphereException):
    def __init__(self, message: str = "You do not have permission to access this resource"):
        super().__init__(message, 403)
