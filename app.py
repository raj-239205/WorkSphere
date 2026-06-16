from flask import Flask, render_template, redirect, url_for, session, request
from config import Config
from blueprints import auth_bp, dashboard_bp, employee_bp, attendance_bp, leave_bp, department_bp, reports_bp, api_bp
import os

app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(leave_bp)
app.register_blueprint(department_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(api_bp)


# HTTP 403 Forbidden handler
@app.errorhandler(403)
def forbidden(error):
    return render_template('access_denied.html'), 403

# HTTP 404 Not Found handler
@app.errorhandler(404)
def not_found(error):
    # If the user is logged in, redirect them to dashboard, otherwise redirect to login
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

# Context processor to inject active path helper into templates
@app.context_processor
def inject_active_class():
    def active_class(blueprint_name):
        return 'active' if request.blueprint == blueprint_name else ''
    return dict(active_class=active_class)

if __name__ == '__main__':
    # Check if database is initialized, if not, bootstrap automatically
    if not os.path.exists(Config.DATABASE_PATH):
        print("Database erp.db not found. Bootstrapping...")
        from init_db import initialize_database, seed_data
        initialize_database()
        seed_data()
        
    # Running Flask on default local port 5000
    app.run(debug=True, port=5000)
