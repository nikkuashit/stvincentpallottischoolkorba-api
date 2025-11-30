"""
Passenger WSGI configuration for cPanel deployment.
This file is used by Passenger to start your Django application.
"""
import os
import sys

# Add your project directory to the sys.path
# Adjust the path to match your cPanel directory structure
# Example: /home/username/stvincentpallottischoolkorba-api
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'school_api.settings'

# Import Django's WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
