from flask import Blueprint, jsonify, request
from models.models import db, IdentityRegistry, CompanyProfile, StudentProfile, PlacementOpportunity, PlacementWorkflow, Notification
from utils.decorators import restrict_access_to
from flask_jwt_extended import jwt_required, get_jwt_identity
from cache_manager import ShaanUCache

admin_blueprint = Blueprint('controller', __name__)

@admin_blueprint.route('/dashboard/metrics', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def fetch_system_vitals():
    """Requirement: Aggregated institutional stats with Redis caching."""
    cache_key = "admin_dashboard_vitals"
    cached_data = ShaanUCache.get_value(cache_key)
    if cached_data:
        return jsonify(cached_data), 200

    metrics = {
        "candidate_count": StudentProfile.query.count(),
        "enterprise_count": CompanyProfile.query.count(),
        "active_drives": PlacementOpportunity.query.filter_by(drive_state='active').count(),
        "placed_students": PlacementWorkflow.query.filter_by(current_stage='Selected').count()
    }
    ShaanUCache.set_value(cache_key, metrics, timeout=300)
    return jsonify(metrics), 200

#Moderation of enterprise

@admin_blueprint.route('/moderate/enterprises', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def list_pending_enterprises():
    """Requirement: Admin can view companies awaiting institutional verification."""
    pending = CompanyProfile.query.filter_by(verification_status='pending').all()
    return jsonify([{
        "id": c.id, 
        "name": c.legal_entity_name, 
        "sector": c.industry_domain,
        "email": c.identity_anchor.email_address,
        "joined": c.identity_anchor.onboarded_at.strftime("%Y-%m-%d")
    } for c in pending]), 200

@admin_blueprint.route('/action/enterprise/<int:cid>', methods=['PATCH'])
@jwt_required()
@restrict_access_to('admin')
def resolve_enterprise_identity(cid):
    """Approve or reject enterprise registration."""
    status = request.json.get('status')
    org = CompanyProfile.query.get_or_404(cid)
    org.verification_status = status
    
    Notification.create(
        receiver_id=org.registry_id,
        title=f"Institutional Verification: {status.upper()}",
        message=f"Your enterprise profile for {org.legal_entity_name} has been {status}.",
        n_type='success' if status == 'approved' else 'danger'
    )
    db.session.commit()
    ShaanUCache.delete_key("admin_dashboard_vitals")
    return jsonify({"message": f"Organization {status}."}), 200

#Drive Lifecycle moderation

@admin_blueprint.route('/moderate/drives/all', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def list_all_drives():
    """Requirement: View and manage ALL drives in the system."""
    drives = PlacementOpportunity.query.order_by(PlacementOpportunity.id.desc()).all()
    return jsonify([{
        "id": d.id, 
        "title": d.job_title, 
        "company": d.host_enterprise.legal_entity_name,
        "package": d.remuneration_package, 
        "status": d.drive_state,
        "applicants": len(d.submissions),
        "min_cgpa": d.cgpa_threshold,
        "description": d.description_text
    } for d in drives]), 200

@admin_blueprint.route('/action/drive/<int:did>', methods=['PATCH'])
@jwt_required()
@restrict_access_to('admin')
def resolve_drive_listing(did):
    """Accept, Close, or Deny a placement drive."""
    status = request.json.get('status') 
    drive = PlacementOpportunity.query.get_or_404(did)
    drive.drive_state = status
    
    Notification.create(
        receiver_id=drive.host_enterprise.registry_id,
        title=f"Drive Update: {status.upper()}",
        message=f"The campaign for '{drive.job_title}' is now {status}.",
        n_type='success' if status == 'active' else 'danger'
    )
    db.session.commit()
    ShaanUCache.delete_key("admin_dashboard_vitals")
    return jsonify({"message": "Drive status updated."}), 200

#user registry management

@admin_blueprint.route('/registry/all', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def get_full_registry():
    """Returns the complete list of non-admin users for management."""
    users = IdentityRegistry.query.filter(IdentityRegistry.assigned_role != 'admin').all()
    return jsonify([{
        "id": u.id,
        "email": u.email_address,
        "role": u.assigned_role,
        "is_active": u.is_active_member,
        "display_name": u.student_profile.full_name_official if u.assigned_role == 'student' else u.company_profile.legal_entity_name if u.assigned_role == 'company' else u.username_handle
    } for u in users]), 200

@admin_blueprint.route('/registry/toggle-access/<int:uid>', methods=['POST'])
@jwt_required()
@restrict_access_to('admin')
def toggle_identity_access(uid):
    user = IdentityRegistry.query.get_or_404(uid)
    if user.assigned_role == 'admin': return jsonify({"error": "Unauthorized"}), 403
    user.is_active_member = not user.is_active_member
    db.session.commit()
    return jsonify({"message": "Access toggled.", "new_status": user.is_active_member}), 200

@admin_blueprint.route('/monitor/applications', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def view_global_applications():
    apps = PlacementWorkflow.query.order_by(PlacementWorkflow.applied_on.desc()).all()
    return jsonify([{
        "id": a.id, 
        "student": a.candidate_ref.full_name_official,
        "company": a.opportunity_ref.host_enterprise.legal_entity_name,
        "role": a.opportunity_ref.job_title, 
        "stage": a.current_stage,
        "date": a.applied_on.strftime("%Y-%m-%d")
    } for a in apps]), 200

@admin_blueprint.route('/notifications', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def get_admin_notifications():
    uid = get_jwt_identity()
    notes = Notification.query.filter_by(receiver_id=uid).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([{
        "id": n.id, "title": n.title, "message": n.message, "type": n.type,
        "time": n.created_at.strftime("%Y-%m-%d %H:%M"), "read": n.is_read
    } for n in notes]), 200

@admin_blueprint.route('/notifications/mark-read', methods=['POST'])
@jwt_required()
@restrict_access_to('admin')
def mark_read():
    uid = get_jwt_identity()
    Notification.query.filter_by(receiver_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "Read"}), 200