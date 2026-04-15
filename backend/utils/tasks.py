import os
import logging
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
from flask import render_template_string
from fpdf import FPDF
from models.models import db, StudentProfile, PlacementOpportunity, PlacementWorkflow

# Initialize Celery with Redis as the broker and result backend
# Requirement: Redis and Celery for batch jobs
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery('shaanu_tasks', broker=redis_url, backend=redis_url)

logger = logging.getLogger("ShaanU_Worker")



# A. DAILY REMINDERS LOGIC

def daily_deadline_reminders():
    """
    Requirement: Scheduled Job - Daily reminders for upcoming deadlines.
    Identifies active drives closing within 24 hours and alerts eligible students
    who have not yet submitted an application.
    """
    from app import initialize_shaanu_app
    flask_app = initialize_shaanu_app()
    
    with flask_app.app_context():
        # Look for drives expiring tomorrow
        tomorrow = (datetime.utcnow() + timedelta(days=1)).date()
        critical_drives = PlacementOpportunity.query.filter(
            db.func.date(PlacementOpportunity.expiration_date) == tomorrow,
            PlacementOpportunity.drive_state == 'active'
        ).all()

        for drive in critical_drives:
            # Filter students meeting CGPA threshold
            eligible = StudentProfile.query.filter(
                StudentProfile.cumulative_gpa >= drive.cgpa_threshold
            ).all()

            for student in eligible:
                # Check if application already exists
                has_applied = PlacementWorkflow.query.filter_by(
                    opportunity_id=drive.id, 
                    student_id=student.id
                ).first()

                if not has_applied:
                    # Simulation: In production, this triggers G-Chat Webhooks or SES Emails
                    logger.info(
                        f"ALERT DISPATCHED: {student.full_name_official} -> "
                        f"Deadline approaching for {drive.job_title} at "
                        f"{drive.host_enterprise.legal_entity_name}."
                    )
        return f"Processed {len(critical_drives)} critical drives."



# B. MONTHLY ACTIVITY REPORT LOGIC

def monthly_report_job():
    """
    Requirement: Monthly activity report (Backend Job 2).
    Generates a professional HTML summary and a PDF audit trail for the Admin.
    """
    from app import initialize_shaanu_app
    flask_app = initialize_shaanu_app()
    
    with flask_app.app_context():
        # Define reporting period (the month that just concluded)
        report_month = (datetime.now() - timedelta(days=1)).strftime("%B %Y")
        
        #Aggregate Institutional Statistics
        metrics = {
            "drives": PlacementOpportunity.query.count(),
            "apps": PlacementWorkflow.query.count(),
            "selected": PlacementWorkflow.query.filter_by(current_stage='Selected').count(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        #HTML Report Generation
        html_template = """
        <div style="font-family: 'Inter', sans-serif; padding: 40px; background: #fdfdfd; max-width: 650px; margin: auto; border: 1px solid #eee; border-radius: 20px;">
            <div style="text-align: center; border-bottom: 2px solid #1e3c72; padding-bottom: 20px; margin-bottom: 30px;">
                <h1 style="color: #1e3c72; margin: 0;">Institutional Audit</h1>
                <p style="color: #64748b; margin-top: 5px; font-weight: 600;">Monthly Placement Activity: {{ month }}</p>
            </div>
            
            <div style="display: grid; gap: 15px;">
                <div style="background: #f8fafd; padding: 20px; border-radius: 12px; border-left: 4px solid #1e3c72;">
                    <span style="display: block; font-size: 12px; color: #64748b; text-transform: uppercase;">Recruitment Drives</span>
                    <strong style="font-size: 24px; color: #1e3c72;">{{ drives }}</strong>
                </div>
                <div style="background: #f8fafd; padding: 20px; border-radius: 12px; border-left: 4px solid #1e3c72;">
                    <span style="display: block; font-size: 12px; color: #64748b; text-transform: uppercase;">Total Applications</span>
                    <strong style="font-size: 24px; color: #1e3c72;">{{ apps }}</strong>
                </div>
                <div style="background: #f0fdf4; padding: 20px; border-radius: 12px; border-left: 4px solid #22c55e;">
                    <span style="display: block; font-size: 12px; color: #15803d; text-transform: uppercase;">Successful Placements</span>
                    <strong style="font-size: 24px; color: #15803d;">{{ selected }}</strong>
                </div>
            </div>
            
            <footer style="margin-top: 40px; text-align: center; font-size: 11px; color: #94a3b8;">
                ShaanU Placement Portal &bull; Automated System Audit &bull; {{ date }}
            </footer>
        </div>
        """
        html_content = render_template_string(html_template, month=report_month, **metrics)
        
        # Define Storage Paths
        report_dir = os.path.join(flask_app.static_folder, 'static', 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        #Save HTML Copy
        html_path = os.path.join(report_dir, f"Audit_{report_month.replace(' ', '_')}.html")
        with open(html_path, 'w') as f:
            f.write(html_content)

        #PDF Conversion (Requirement: Well-designed PDF)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(30, 60, 114) # ShaanU Blue
        pdf.cell(0, 20, f"ShaanU Institutional Activity Report", 0, 1, 'C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, f"Reporting Period: {report_month}", 0, 1, 'C')
        pdf.ln(15)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(240, 244, 250)
        pdf.cell(95, 12, "Institutional Metric", 1, 0, 'L', True)
        pdf.cell(95, 12, "Quantity", 1, 1, 'C', True)
        
        pdf.set_font("Arial", size=11)
        pdf.cell(95, 10, "Recruitment Campaigns Launch", 1)
        pdf.cell(95, 10, str(metrics['drives']), 1, 1, 'C')
        pdf.cell(95, 10, "Student Applications Processed", 1)
        pdf.cell(95, 10, str(metrics['apps']), 1, 1, 'C')
        pdf.cell(95, 10, "Final Selections (Offers Made)", 1)
        pdf.cell(95, 10, str(metrics['selected']), 1, 1, 'C')
        
        pdf_filename = f"Audit_{report_month.replace(' ', '_')}.pdf"
        pdf_path = os.path.join(report_dir, pdf_filename)
        pdf.output(pdf_path)

        logger.info(f"MONTHLY AUDIT COMPLETE: PDF archived at {pdf_path}")
        return pdf_path



# Celery Beat Internal Scheduler

celery_app.conf.beat_schedule = {
    'daily-reminders': {
        'task': 'dispatch_daily_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    'monthly-admin-report': {
        'task': 'generate_monthly_admin_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    }
}
celery_app.conf.timezone = 'UTC'