from django.conf.urls.defaults import *
from django.conf import settings as config

urlpatterns = patterns(
    '',
    (r'^%s' % config.SERVER_BASEDIR, include('recap-server.uploads.urls')),
)
