import logging
import os

def setup_logger(app):
    """Configure logging for local development and Vercel."""

    log_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    app.logger.handlers.clear()
    app.logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    app.logger.addHandler(console_handler)

    # Local file logging only (NOT on Vercel)
    if not os.environ.get("VERCEL"):
        from logging.handlers import RotatingFileHandler

        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "logs"
        )

        os.makedirs(log_dir, exist_ok=True)

        info_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )

        error_handler = RotatingFileHandler(
            os.path.join(log_dir, "errors.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=3
        )

        info_handler.setLevel(logging.INFO)
        error_handler.setLevel(logging.ERROR)

        info_handler.setFormatter(log_format)
        error_handler.setFormatter(log_format)

        app.logger.addHandler(info_handler)
        app.logger.addHandler(error_handler)

    app.logger.info("Logging initialized.")
