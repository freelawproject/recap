#!/bin/bash

export RECAP_PATH=/var/django/recapdev
export PYTHONPATH=$RECAP_PATH
export DJANGO_SETTINGS_MODULE=settings
/usr/bin/python2.5 $RECAP_PATH/uploads/InternetArchive.py >> $RECAP_PATH/cron.log 2>&1
