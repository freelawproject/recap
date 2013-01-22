import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'recapsite.settings'
os.environ['PYTHON_EGG_CACHE'] = '/usr/local/django/python-eggs'

path = '/var/django/recap_prod'
if path not in sys.path:
    sys.path.append(path)

other_path = '/var/django/recap_prod/recapsite'

if other_path not in sys.path:
    sys.path.append(other_path)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

