"""
WSGI config for config project.
"""

import os
from django.core.wsgi import get_wsgi_application

# Heroku sets DYNO environment variable
if 'DYNO' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_heroku')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
