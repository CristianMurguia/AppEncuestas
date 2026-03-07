import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('Django_SETTINGS_MODULE', 'survey_project.settings')

application = get_wsgi_application()