from flask import Blueprint, jsonify, request
from models.models import db, StudentProfile, PlacementOpportunity, PlacementWorkflow, InterviewSession, Notification
from utils.decorators import restrict_access_to
from flask_jwt_extended import jwt_required, get_jwt_identity
from tasks import export_applications_to_csv
from datetime import datetime

student_blueprint = Blueprint('candidate', __name__)

@student_blueprint.route('/profile', methods=['GET'])
@jwt_required()
@restrict_access_to('student')
def get_profile():
    """Requirement: Retrieve student profile metadata for the dashboard."""
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first_or_404()
    return jsonify({
        "full_name": student.full_name_official,
        "cgpa": student.cumulative_gpa,
        "department": student.academic_dept,
        "enrollment": student.enrollment_id,
        "resume": student.resume_path
    }), 200

@student_blueprint.route('/update-profile', methods=['PATCH'])
@jwt_required()
@restrict_access_to('student')
def update_profile():
    """Synchronize profile changes with institutional registry."""
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first_or_404()
    data = request.json
    #Preventing empty names - validation
    if 'fullname' in data:
        if not data['fullname'].strip():
            return jsonify({"error": "Full name cannot be empty."}), 400
        student.full_name_official = data['fullname'].strip()
        
    if 'department' in data:
        student.academic_dept = data['department'].strip()
        
    if 'resume_name' in data:
        if not data['resume_name'].lower().endswith('.pdf'):
            return jsonify({"error": "Resume must be a valid PDF reference."}), 400
        student.resume_path = data['resume_name']
    
    db.session.commit()
    return jsonify({"message": "Profile metadata updated successfully."}), 200

@student_blueprint.route('/available-drives', methods=['GET'])
@jwt_required()
@restrict_access_to('student')
def list_eligible_drives():
    """Requirement: List active drives filtered by CGPA eligibility and search query."""
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first()
    query = request.args.get('q', '')
    
    #filter by CGPA threshold and active state
    drives = PlacementOpportunity.query.filter(
        PlacementOpportunity.drive_state == 'active',
        PlacementOpportunity.cgpa_threshold <= student.cumulative_gpa,
        PlacementOpportunity.job_title.ilike(f"%{query}%")
    ).all()
    
    return jsonify([{
        "drive_id": d.id,
        "company": d.host_enterprise.legal_entity_name,
        "position": d.job_title,
        "ctc": d.remuneration_package,
        "min_cgpa": d.cgpa_threshold,
        "description": d.description_text
    } for d in drives]), 200

@student_blueprint.route('/submit-application', methods=['POST'])
@jwt_required()
@restrict_access_to('student')
def apply():
    """
    Requirement: Submit application and trigger dynamic notifications.
    Notifies both the Student (confirmation) and the Company (new lead).
    """
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first()
    drive_id = request.json.get('drive_id')
    
    if not drive_id:
        return jsonify({"error": "Target drive ID is required."}), 400
        
    #block duplicate applications
    existing = PlacementWorkflow.query.filter_by(student_id=student.id, opportunity_id=drive_id).first()
    if existing:
        return jsonify({"error": "Duplicate Application", "message": "You have already applied for this drive."}), 400
        
    drive = PlacementOpportunity.query.get_or_404(drive_id)
    
    #eligibility Validation: Re-verify CGPA on backend
    if student.cumulative_gpa < drive.cgpa_threshold:
        return jsonify({
            "error": "Eligibility Breach",
            "message": f"Your CGPA ({student.cumulative_gpa}) does not meet the drive threshold ({drive.cgpa_threshold})."
        }), 403

    new_app = PlacementWorkflow(student_id=student.id, opportunity_id=drive_id, current_stage='Applied')
    db.session.add(new_app)
    
    #dynamic Notification for Student
    Notification.create(
        receiver_id=uid,
        title="Application Confirmed",
        message=f"Your application for {drive.job_title} at {drive.host_enterprise.legal_entity_name} has been recorded.",
        n_type='success'
    )

    #dynamic Notification for Company
    company_identity_id = drive.host_enterprise.registry_id
    Notification.create(
        receiver_id=company_identity_id,
        title="New Applicant Found",
        message=f"Candidate {student.full_name_official} has applied for your {drive.job_title} role.",
        n_type='info'
    )
    
    db.session.commit()
    return jsonify({"message": "Application submitted successfully."}), 201

@student_blueprint.route('/application-tracking', methods=['GET'])
@jwt_required()
@restrict_access_to('student')
def track_applications():
    """Requirement: Detailed application tracking including interview sessions."""
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first()
    apps = PlacementWorkflow.query.filter_by(student_id=student.id).all()
    
    return jsonify([{
        "id": a.id,
        "drive": a.opportunity_ref.job_title,
        "company": a.opportunity_ref.host_enterprise.legal_entity_name,
        "status": a.current_stage,
        "applied_on": a.applied_on.strftime("%Y-%m-%d"),
        "interviews": [{
            "id": i.id,
            "time": i.proposed_time.strftime("%Y-%m-%d %H:%M"),
            "status": i.status,
            "link": i.meeting_link
        } for i in a.interviews]
    } for a in apps]), 200

@student_blueprint.route('/interviews/respond', methods=['POST'])
@jwt_required()
@restrict_access_to('student')
def respond_to_interview():
    """
    Requirement: Bidirectional interview orchestration.
    Notifies the company when a student confirms or requests a reschedule.
    """
    data = request.json
    session_id = data.get('id')
    action = data.get('action') # 'confirmed' or 'reschedule_requested'
    remarks = data.get('remarks', '')
    
    if action not in ['confirmed', 'reschedule_requested']:
        return jsonify({"error": "Invalid response action."}), 400
    
    session = InterviewSession.query.get_or_404(session_id)
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first()
    
    # Security Check: Ensure session belongs to the student
    if session.workflow_context.student_id != student.id:
        return jsonify({"error": "Unauthorized session access."}), 403
        
    session.status = action
    
    #Identification for Dynamic Notification
    company_uid = session.workflow_context.opportunity_ref.host_enterprise.registry_id
    candidate_name = student.full_name_official
    job_title = session.workflow_context.opportunity_ref.job_title

    if action == 'reschedule_requested':
        session.student_notes = remarks
        # Notify Company about reschedule request with dynamic remarks
        Notification.create(
            receiver_id=company_uid,
            title="Timing Change Requested",
            message=f"{candidate_name} requested a reschedule for {job_title}. Note: {remarks}",
            n_type='warning'
        )
    else:
        #notification to company for confirmation
        Notification.create(
            receiver_id=company_uid,
            title="Interview Slot Confirmed",
            message=f"{candidate_name} has accepted the interview slot for {job_title}.",
            n_type='success'
        )
        
    db.session.commit()
    return jsonify({"message": "Response recorded successfully."}), 200

@student_blueprint.route('/notifications', methods=['GET'])
@jwt_required()
@restrict_access_to('student')
def get_student_notifications():
    """Requirement: Retrieve dynamic alerts for the current student dashboard bell."""
    uid = get_jwt_identity()
    notes = Notification.query.filter_by(receiver_id=uid).order_by(Notification.created_at.desc()).limit(20).all()
    
    return jsonify([{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "category": getattr(n, 'category', 'info'), # For specialized reports
        "time": n.created_at.strftime("%Y-%m-%d %H:%M"),
        "read": n.is_read
    } for n in notes]), 200

@student_blueprint.route('/notifications/mark-read', methods=['POST'])
@jwt_required()
@restrict_access_to('student')
def mark_read():
    """Synchronize read status with the institutional registry."""
    uid = get_jwt_identity()
    Notification.query.filter_by(receiver_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "Alerts cleared."}), 200

@student_blueprint.route('/export-applications', methods=['POST'])
@jwt_required()
@restrict_access_to('student')
def trigger_export():
    """Requirement: Trigger Celery task for institutional history export."""
    uid = get_jwt_identity()
    student = StudentProfile.query.filter_by(registry_id=uid).first()
    export_applications_to_csv.delay(student.id)
    return jsonify({"message": "Export initiated. Check back in a few minutes for the CSV."}), 200