import logging
import os
import csv
import io
from datetime import datetime, timedelta
from flask import render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from fpdf import FPDF
from models.models import db, StudentProfile, PlacementOpportunity, PlacementWorkflow, CompanyProfile, IdentityRegistry
from cache_manager import ShaanUCache

logger = logging.getLogger("ShaanU_Jobs")

class ShaanUReportPDF(FPDF):
    """
    Institutional PDF Template with custom headers and footers.
    Requirement: Well-designed PDF reports.
    """
    def header(self):
        # Set ShaanU Blue branding
        self.set_text_color(30, 60, 114)
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'ShaanU Placement Intelligence Report', 0, 1, 'C')
        self.set_draw_color(30, 60, 114)
        self.line(10, 22, 200, 22)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Institutional Registry | Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def generate_monthly_pdf_report(metrics, month_name):
    """
    Requirement: Backend Job 2 - Monthly Activity Report.
    Generates a professional audit trail for institutional records.
    """
    pdf = ShaanUReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Header Background
    pdf.set_fill_color(240, 244, 250)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Executive Placement Summary - {month_name}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # Metrics Table
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(100, 10, "Institutional Metric", 1, 0, 'L', True)
    pdf.cell(80, 10, "Statistical Value", 1, 1, 'C', True)
    
    pdf.set_font("Arial", size=10)
    metrics_data = [
        ["Total Recruitment Drives Launch", str(metrics.get('drives', 0))],
        ["Student Applications Processed", str(metrics.get('apps', 0))],
        ["Successful Placements (Offers)", str(metrics.get('selections', 0))],
        ["Placement Conversion Rate", f"{metrics.get('velocity', 0)}%"]
    ]
    
    for row in metrics_data:
        pdf.cell(100, 10, row[0], 1)
        pdf.cell(80, 10, row[1], 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.multi_cell(0, 5, "Notice: This document is an automated institutional record. Any discrepancies should be reported to the ShaanU Administrative Controller immediately.")
    
    # Save to Static Directory
    report_filename = f"Audit_Report_{month_name.replace(' ', '_')}.pdf"
    report_path = os.path.join('frontend', 'static', 'reports', report_filename)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    pdf.output(report_path)
    return report_filename

def generate_offer_letter(candidate_name, company_name, package, role):
    """
    Requirement: Dummy offer letter generator for the company side.
    Provides students with a downloadable PDF certificate upon selection.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Branding
    pdf.set_fill_color(30, 60, 114)
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 30, "OFFER OF EMPLOYMENT", 0, 1, 'C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)
    pdf.set_font("Arial", size=12)
    
    date_str = datetime.now().strftime("%B %d, %Y")
    content = f"""
    Date: {date_str}
    
    Dear {candidate_name},
    
    We are pleased to offer you the position of {role} at {company_name}. 
    Our selection committee was highly impressed with your academic performance at ShaanU.
    
    The details of your offer are as follows:
    - Role Classification: {role}
    - Annual Remuneration (CTC): {package}
    - Location: Corporate Office / Remote (As discussed)
    
    This offer is valid subject to the verification of your institutional records and 
    final graduation clearance from ShaanU.
    
    We look forward to having you on board.
    
    Sincerely,
    
    The Human Resources Team
    {company_name}
    """
    pdf.multi_cell(0, 10, content)
    
    filename = f"Offer_{candidate_name.replace(' ', '_')}_{os.urandom(2).hex()}.pdf"
    path = os.path.join('frontend', 'static', 'offers', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pdf.output(path)
    return filename

def monthly_activity_job():
    """
    Scheduled Job logic: Aggregates monthly data and triggers PDF generation.
    Designed for use with APScheduler as a secondary fallback to Celery.
    """
    from app import db # Delayed import to avoid circular dependencies
    
    with db.app.app_context():
        # Current month label
        month_label = datetime.now().strftime("%B %Y")
        
        # Aggregate statistics from SQLAlchemy models
        drives_count = PlacementOpportunity.query.count()
        apps_count = PlacementWorkflow.query.count()
        selections_count = PlacementWorkflow.query.filter_by(current_stage='Selected').count()
        
        velocity = round((selections_count / apps_count * 100), 2) if apps_count > 0 else 0
        
        metrics = {
            'drives': drives_count,
            'apps': apps_count,
            'selections': selections_count,
            'velocity': velocity
        }
        
        # Trigger PDF generation
        filename = generate_monthly_pdf_report(metrics, month_label)
        logger.info(f"Scheduled Monthly Job Finished: {filename}")

def init_scheduler(app):
    """
    Initializes the BackgroundScheduler within the Flask application context.
    Ensures periodic jobs run without blocking the main request loop.
    """
    scheduler = BackgroundScheduler()
    # Schedule the audit for the 1st of every month
    scheduler.add_job(func=monthly_activity_job, trigger="cron", day=1, hour=0, id='monthly_audit')
    scheduler.start()
    logger.info("ShaanU Background Scheduler initialized and running.")