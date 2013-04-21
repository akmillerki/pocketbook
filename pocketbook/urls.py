from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import pbfinancials
from pocketbook import settings


admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    (r'^pocketbook/accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^pocketbook/accounts/profile/$', 'pbfinancials.views.home', {}),
    (r'static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
    url(r'^$', 'pocketbook.views.index', name='index'),
    #url(r'^pbfinancials/', include('pbfinancials.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pbfinancials/', include('pbfinancials.urls')),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': '/Users/mattmccaskey/PycharmProjects/pocketbook/site_media/'}),
)
