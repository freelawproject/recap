# Public django settings for recap-server project. This file is dynamically
# read by settings.py in the root directory. All values in this file are
# essentially transcluded into that file.
import os 
import logging

DEBUG = True
TEMPLATE_DEBUG = DEBUG


ADMINS = (
    DJANGO_ADMIN,  # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS


SERVER_EMAIL = "recaplogger@gmail.com"
DEFULT_FROM_EMAIL = "recaplogger@gmail.com"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'recaplogger@gmail.com'
# EMAIL_HOST_PASSWORD = '' # Set in 05-private.py
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_TLS = True


logging.basicConfig(
    level = logging.DEBUG if DEBUG else logging.INFO,
    format = '%(asctime)s %(levelname)s %(name)s: %(message)s',
    filename = ROOT_PATH + '/debug.log',
    filemode = 'a'
)


DATABASE_ENGINE = 'mysql'
# DATABASE_NAME = '' # Set in 05-private.py
# DATABASE_USER = '' # Set in 05-private.py
# DATABASE_PASSWORD = '' # Set in 05-private.py
DATABASE_HOST = '' # Set to empty string for localhost.
DATABASE_PORT = '' # Set to empty string for default.


# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ROOT_PATH + '/templates',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'recap-server.uploads',
)
