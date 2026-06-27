import threading
import json
from datetime import datetime
from functools import wraps
from flask import has_request_context, request, session, render_template, jsonify, redirect
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from config import BaseConfig
import os
from exceptions.custom_exceptions import UnauthorizedAccessException

DATABASE_PATH = os.path.join(BaseConfig.BASE_DIR, 'database', 'erp.db')

# Thread-local storage for security context (used in unit tests / direct service calls)
_security_context = threading.local()

class SecurityContext:
    def __init__(self, user_id=None, username=None, role=None):
        self.user_id = user_id
        self.username = username
        self.role = role

    def __enter__(self):
        self.old_context = getattr(_security_context, 'current', None)
        _security_context.current = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _security_context.current = self.old_context

ROLE_PERMISSIONS = {
    'Admin': {
        'can_view_employees', 'can_add_employee', 'can_edit_employee', 'can_delete_employee',
        'can_view_departments', 'can_add_department', 'can_edit_department', 'can_delete_department',
        'can_view_attendance', 'can_manage_attendance',
        'can_view_leaves', 'can_approve_leave',
        'can_view_reports', 'can_view_analytics',
        'can_manage_users', 'can_manage_roles', 'can_view_audit_logs',
        'can_view_own_profile', 'can_view_own_attendance', 'can_view_own_leaves'
    },
    'HR': {
        'can_view_employees', 'can_add_employee', 'can_edit_employee',
        'can_view_departments',
        'can_view_attendance', 'can_manage_attendance',
        'can_view_leaves', 'can_approve_leave',
        'can_view_reports', 'can_view_analytics',
        'can_view_own_profile', 'can_view_own_attendance', 'can_view_own_leaves'
    },
    'Employee': {
        'can_view_own_profile', 'can_view_own_attendance', 'can_view_own_leaves'
    }
}

def has_permission(role, permission):
    if not role or role not in ROLE_PERMISSIONS:
        return False
    return permission in ROLE_PERMISSIONS[role]

def get_current_user_details():
    # 1. Thread-local security context (takes precedence for testing/direct calls)
    current = getattr(_security_context, 'current', None)
    if current is not None:
        return {
            'user_id': current.user_id,
            'username': current.username,
            'role': current.role
        }

    # 2. Flask request context
    if has_request_context():
        # Check Session (Web UI)
        if 'user_id' in session:
            return {
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'role': session.get('role')
            }
        
        # Check JWT (REST API)
        try:
            if 'Authorization' in request.headers or request.cookies.get('access_token_cookie'):
                verify_jwt_in_request(optional=True)
                identity_str = get_jwt_identity()
                if identity_str:
                    identity = json.loads(identity_str) if isinstance(identity_str, str) else identity_str
                    return {
                        'user_id': identity.get('user_id'),
                        'username': identity.get('username'),
                        'role': identity.get('role')
                    }
        except Exception:
            pass

    return None

def log_auth_event(user_id, username, role, permission, action, result, ip_address):
    """Logs the authorization event using an independent SQLAlchemy session to remain database-agnostic."""
    try:
        from database.db_manager import db
        from models.activity_log import ActivityLog
        from sqlalchemy.orm import sessionmaker
        
        log_details = {
            "permission_checked": permission,
            "action_attempted": action,
            "role": role,
            "username": username,
            "result": result
        }
        
        # Create an independent session utilizing the app's engine
        # This keeps the logging operation decoupled from any pending/failed transaction in the main thread session.
        Session = sessionmaker(bind=db.engine)
        session = Session()
        try:
            log_entry = ActivityLog(
                user_id=user_id,
                action_type=action,
                ip_address=ip_address,
                new_value=json.dumps(log_details)
            )
            log_entry.timestamp = datetime.utcnow()
            session.add(log_entry)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        print(f"Audit log write failed: {e}")

def check_permission(permission, action_attempted=None):
    """
    Service layer and route helper to enforce permissions.
    If unauthorized, logs denial and raises UnauthorizedAccessException.
    If called outside of context (no request context & no security context), bypasses checks.
    """
    user_details = get_current_user_details()
    if user_details is None:
        # Bypass when called offline (database seeding / CLI startup)
        return True
        
    user_id = user_details.get('user_id')
    username = user_details.get('username')
    role = user_details.get('role')
    
    is_allowed = has_permission(role, permission)
    result = "Allowed" if is_allowed else "Denied"
    
    ip_addr = request.remote_addr if (has_request_context() and request) else "127.0.0.1"
    action = action_attempted or f"Permission Check: {permission}"
    
    log_auth_event(user_id, username, role, permission, action, result, ip_addr)
    
    if not is_allowed:
        raise UnauthorizedAccessException(f"Access Denied: Role '{role}' lacks permission '{permission}'")
        
    return True

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_request_context() or 'user_id' not in session:
                return redirect('/login')
            try:
                check_permission(permission, action_attempted=f"{f.__name__} (Route Access)")
            except UnauthorizedAccessException:
                return render_template('access_denied.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                check_permission(permission, action_attempted=f"{f.__name__} (API Access)")
            except UnauthorizedAccessException:
                return jsonify({"error": "Forbidden: You do not have permission to access this resource"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
