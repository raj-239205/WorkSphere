import os
from flask import Flask, render_template, redirect, url_for, session, request
from database.db_manager import db
from extensions import jwt, limiter
from flask_migrate import Migrate
from flasgger import Swagger
from utils.logging_setup import setup_logger
from blueprints import auth_bp, dashboard_bp, employee_bp, attendance_bp, leave_bp, department_bp, reports_bp, api_bp

def create_app(config_class=None):
    """Application Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    
    # Load configuration profile dynamically
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            from config.production import ProductionConfig
            config_class = ProductionConfig
        elif env == 'testing':
            from config.testing import TestingConfig
            config_class = TestingConfig
        else:
            from config.development import DevelopmentConfig
            config_class = DevelopmentConfig
            
    app.config.from_object(config_class)
    
    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    Migrate(app, db)
    Swagger(app)
    
    # Setup Rotating File Logging
    setup_logger(app)
    
    # Register Controller Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    
    # HTTP Error Handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('access_denied.html'), 403
        
    @app.errorhandler(404)
    def not_found(error):
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
        
    # Context Processor for active navigation states & RBAC
    @app.context_processor
    def inject_active_class():
        from utils.security import has_permission
        def active_class(blueprint_name):
            return 'active' if request.blueprint == blueprint_name else ''
        return dict(active_class=active_class, has_permission=has_permission)
        
    return app

# Expose app instance for development runners
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
