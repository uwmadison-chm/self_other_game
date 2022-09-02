from django.conf.urls.defaults import *
from django.conf import settings

from .offers import views
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    (r'^admin/(.*)', admin.site.root),
    (r'^$', views.login),
    (r'^login$', views.login),
    (r'instructions$', views.instructions),
    (r'^offer$', views.offer),
    (r'^thanks$', views.thanks),
    (r'^probe_preparation$', views.probe_preparation),
    (r'^probe$', views.probe),
    (r'^trials\.csv$', views.trials_csv),
    (r'^probes\.csv$', views.probes_csv),
    (r'^summary.csv$', views.summary_csv),
    (r'^evolution.csv$', views.evolution),
    (r'^plot_logistic/$', views.plot_logistic_multiple),
    (r'^plot_logistic.png$', views.plot_logistic_multiple_png),
    (r'^sessions/(?P<session_name>\S{0,3})/plot_logistic.png$', views.plot_logistic_multiple_png),
    (r'^subjects/(?P<subject_name>\S{10})/plot_logistic.png$', views.plot_logistic_png),
    (r'^subjects/(?P<subject_name>\S{10})/plot_logistic/$', views.plot_logistic),
    (r'^subjects/(?P<subject_name>\S{10})/plot_scatter/(?P<var_names>\S{0,40}).png$', views.plot_scatter_png),
    (r'^subjects/(?P<subject_name>\S{10})/plot_scatter/(?P<var_names>\S{0,40}).csv$', views.plot_scatter_csv),
    (r'^ips.csv$', views.ips_csv)
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'static/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root' : settings.STATIC_ROOT})
    )
