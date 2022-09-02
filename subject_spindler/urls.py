from django.conf.urls.defaults import *
from django.conf import settings

from .spindler import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^subject_spindler/', include('subject_spindler.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^sessions/(\d+)\.?(\w+)?$', views.show),
    (r'^admin/', admin.site.urls),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'static/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root' : settings.STATIC_ROOT})
    )