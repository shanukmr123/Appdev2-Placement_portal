import os
import logging
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from celery.schedules import crontab
from werkzeug.utils import secure_filename

# Institutional Logic Imports
from models.models import db, IdentityRegistry
from routes.auth import auth_blueprint
from routes.admin import admin_blueprint
from routes.company import company_blueprint
from routes.student import student_blueprint
from cache_manager import ShaanUCache
from tasks import celery_app

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ShaanU_Core")

def initialize_shaanu_app():
    """
    Orchestrates the ShaanU Placement Portal backend.
    Handles configuration, directory provisioning, and module registration.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.abspath(os.path.join(base_dir, '..', 'frontend'))
    instance_dir = os.path.abspath(os.path.join(base_dir, '..', 'instance'))
    upload_dir = os.path.join(frontend_dir, 'static', 'resumes')
    
    app = Flask(__name__, 
                instance_path=instance_dir,
                static_folder=frontend_dir, 
                static_url_path='')

    #Institutional Configuration
    database_path = os.path.join(instance_dir, 'shaanu_portal_v1.db')
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY='shaanu-institutional-security-key-2024',
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=10),
        UPLOAD_FOLDER=upload_dir,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024 # 5MB Institutional Limit
    )

    #Initialize Extensions
    CORS(app)
    db.init_app(app)
    JWTManager(app)
    ShaanUCache.init_redis()

    #Register Role-Based Blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/api/v1/gatekeeper')
    app.register_blueprint(admin_blueprint, url_prefix='/api/v1/controller')
    app.register_blueprint(company_blueprint, url_prefix='/api/v1/enterprise')
    app.register_blueprint(student_blueprint, url_prefix='/api/v1/candidate')

    #Background Task Scheduling (Celery Beat)
    celery_app.conf.beat_schedule = {
        'daily-student-reminders': {
            'task': 'tasks.send_daily_reminders',
            'schedule': crontab(hour=9, minute=0), # Runs daily at 9:00 AM
        },
        'monthly-placement-audit': {
            'task': 'tasks.generate_monthly_report',
            'schedule': crontab(day_of_month=1, hour=0, minute=0), # 1st of every month
        }
    }
    celery_app.conf.timezone = 'UTC'

    #Asset Management & Resume Upload Logic
    @app.route('/api/v1/candidate/upload-resume', methods=['POST'])
    def handle_resume_upload():
        """Handles compulsory PDF resume uploads for students."""
        if 'resume' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['resume']
        if file.filename == '' or not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Invalid file. Only PDF allowed."}), 400
        
        filename = secure_filename(file.filename)
        unique_name = f"{os.urandom(4).hex()}_{filename}"
        
        # Ensure upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
        
        return jsonify({
            "message": "Institutional Portfolio Synchronized",
            "filename": unique_name
        }), 200

    #Frontend Serving Logic
    @app.route('/')
    def serve_frontend():
        return send_from_directory(os.path.join(frontend_dir, 'src'), 'index.html')

    @app.route('/components/<path:path>')
    def serve_components(path):
        return send_from_directory(os.path.join(frontend_dir, 'components'), path)

    @app.route('/static/<path:path>')
    def serve_static_assets(path):
        return send_from_directory(os.path.join(frontend_dir, 'static'), path)

    #Programmatic Database Initialization
    with app.app_context():
        # Ensure institutional directories exist
        required_dirs = [
            instance_dir, 
            upload_dir, 
            os.path.join(frontend_dir, 'static', 'reports'),
            os.path.join(frontend_dir, 'static', 'offers'),
            os.path.join(frontend_dir, 'static', 'exports')
        ]
        for d in required_dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                logger.info(f"Initialized directory: {d}")

        db.create_all()
        # Seed the only system admin allowed (Requirement: Programmatic seeding)
        IdentityRegistry.seed_system_admin()

    return app

if __name__ == '__main__':
    shaanu_server = initialize_shaanu_app()
    logger.info("ShaanU Institutional Portal Live: http://localhost:5010")
    # Debug mode enabled for local development
    shaanu_server.run(host='0.0.0.0', port=5010, debug=True)