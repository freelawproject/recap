from django.conf.urls import patterns

urlpatterns = patterns(
    'uploads.views',
    (r'^$', 'index'),
    (r'^upload/$', 'upload'),
    (r'^query/$', 'query'),
    (r'^query_cases/$', 'query_cases'),
    (r'^adddocmeta/$', 'adddocmeta'),
    (r'^lock/$', 'lock'),
    (r'^unlock/$', 'unlock'),
    (r'^querylocks/$', 'querylocks'),
    (r'^get_updated_cases/$', 'get_updated_cases'),
    (r'^heartbeat/$', 'heartbeat'),
    (r'^load/$', 'load'),
)
