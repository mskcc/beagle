"""
WSGI config for beagle project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
from dj_static import Cling
from django.core.wsgi import get_wsgi_application
from beagle_etl.tasks import fetch_request_nats
from concurrent.futures import ThreadPoolExecutor, wait

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beagle.settings')

# Create Endpoint to start this job
fetch_request_nats.delay()


application = Cling(get_wsgi_application())
