from django.conf.urls.defaults import *
from django.conf import settings

from offers import views

urlpatterns = patterns('',
    (r'^$', views.instructions),
    (r'^offer$', views.offer),
    (r'^probe_preparation$', views.probe_preparation),
    (r'^probe$', views.probe),
    (r'plot_logistic$', views.plot_logistic),
    (r'^plot_logistic\.png$', views.plot_logistic_png),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root' : settings.STATIC_ROOT})
    )