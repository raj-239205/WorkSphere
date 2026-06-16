from database.db import DB
from models.employee import Employee

class EmployeeService:
    @staticmethod
    def get_all_employees(search_query=None, department_id=None):
        """
        Retrieves all employees, optionally filtered by department and search text.
        """
        query = """
            SELECT e.*, d.department_name
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        
        if department_id:
            query += " AND e.department_id = ?"
            params.append(department_id)
            
        if search_query:
            query += " AND (e.name LIKE ? OR e.email LIKE ? OR e.designation LIKE ?)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_param])
            
        query += " ORDER BY e.name ASC"
        
        rows = DB.execute_query(query, params, fetch_all=True)
        return [Employee.from_row(row) for row in rows]

    @staticmethod
    def get_employee_by_id(emp_id):
        query = """
            SELECT e.*, d.department_name
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE e.emp_id = ?
        """
        row = DB.execute_query(query, (emp_id,), fetch_one=True)
        return Employee.from_row(row) if row else None

    @staticmethod
    def get_employee_by_email(email):
        query = "SELECT * FROM employees WHERE email = ?"
        row = DB.execute_query(query, (email,), fetch_one=True)
        return Employee.from_row(row) if row else None

    @staticmethod
    def create_employee(name, email, phone, department_id, salary, designation):
        # Validate unique email
        existing = EmployeeService.get_employee_by_email(email)
        if existing:
            raise ValueError(f"An employee with email '{email}' already exists.")
            
        query = """
            INSERT INTO employees (name, email, phone, department_id, salary, designation)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return DB.execute_query(query, (name, email, phone, department_id, salary, designation))

    @staticmethod
    def update_employee(emp_id, name, email, phone, department_id, salary, designation):
        # Validate unique email excluding self
        existing = EmployeeService.get_employee_by_email(email)
        if existing and existing.emp_id != int(emp_id):
            raise ValueError(f"An employee with email '{email}' already exists.")
            
        query = """
            UPDATE employees
            SET name = ?, email = ?, phone = ?, department_id = ?, salary = ?, designation = ?
            WHERE emp_id = ?
        """
        DB.execute_query(query, (name, email, phone, department_id, salary, designation, emp_id))

    @staticmethod
    def delete_employee(emp_id):
        # Note: cascade delete triggers will handle attendance and leaves if foreign keys are configured correctly.
        query = "DELETE FROM employees WHERE emp_id = ?"
        DB.execute_query(query, (emp_id,))
