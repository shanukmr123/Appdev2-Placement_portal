import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class IdentityRegistry(db.Model):
    """
    Requirement: Unified user model to differentiate all types of user roles.
    Centralized authentication for Admins, Students, and Companies.
    """
    __tablename__ = 'identity_registry'
    
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(120), unique=True, nullable=False)
    username_handle = db.Column(db.String(64), unique=True, nullable=False)
    password_cipher = db.Column(db.String(256), nullable=False)
    
    #Role based
    assigned_role = db.Column(db.String(20), nullable=False) # 'admin', 'student', 'company'
    
    is_active_member = db.Column(db.Boolean, default=True)
    onboarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Link to specific profile metadata
    student_profile = db.relationship('StudentProfile', backref='identity_anchor', uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship('CompanyProfile', backref='identity_anchor', uselist=False, cascade="all, delete-orphan")
    
    # Relationship to notifications
    notifications = db.relationship('Notification', backref='recipient', lazy=True)

    def set_secret(self, raw_password):
        self.password_cipher = generate_password_hash(raw_password)

    def verify_secret(self, raw_password):
        return check_password_hash(self.password_cipher, raw_password)

    @classmethod
    def seed_system_admin(cls):
        """
        Requirement: Only one admin identified by its role. No admin registration.
        This is called programmatically in app.py during startup.
        """
        existing_admin = cls.query.filter_by(assigned_role='admin').first()
        if not existing_admin:
            root = cls(
                email_address="placement_head@shaanu.edu",
                username_handle="shaanu_admin",
                assigned_role="admin"
            )
            root.set_secret("shaanu_secure_admin_2024")
            db.session.add(root)
            db.session.commit()

class Notification(db.Model):
    """
    Requirement: Dynamic, role-based notification system.
    Stores alerts for Students, Companies, and Admins.
    """
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('identity_registry.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info') # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def create(cls, receiver_id, title, message, n_type='info'):
        """Utility to quickly dispatch a notification."""
        note = cls(receiver_id=receiver_id, title=title, message=message, type=n_type)
        db.session.add(note)
        # Session commit should be handled by the caller route logic

class StudentProfile(db.Model):
    """
    Requirement: Student profile management.
    """
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey('identity_registry.id'), nullable=False)
    full_name_official = db.Column(db.String(150), nullable=False)
    enrollment_id = db.Column(db.String(50), unique=True, nullable=False)
    academic_dept = db.Column(db.String(100))
    cumulative_gpa = db.Column(db.Float, default=0.0)
    resume_path = db.Column(db.String(255))
    
    #Relation to applications
    applications = db.relationship('PlacementWorkflow', backref='candidate_ref', lazy=True)

class CompanyProfile(db.Model):
    """
    Requirement: Company profile and registration tracking.
    """
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    registry_id = db.Column(db.Integer, db.ForeignKey('identity_registry.id'), nullable=False)
    legal_entity_name = db.Column(db.String(150), nullable=False)
    industry_domain = db.Column(db.String(100))
    website_url = db.Column(db.String(255))
    
    #Admin approval or rejection to company registrations
    verification_status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    
    #Relationship to drives
    opportunities = db.relationship('PlacementOpportunity', backref='host_enterprise', lazy=True)

class PlacementOpportunity(db.Model):
    """
    Requirement: Placement drives created by companies.
    """
    __tablename__ = 'placement_opportunities'
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    description_text = db.Column(db.Text)
    remuneration_package = db.Column(db.String(100))
    cgpa_threshold = db.Column(db.Float, default=6.0)
    
    #Admin approval or rejection to placement drives
    drive_state = db.Column(db.String(30), default='pending_approval') # pending_approval, active, rejected
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime) # Used for daily reminders
    
    # Relationship to submissions
    submissions = db.relationship('PlacementWorkflow', backref='opportunity_ref', lazy=True)

class PlacementWorkflow(db.Model):
    """
    Requirement: Track application status and history.
    """
    __tablename__ = 'placement_workflows'
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('placement_opportunities.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    #application status dynamically updation
    current_stage = db.Column(db.String(64), default='Applied') # Applied, Shortlisted, Interviewing, Selected, Rejected
    
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    #pecific interview sessions
    interviews = db.relationship('InterviewSession', backref='workflow_context', lazy=True)

class InterviewSession(db.Model):
    """
    Requirement: Bidirectional interview scheduling.
    """
    __tablename__ = 'interview_sessions'
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('placement_workflows.id'), nullable=False)
    
    proposed_time = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(255))
    
    #Student can approve/ request another time slot
    status = db.Column(db.String(50), default='invited') # invited, confirmed, reschedule_requested
    
    company_notes = db.Column(db.Text)
    student_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)