from database.db import DB
from models.department import Department

class DepartmentService:
    @staticmethod
    def get_all_departments():
        """
        Retrieves all departments, including the headcount of employees in each.
        """
        query = """
            SELECT d.department_id, d.department_name, d.manager_name, COUNT(e.emp_id) as employee_count
            FROM departments d
            LEFT JOIN employees e ON d.department_id = e.department_id
            GROUP BY d.department_id
            ORDER BY d.department_name
        """
        rows = DB.execute_query(query, fetch_all=True)
        return [Department.from_row(row) for row in rows]

    @staticmethod
    def get_department_by_id(department_id):
        query = "SELECT * FROM departments WHERE department_id = ?"
        row = DB.execute_query(query, (department_id,), fetch_one=True)
        return Department.from_row(row) if row else None

    @staticmethod
    def get_department_by_name(department_name):
        query = "SELECT * FROM departments WHERE department_name = ?"
        row = DB.execute_query(query, (department_name,), fetch_one=True)
        return Department.from_row(row) if row else None

    @staticmethod
    def create_department(department_name, manager_name):
        # Validate uniqueness
        existing = DepartmentService.get_department_by_name(department_name)
        if existing:
            raise ValueError(f"Department '{department_name}' already exists.")
            
        query = "INSERT INTO departments (department_name, manager_name) VALUES (?, ?)"
        return DB.execute_query(query, (department_name, manager_name))

    @staticmethod
    def update_department(department_id, department_name, manager_name):
        # Validate uniqueness excluding self
        existing = DepartmentService.get_department_by_name(department_name)
        if existing and existing.department_id != int(department_id):
            raise ValueError(f"Department '{department_name}' already exists.")
            
        query = "UPDATE departments SET department_name = ?, manager_name = ? WHERE department_id = ?"
        DB.execute_query(query, (department_name, manager_name, department_id))

    @staticmethod
    def delete_department(department_id):
        # Check if department has employees
        check_query = "SELECT COUNT(*) as count FROM employees WHERE department_id = ?"
        result = DB.execute_query(check_query, (department_id,), fetch_one=True)
        if result and result['count'] > 0:
            raise ValueError("Cannot delete department because it has active employees. Reassign employees first.")
            
        query = "DELETE FROM departments WHERE department_id = ?"
        DB.execute_query(query, (department_id,))
