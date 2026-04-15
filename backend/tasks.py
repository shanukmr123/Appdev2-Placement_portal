import os
import csv
import logging
from datetime import datetime
from utils.tasks import celery_app, daily_deadline_reminders, monthly_report_job
from models.models import db, StudentProfile, PlacementWorkflow

logger = logging.getLogger("ShaanU_Tasks")

#Task Registry & Proxies

@celery_app.task(name='tasks.send_daily_reminders')
def send_daily_reminders():
    """
    Scheduled Proxy: Triggers the daily student alert system.
    Referenced in app.py Celery Beat schedule.
    """
    return daily_deadline_reminders()

@celery_app.task(name='tasks.generate_monthly_report')
def generate_monthly_report():
    """
    Scheduled Proxy: Triggers the institutional monthly audit.
    Referenced in app.py Celery Beat schedule.
    """
    return monthly_report_job()

#On-Demand Tasks

@celery_app.task(name='tasks.export_applications_to_csv')
def export_applications_to_csv(student_id):
    """
    Requirement: User Triggered Async Job.
    Generates a CSV of the student's application history and saves it to static storage.
    Imported and called by student_blueprint.
    """
    from app import initialize_shaanu_app
    app = initialize_shaanu_app()
    
    with app.app_context():
        student = StudentProfile.query.get(student_id)
        if not student:
            return "Student not found"
            
        apps = PlacementWorkflow.query.filter_by(student_id=student_id).all()
        
        # Define institutional export path
        filename = f"History_{student.enrollment_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        filepath = os.path.join(app.static_folder, 'static', 'exports', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                # Header row matching institutional requirements
                writer.writerow(['Drive Title', 'Company', 'Status', 'Applied Date'])
                
                for a in apps:
                    writer.writerow([
                        a.opportunity_ref.job_title,
                        a.opportunity_ref.host_enterprise.legal_entity_name,
                        a.current_stage,
                        a.applied_on.strftime("%Y-%m-%d")
                    ])
            
            logger.info(f"EXPORT SUCCESS: Generated {filename} for {student.full_name_official}")
            return f"/static/exports/{filename}"
            
        except Exception as e:
            logger.error(f"EXPORT FAILURE: {str(e)}")
            return None