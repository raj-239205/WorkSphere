import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """Configures application-wide logging with file and console channels."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # 1. Info & General Application Log Handler
    info_log_path = os.path.join(log_dir, 'app.log')
    info_handler = RotatingFileHandler(info_log_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(log_format)

    # 2. Error Log Handler
    error_log_path = os.path.join(log_dir, 'errors.log')
    error_handler = RotatingFileHandler(error_log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)

    # 3. Console Handler (for debug/development outputs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)

    # Attach all handlers to Flask app logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(info_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)

    app.logger.info("Logging infrastructure initialized successfully.")
