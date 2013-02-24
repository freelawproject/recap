#!/bin/bash

export PYTHONPATH=/var/django/recap_dev:/var/django/recap_dev/recapsite
export DJANGO_SETTINGS_MODULE=recapsite.settings
/usr/bin/python2.5 /var/django/recap_dev/recapsite/uploads/InternetArchive.py >> /var/django/recap_dev/recapsite/cron.log 2>&1
