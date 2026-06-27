from flask import Blueprint, render_template, request, send_file
from utils.security import permission_required
from services.report_service import ReportService
from services.department_service import DepartmentService
from services.analytics_service import AnalyticsService
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

report_service = ReportService()
department_service = DepartmentService()
analytics_service = AnalyticsService()

@reports_bp.route('/reports')
@permission_required('can_view_reports')
def index():
    dept_rows = report_service.get_salaries_report_data()
            
    # Leave Summary Data using Analytics Service
    analytics_data = analytics_service.get_workforce_analytics()
    leave_summary = analytics_data.get('leave_stats', {'Pending': 0, 'Approved': 0, 'Rejected': 0})
            
    # Monthly Attendance Trends (last 6 months)
    all_attendance = report_service.attendance_service.get_attendance_records()
    from collections import defaultdict
    monthly_data = defaultdict(lambda: {'Present': 0, 'Absent': 0, 'Leave': 0})
    for record in all_attendance:
        if record.date:
            month = record.date[:7]  # Extract YYYY-MM
            if record.status in monthly_data[month]:
                monthly_data[month][record.status] += 1
        
    months_labels = sorted(list(monthly_data.keys()))
    attendance_rates = []
    
    for m in months_labels:
        data = monthly_data[m]
        presents = data['Present']
        absents = data['Absent']
        total = presents + absents
        rate = round((presents / total * 100), 1) if total > 0 else 100.0
        attendance_rates.append(rate)
        
    # Formatting month labels (e.g. 2026-06 to Jun 2026)
    formatted_months = []
    for m in months_labels:
        try:
            dt = datetime.strptime(m, '%Y-%m')
            formatted_months.append(dt.strftime('%b %Y'))
        except ValueError:
            formatted_months.append(m)

    return render_template(
        'reports/analytics.html',
        dept_rows=dept_rows,
        leave_summary=leave_summary,
        months_labels=formatted_months,
        attendance_rates=attendance_rates
    )

@reports_bp.route('/reports/attendance')
@permission_required('can_view_reports')
def attendance_report():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    dept_id = request.args.get('department_id', '')
    
    # Default to past 30 days
    if not start_date or not end_date:
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
    selected_dept_id = int(dept_id) if dept_id and dept_id.isdigit() else None
    rows = report_service.get_attendance_report_data(start_date, end_date, selected_dept_id)
    departments = department_service.get_all_departments()
    
    return render_template(
        'reports/attendance.html',
        rows=rows,
        departments=departments,
        start_date=start_date,
        end_date=end_date,
        selected_dept=selected_dept_id
    )

@reports_bp.route('/reports/export/pdf')
@permission_required('can_view_reports')
def export_pdf():
    """Generates PDF report of workforce summary."""
    pdf_buf = report_service.export_pdf()
    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"WorkSphere_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

@reports_bp.route('/reports/export/excel')
@permission_required('can_view_reports')
def export_excel():
    """Generates Excel directory download of workforce."""
    excel_buf = report_service.export_excel()
    return send_file(
        excel_buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"WorkSphere_Directory_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )
