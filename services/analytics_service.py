import os
from datetime import datetime
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend for server environments
import matplotlib.pyplot as plt

from database.db_manager import db
from models.user import Employee
from models.attendance import Attendance
from models.leave import LeaveRequest
from models.department import Department
from services.base_service import BaseService

class AnalyticsService(BaseService):
    """Business Intelligence and Data Science Analytics service."""

    def __init__(self):
        self.charts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'charts')
        if not os.environ.get("VERCEL"):
            os.makedirs(self.charts_dir, exist_ok=True)

    def get_workforce_analytics(self) -> dict:
        """Computes statistical metrics on salaries, departments, attendance, and leaves using Pandas/NumPy."""
        from utils.security import check_permission
        check_permission('can_view_analytics', "Get Workforce Analytics")
        default_stats = {
            "headcount": 0,
            "avg_salary": 0.0,
            "median_salary": 0.0,
            "std_salary": 0.0,
            "dept_distribution": {},
            "attendance_stats": {
                "mean_rate": 0.0,
                "median_rate": 0.0,
                "std_rate": 0.0
            },
            "leave_stats": {
                "Pending": 0,
                "Approved": 0,
                "Rejected": 0
            }
        }
        try:
            # 1. Load active employees
            employees = db.session.query(Employee).filter(Employee.is_active == True).all()
            if not employees:
                return default_stats

            emp_data = [{
                'emp_id': emp.user_id,
                'name': emp.name,
                'salary': emp.salary,
                'department': emp.department.department_name if emp.department else 'Unassigned'
            } for emp in employees]
            
            df_emp = pd.DataFrame(emp_data)

            # Salary statistics via NumPy / Pandas
            salaries = df_emp['salary'].to_numpy()
            avg_salary = float(np.mean(salaries))
            median_salary = float(np.median(salaries))
            std_salary = float(np.std(salaries)) if len(salaries) > 1 else 0.0

            # Department headcount aggregation
            dept_counts = df_emp['department'].value_counts().to_dict()

            # 2. Load attendance records
            attendance = db.session.query(Attendance).filter(Attendance.is_active == True).all()
            att_stats = {
                "mean_rate": 0.0,
                "median_rate": 0.0,
                "std_rate": 0.0
            }
            if attendance:
                att_data = [{
                    'date': att.date,
                    'status': att.status,
                    'emp_id': att.emp_id
                } for att in attendance]
                df_att = pd.DataFrame(att_data)

                # Calculate daily attendance rates
                daily_rates = []
                for date, group in df_att.groupby('date'):
                    presents = len(group[group['status'] == 'Present'])
                    total = len(group[group['status'].isin(['Present', 'Absent'])])
                    rate = (presents / total * 100) if total > 0 else 100.0
                    daily_rates.append(rate)

                daily_rates_np = np.array(daily_rates)
                if len(daily_rates_np) > 0:
                    att_stats = {
                        "mean_rate": float(np.mean(daily_rates_np)),
                        "median_rate": float(np.median(daily_rates_np)),
                        "std_rate": float(np.std(daily_rates_np)) if len(daily_rates_np) > 1 else 0.0
                    }

            # 3. Load leave requests
            leaves = db.session.query(LeaveRequest).filter(LeaveRequest.is_active == True).all()
            leave_counts = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
            if leaves:
                leave_data = [{'status': l.status} for l in leaves]
                df_leave = pd.DataFrame(leave_data)
                counts = df_leave['status'].value_counts().to_dict()
                for status in leave_counts:
                    leave_counts[status] = int(counts.get(status, 0))

            return {
                "headcount": len(employees),
                "avg_salary": round(avg_salary, 2),
                "median_salary": round(median_salary, 2),
                "std_salary": round(std_salary, 2),
                "dept_distribution": dept_counts,
                "attendance_stats": att_stats,
                "leave_stats": leave_counts
            }
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error calculating workforce analytics: {str(e)}", exc_info=True)
            return default_stats

    def generate_charts(self) -> dict:
        """Generates and saves dynamic Matplotlib PNG charts to static/charts/."""
        from utils.security import check_permission
        check_permission('can_view_analytics', "Generate Analytics Charts")
        
        # On Vercel, the filesystem is read-only, so we bypass actual file generation
        if os.environ.get("VERCEL"):
            return {
                'department_headcount': '/static/charts/department_headcount.png',
                'leave_distribution': '/static/charts/leave_distribution.png',
                'attendance_trends': '/static/charts/attendance_trends.png',
                'attendance_heatmap': '/static/charts/attendance_heatmap.png'
            }
            
        try:
            # 1. Retrieve Data
            analytics_data = self.get_workforce_analytics()
            
            # Color Palettes
            primary_color = '#4f46e5'  # Sleek Indigo
            secondary_color = '#10b981' # Emerald Green
            accent_color = '#f59e0b'    # Amber Gold
            danger_color = '#ef4444'    # Crimson Red
            bg_dark_theme = '#1e1b4b'   # Dark Indigo
            
            chart_paths = {}

            plt.style.use('ggplot')
            plt.rcParams.update({
                'font.family': 'sans-serif',
                'font.size': 10,
                'figure.facecolor': '#f8fafc',
                'axes.facecolor': '#ffffff'
            })

            # Chart 1: Department Headcount (Bar Chart)
            dept_dist = analytics_data['dept_distribution']
            if dept_dist:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.bar(dept_dist.keys(), dept_dist.values(), color=primary_color, edgecolor='none', width=0.5)
                ax.set_title('Workforce Distribution by Department', fontsize=12, fontweight='bold', pad=15)
                ax.set_ylabel('Number of Employees')
                plt.xticks(rotation=15, ha='right')
                plt.tight_layout()
                path = os.path.join(self.charts_dir, 'department_headcount.png')
                fig.savefig(path, dpi=150)
                plt.close(fig)
                chart_paths['department_headcount'] = '/static/charts/department_headcount.png'

            # Chart 2: Leave Status Distribution (Pie Chart)
            leave_stats = analytics_data['leave_stats']
            if sum(leave_stats.values()) > 0:
                fig, ax = plt.subplots(figsize=(5, 5))
                labels = list(leave_stats.keys())
                sizes = list(leave_stats.values())
                colors = [accent_color, secondary_color, danger_color]
                
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, 
                       textprops={'fontweight': 'bold'}, wedgeprops={'edgecolor': '#ffffff', 'linewidth': 2})
                ax.set_title('Leave Request Status Distribution', fontsize=12, fontweight='bold', pad=15)
                plt.tight_layout()
                path = os.path.join(self.charts_dir, 'leave_distribution.png')
                fig.savefig(path, dpi=150)
                plt.close(fig)
                chart_paths['leave_distribution'] = '/static/charts/leave_distribution.png'

            # Chart 3: Attendance Rate Trend (Line Chart)
            attendance = db.session.query(Attendance).filter(Attendance.is_active == True).all()
            if attendance:
                att_data = [{'date': att.date, 'status': att.status} for att in attendance]
                df_att = pd.DataFrame(att_data)
                
                # Calculate daily rates
                daily_stats = []
                for date, group in df_att.groupby('date'):
                    presents = len(group[group['status'] == 'Present'])
                    total = len(group[group['status'].isin(['Present', 'Absent'])])
                    rate = (presents / total * 100) if total > 0 else 100.0
                    daily_stats.append({'date': date, 'rate': rate})
                
                df_trends = pd.DataFrame(daily_stats).sort_values('date')
                if not df_trends.empty:
                    fig, ax = plt.subplots(figsize=(7, 3.5))
                    ax.plot(df_trends['date'], df_trends['rate'], marker='o', color=primary_color, linewidth=2)
                    ax.set_title('Company Attendance Rate Trend (%)', fontsize=12, fontweight='bold', pad=15)
                    ax.set_ylim(0, 105)
                    ax.set_ylabel('Rate %')
                    plt.xticks(rotation=20, ha='right')
                    plt.tight_layout()
                    path = os.path.join(self.charts_dir, 'attendance_trends.png')
                    fig.savefig(path, dpi=150)
                    plt.close(fig)
                    chart_paths['attendance_trends'] = '/static/charts/attendance_trends.png'

            # Chart 4: Attendance Heatmap-like grid (Day of Week vs status counts)
            if attendance:
                df_att = pd.DataFrame([{
                    'date': datetime.strptime(a.date, '%Y-%m-%d'),
                    'status': a.status
                } for a in attendance])
                df_att['day_of_week'] = df_att['date'].dt.day_name()
                
                # Pivot table for Day of Week vs Status counts
                pivot_df = df_att.groupby(['day_of_week', 'status']).size().unstack(fill_value=0)
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                pivot_df = pivot_df.reindex(days_order).dropna(how='all')
                
                if not pivot_df.empty:
                    fig, ax = plt.subplots(figsize=(6.5, 4))
                    # Plot grouped bar chart as a visual heatmap substitute
                    pivot_df.plot(kind='bar', stacked=True, color=[danger_color, accent_color, secondary_color], ax=ax, width=0.6)
                    ax.set_title('Weekly Attendance Status Distribution', fontsize=12, fontweight='bold', pad=15)
                    ax.set_ylabel('Record Count')
                    ax.set_xlabel('Day of Week')
                    plt.xticks(rotation=15, ha='right')
                    plt.tight_layout()
                    path = os.path.join(self.charts_dir, 'attendance_heatmap.png')
                    fig.savefig(path, dpi=150)
                    plt.close(fig)
                    chart_paths['attendance_heatmap'] = '/static/charts/attendance_heatmap.png'

            return chart_paths
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error generating charts: {str(e)}", exc_info=True)
            return {}
