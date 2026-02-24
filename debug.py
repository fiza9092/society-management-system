# debug.py
try:
    from flask import Flask
    print("✓ Flask imported")
    
    from flask_sqlalchemy import SQLAlchemy
    print("✓ SQLAlchemy imported")
    
    from flask_login import LoginManager, login_user, login_required, logout_user, current_user
    print("✓ Flask-Login imported")
    
    from datetime import datetime, date
    print("✓ datetime imported")
    
    from dateutil.relativedelta import relativedelta
    print("✓ dateutil imported")
    
    import random
    import os
    print("✓ All imports successful!")
    
except Exception as e:
    print(f"✗ Import error: {e}")