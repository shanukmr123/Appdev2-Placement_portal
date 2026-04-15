#!/usr/bin/env python
"""
Test script to verify circular imports are resolved
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[v0] Testing imports...")

try:
    print("[v0] Importing database module...")
    from database import db
    print("[v0] ✓ Database module imported successfully")
    
    print("[v0] Importing Flask app...")
    from app import app
    print("[v0] ✓ Flask app imported successfully")
    
    print("[v0] Importing models...")
    from models.models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
    print("[v0] ✓ Models imported successfully")
    
    print("[v0] Importing auth routes...")
    from routes.auth import auth_bp
    print("[v0] ✓ Auth routes imported successfully")
    
    print("[v0] Importing admin routes...")
    from routes.admin import admin_bp
    print("[v0] ✓ Admin routes imported successfully")
    
    print("[v0] Importing company routes...")
    from routes.company import company_bp
    print("[v0] ✓ Company routes imported successfully")
    
    print("[v0] Importing student routes...")
    from routes.student import student_bp
    print("[v0] ✓ Student routes imported successfully")
    
    print("\n[v0] SUCCESS: All imports resolved! Circular import fixed.")
    
except ImportError as e:
    print(f"\n[v0] ERROR: Import failed - {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n[v0] ERROR: Unexpected error - {e}")
    sys.exit(1)
