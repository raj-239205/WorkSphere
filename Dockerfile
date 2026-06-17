# Use official lightweight Python image
FROM python:3.11-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Set working directory inside container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Bootstrap database schema and seed data
RUN python init_db.py

# Expose server port
EXPOSE 5000

# Start server using Gunicorn production WSGI HTTP server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
