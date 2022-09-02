from django.conf.urls.defaults import *
from django.conf import settings

from .offers import views
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    (r'^admin/(.*)', admin.site.root),
#    (r'^$', views.beta),
    (r'^$', views.login),
    (r'^login$', views.login),
    (r'^instructions$', views.instructions),
    (r'^offer$', views.offer),
    (r'^thanks$', views.thanks),
    (r'^probe_preparation$', views.probe_preparation),
    (r'^probe$', views.probe),
    (r'^trials\.csv$', views.trials_csv),
    (r'^probes\.csv$', views.probes_csv),
    (r'^ips\.csv$', views.ips_csv),
    (r'^summary\.csv$', views.summary_csv),
    (r'^subjects/(?P<subject_name>\S{10})/plot_logistic.png$', views.plot_logistic_png ),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'static/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root' : settings.STATIC_ROOT})
    )
