from flask import Blueprint, jsonify, request
from models.models import db, CompanyProfile, PlacementOpportunity, PlacementWorkflow, InterviewSession, Notification
from utils.decorators import restrict_access_to
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

#Ensuring institutional jobs engine is accessible for offer generation
from jobs import generate_offer_letter

company_blueprint = Blueprint('enterprise', __name__)
logger = logging.getLogger("ShaanU_Enterprise")

@company_blueprint.route('/profile-status', methods=['GET'])
@jwt_required()
@restrict_access_to('company')
def fetch_status():
    """Requirement: Retrieve enterprise verification status and profile metadata."""
    uid = get_jwt_identity()
    company = CompanyProfile.query.filter_by(registry_id=uid).first_or_404()
    return jsonify({
        "name": company.legal_entity_name,
        "industry": company.industry_domain,
        "website": company.website_url,
        "status": company.verification_status 
    }), 200

@company_blueprint.route('/update-profile', methods=['PATCH'])
@jwt_required()
@restrict_access_to('company')
def update_profile():
    """Requirement: Synchronize corporate identity changes with the institutional registry."""
    uid = get_jwt_identity()
    company = CompanyProfile.query.filter_by(registry_id=uid).first_or_404()
    data = request.json
    
    if 'name' in data: company.legal_entity_name = data['name']
    if 'industry' in data: company.industry_domain = data['industry']
    if 'website' in data: company.website_url = data['website']
    
    db.session.commit()
    return jsonify({"message": "Institutional records successfully synchronized."}), 200

@company_blueprint.route('/publish-drive', methods=['POST'])
@jwt_required()
@restrict_access_to('company')
def publish_drive():
    """Requirement: Corporate  partners can initiate placement drives for administrative review."""
    uid = get_jwt_identity()
    company = CompanyProfile.query.filter_by(registry_id=uid).first()
    data = request.json
    
    if not all(k in data for k in ('title', 'package', 'description')):
        return jsonify({"error": "Missing mandatory drive specifications (title, package, description)."}), 400

    new_drive = PlacementOpportunity(
        employer_id=company.id,
        job_title=data['title'],
        remuneration_package=data['package'],
        description_text=data['description'],
        cgpa_threshold=data.get('eligibility', 6.0),
        drive_state='pending_approval' 
    )
    
    db.session.add(new_drive)
    db.session.commit()
    return jsonify({"message": "Drive submitted for institutional authorization."}), 201

@company_blueprint.route('/my-drives', methods=['GET'])
@jwt_required()
@restrict_access_to('company')
def list_drives():
    """Requirement: Enumerate all placement campaigns launched by the enterprise."""
    uid = get_jwt_identity()
    company = CompanyProfile.query.filter_by(registry_id=uid).first()
    drives = PlacementOpportunity.query.filter_by(employer_id=company.id).all()
    
    return jsonify([{
        "id": d.id,
        "title": d.job_title,
        "package": d.remuneration_package,
        "status": d.drive_state,
        "applicants": len(d.submissions)
    } for d in drives]), 200

@company_blueprint.route('/pipeline/applicants/<int:drive_id>', methods=['GET'])
@jwt_required()
@restrict_access_to('company')
def view_applicants(drive_id):
    """
    Requirement: View recruitment  pipeline with interview schedules.
    Returns nested interview sessions to allow companies to see scheduled times.
    """
    apps = PlacementWorkflow.query.filter_by(opportunity_id=drive_id).all()
    return jsonify([{
        "workflow_id": a.id,
        "candidate_name": a.candidate_ref.full_name_official,
        "cgpa": a.candidate_ref.cumulative_gpa,
        "stage": a.current_stage,
        "resume": a.candidate_ref.resume_path,
        "interviews": [{
            "id": i.id,
            "time": i.proposed_time.strftime("%Y-%m-%d %H:%M"),
            "status": i.status,
            "link": i.meeting_link,
            "student_notes": getattr(i, 'student_notes', '')
        } for i in a.interviews]
    } for a in apps]), 200

@company_blueprint.route('/pipeline/update-stage', methods=['PATCH'])
@jwt_required()
@restrict_access_to('company')
def update_stage():
    """Requirement: Advance candidates through the recruitment funnel with automated notifications."""
    data = request.json
    workflow = PlacementWorkflow.query.get_or_404(data.get('workflow_id'))
    new_stage = data.get('stage')
    
    workflow.current_stage = new_stage
    
    #Triggering dynamic Student notification
    Notification.create(
        receiver_id=workflow.candidate_ref.registry_id,
        title="Institutional Status Update",
        message=f"Your status for the {workflow.opportunity_ref.job_title} role at {workflow.opportunity_ref.host_enterprise.legal_entity_name} has been updated to: {new_stage}.",
        n_type='info'
    )
    
    db.session.commit()
    return jsonify({"message": f"Candidate successfully moved to {new_stage}."}), 200

@company_blueprint.route('/interviews/schedule', methods=['POST'])
@jwt_required()
@restrict_access_to('company')
def schedule_interview():
    """Robust date parsing to handle the format seen in institutional dashboard inputs."""
    data = request.json
    workflow = PlacementWorkflow.query.get_or_404(data.get('workflow_id'))
    
    try:
        # Standardize format for fromisoformat (Handling browser-specific time formatting)
        time_str = data['time'].replace(' ', 'T')
        proposed_time = datetime.fromisoformat(time_str)
        
        new_session = InterviewSession(
            workflow_id=workflow.id,
            proposed_time=proposed_time,
            meeting_link=data.get('link'),
            status='invited'
        )
        db.session.add(new_session)
        
        #dispatching Notification to Candidate
        Notification.create(
            receiver_id=workflow.candidate_ref.registry_id,
            title="Interview Session Dispatched",
            message=f"{workflow.opportunity_ref.host_enterprise.legal_entity_name} has proposed an interview session for {proposed_time.strftime('%Y-%m-%d %H:%M')}.",
            n_type='warning'
        )
        
        db.session.commit()
        return jsonify({"message": "Interview session dispatched successfully."}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Scheduling Logic Failure: {str(e)}")
        return jsonify({"error": "Failed to schedule. Please verify date and time format."}), 400

@company_blueprint.route('/pipeline/generate-offer', methods=['POST'])
@jwt_required()
@restrict_access_to('company')
def trigger_offer_generation():
    """Requirement: Automated dummy offer letter generator for selected institutional candidates."""
    data = request.json
    workflow = PlacementWorkflow.query.get_or_404(data.get('workflow_id'))
    
    uid = get_jwt_identity()
    company = CompanyProfile.query.filter_by(registry_id=uid).first()
    
    # Generate the branded PDF via institutional jobs engine
    filename = generate_offer_letter(
        candidate_name=workflow.candidate_ref.full_name_official,
        company_name=company.legal_entity_name,
        package=data.get('package'),
        role=data.get('role')
    )
    
    #creating persistent alert for student
    Notification.create(
        receiver_id=workflow.candidate_ref.registry_id,
        title="Institutional Offer Issued",
        message=f"Congratulations! {company.legal_entity_name} has generated an official offer letter for your candidacy.",
        n_type='success'
    )
    
    db.session.commit()
    return jsonify({
        "message": "Institutional offer letter generated and dispatched.",
        "download_url": f"/static/offers/{filename}"
    }), 201

@company_blueprint.route('/notifications', methods=['GET'])
@jwt_required()
@restrict_access_to('company')
def get_company_notifications():
    """Requirement: Retrieve dynamic institutional alerts for the enterprise dashboard bell."""
    uid = get_jwt_identity()
    notes = Notification.query.filter_by(receiver_id=uid).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "time": n.created_at.strftime("%Y-%m-%d %H:%M"),
        "read": n.is_read
    } for n in notes]), 200