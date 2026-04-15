from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

def restrict_access_to(required_role):
    """
    Requirement: Role-based access control (RBAC).
    
    A decorator factory that ensures the current user has the appropriate
    institutional role assigned in their JWT claims before allowing 
    access to a protected route.
    
    Args:
        required_role (str): The role authorized for the endpoint 
                            (e.g., 'admin', 'student', 'company').
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            #Ensureing a valid JWT is present in the request headers
            verify_jwt_in_request()
            
            #Extract additional claims from the token
            claims = get_jwt()
            user_role = claims.get("role")

            #Governance Check: Compare token role with the required role
            if user_role != required_role:
                return jsonify({
                    "error": "Institutional Authorization Failure",
                    "message": f"This endpoint is restricted to {required_role} accounts only.",
                    "detected_role": user_role
                }), 403

            #Access Granted
            return fn(*args, **kwargs)
        
        return wrapper
    return decorator