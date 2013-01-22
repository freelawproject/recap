from django.conf.urls.defaults import *
from uploads.recap_config import config

urlpatterns = patterns('',
                       (r'^%s' % config["SERVER_BASEDIR"], 
                        include('recapsite.uploads.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
