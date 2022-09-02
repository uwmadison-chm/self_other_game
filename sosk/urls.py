from django.conf.urls.defaults import *
from django.conf import settings

from .offers import views
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root))

urlpatterns += patterns('offers.views',
    (r'^$', 'login'),
    (r'^login$', 'login'),
    (r'instructions$', 'instructions'),
    (r'^offer$', 'offer'),
    (r'^thanks$', 'thanks'),
    (r'^probe_preparation$', 'probe_preparation'),
    (r'^probe$', 'probe'),
    (r'^trials\.csv$', 'trials_csv'),
    (r'^probes\.csv$', 'probes_csv'),
    (r'^summary.csv$', 'summary_csv'),
    (r'^evolution.csv$', 'evolution'),
    (r'^plot_logistic/$', 'plot_logistic_multiple'),
    (r'^plot_logistic.png$', 'plot_logistic_multiple_png'),
    (r'^sessions/(?P<session_name>\S{0,3})/plot_logistic.png$', 'plot_logistic_multiple_png'),
    (r'^subjects/(?P<subject_name>\S{10})/plot_logistic.png$', 'plot_logistic_png'),
    (r'^subjects/(?P<subject_name>\S{10})/plot_logistic.pdf$', 'plot_logistic_pdf'),
    (r'^subjects/(?P<subject_name>\S{10})/plot_logistic/$', 'plot_logistic'),
    (r'^subjects/(?P<subject_name>\S{10})/plot_scatter/(?P<var_names>\S{0,40}).png$', 'plot_scatter_png'),
    (r'^subjects/(?P<subject_name>\S{10})/plot_scatter/(?P<var_names>\S{0,40}).csv$', 'plot_scatter_csv'),
    (r'^ips\.csv$', 'ips_csv'),
    (r'^m2\.csv$', 'm2_csv'),
    (r'^m_self_ratio\.csv$', 'm_self_ratio_csv'),
    (r'^m_big_ratio\.csv$', 'm_big_ratio_csv'),
    (r'^ip_parade\.csv$', 'ips_4_csv'),
    (r'^ips_100_self_cutoff\.csv$', 'ips_100_self_cutoff_csv'),
    (r'^m2_100_self_cutoff\.csv$', 'm2_100_self_cutoff_csv'),
    (r'^m_self_ratio_100_self_cutoff\.csv$', 'm_self_ratio_100_self_cutoff_csv'),
    (r'^ip_parade_100_self_cutoff\.csv$', 'ips_100_self_cutoff_4_csv'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'static/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root' : settings.STATIC_ROOT})
    )
