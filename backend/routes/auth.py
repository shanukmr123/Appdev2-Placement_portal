from flask import Blueprint, request, jsonify
from models.models import db, IdentityRegistry, StudentProfile, CompanyProfile
from flask_jwt_extended import create_access_token, jwt_required
from utils.decorators import restrict_access_to
from datetime import timedelta
import logging
import re

auth_blueprint = Blueprint('gatekeeper', __name__)
logger = logging.getLogger("ShaanU_Auth")

def is_valid_institutional_email(email):
    """
    Requirement: Validate that the email follows the shaanu.edu pattern.
    Restricts enrollment to institutional members only.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@shaanu\.edu$'
    return re.match(pattern, email) is not None

@auth_blueprint.route('/enroll/candidate', methods=['POST'])
def register_student():
    """
    Requirement: Self-registration for students with Backend Validation.
    Enforces institutional domain and numeric GPA integrity.
    """
    data = request.json
    
    #mandatory fields check
    required = ['email', 'password', 'username', 'fullname', 'enrollment', 'cgpa']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing mandatory fields for student enrollment."}), 400

    #Email domain check
    email = data.get('email').lower().strip()
    if not is_valid_institutional_email(email):
        return jsonify({"error": "Registration restricted to @shaanu.edu email addresses."}), 400

    #passoword complexity check
    if len(data.get('password')) < 6:
        return jsonify({"error": "Institutional security requires passwords >= 6 characters."}), 400

    #Data integrity check for CGPA
    try:
        cgpa = float(data.get('cgpa'))
        if not (0.0 <= cgpa <= 10.0): raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid CGPA. Value must be numeric between 0.0 and 10.0."}), 400

    #duplicate check
    if IdentityRegistry.query.filter_by(email_address=email).first():
        return jsonify({"error": "An identity with this email already exists in the registry."}), 409

    try:
        #Provision Identity
        user = IdentityRegistry(
            email_address=email,
            username_handle=data.get('username').strip(),
            assigned_role='student'
        )
        user.set_secret(data.get('password'))
        db.session.add(user)
        db.session.flush()

        #Provision Profile
        profile = StudentProfile(
            registry_id=user.id,
            full_name_official=data.get('fullname').strip(),
            enrollment_id=data.get('enrollment').strip(),
            cumulative_gpa=cgpa,
            academic_dept=data.get('department', 'Computer Science')
        )
        db.session.add(profile)
        db.session.commit()
        
        logger.info(f"Student Enrolled: {email}")
        return jsonify({"message": "Institutional identity successfully provisioned."}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Enrollment Logic Failure: {str(e)}")
        return jsonify({"error": "Internal Registry Failure"}), 500

@auth_blueprint.route('/enroll/enterprise', methods=['POST'])
def register_company():
    """
    Requirement: Self-registration for corporate partners.
    Assigns 'pending' status for Administrative verification.
    """
    data = request.json
    
    required = ['email', 'password', 'username', 'company_name', 'industry']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing mandatory corporate metadata."}), 400

    email = data.get('email').lower().strip()
    if IdentityRegistry.query.filter_by(email_address=email).first():
        return jsonify({"error": "Enterprise email is already registered."}), 409

    try:
        #Provision Corporate Identity
        user = IdentityRegistry(
            email_address=email,
            username_handle=data.get('username').strip(),
            assigned_role='company'
        )
        user.set_secret(data.get('password'))
        db.session.add(user)
        db.session.flush()

        #Provision Corporate Profile
        company = CompanyProfile(
            registry_id=user.id,
            legal_entity_name=data.get('company_name').strip(),
            industry_domain=data.get('industry').strip(),
            verification_status='pending' # Required: Admin must verify
        )
        db.session.add(company)
        db.session.commit()
        
        logger.info(f"Enterprise Application Received: {email}")
        return jsonify({"message": "Corporate enrollment submitted for institutional review."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal Registry Failure"}), 500

@auth_blueprint.route('/verify-access', methods=['POST'])
def login():
    """
    Requirement: JWT based Token authentication.
    Checks for credentials and blacklisted (deactivated) status.
    """
    data = request.json
    email = data.get('email', '').lower().strip()
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Institutional credentials are required."}), 400

    user = IdentityRegistry.query.filter_by(email_address=email).first()

    if user and user.verify_secret(password):
        # Requirement: Check blacklisting status
        if not user.is_active_member:
            return jsonify({
                "error": "Access Revoked", 
                "details": "This identity has been blacklisted by the Administrative Controller."
            }), 403

        #Generate Secure Session Token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.assigned_role},
            expires_delta=timedelta(hours=10)
        )
        
        logger.info(f"Successful Verification: {user.username_handle} [{user.assigned_role}]")

        return jsonify({
            "token": access_token,
            "role": user.assigned_role,
            "username": user.username_handle,
            "email": user.email_address
        }), 200

    logger.warning(f"Unauthorized Login Attempt: {email}")
    return jsonify({"error": "Verification Failed: Invalid credentials."}), 401

#admin user management

@auth_blueprint.route('/admin/users', methods=['GET'])
@jwt_required()
@restrict_access_to('admin')
def get_all_users():
    """
    Requirement: Admin should be able to see all users (students and companies).
    Retrieves the full institutional identity registry.
    """
    identities = IdentityRegistry.query.filter(IdentityRegistry.assigned_role != 'admin').all()
    registry_list = []
    
    for identity in identities:
        entry = {
            "id": identity.id,
            "email": identity.email_address,
            "username": identity.username_handle,
            "role": identity.assigned_role,
            "is_active": identity.is_active_member,
            "joined_at": identity.onboarded_at.strftime("%Y-%m-%d")
        }
        
        # Attach profile specific name
        if identity.assigned_role == 'student' and identity.student_profile:
            entry["display_name"] = identity.student_profile.full_name_official
        elif identity.assigned_role == 'company' and identity.company_profile:
            entry["display_name"] = identity.company_profile.legal_entity_name
        else:
            entry["display_name"] = identity.username_handle
            
        registry_list.append(entry)
        
    return jsonify(registry_list), 200

@auth_blueprint.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@jwt_required()
@restrict_access_to('admin')
def toggle_user_status(user_id):
    """
    Requirement: Admin should be able to block and allow users.
    Toggles the is_active_member flag for the specified institutional identity.
    """
    user = IdentityRegistry.query.get_or_404(user_id)
    
    #Prevent admin self blocking / cross admin blocking
    if user.assigned_role == 'admin':
        return jsonify({"error": "Governance Lock: Administrative identities cannot be modified via this endpoint."}), 403
        
    user.is_active_member = not user.is_active_member
    db.session.commit()
    
    status_label = "allowed" if user.is_active_member else "blocked"
    logger.info(f"Governance Action: User {user.email_address} has been {status_label} by Admin.")
    
    return jsonify({
        "message": f"Identity successfully {status_label}.",
        "is_active": user.is_active_member
    }), 200