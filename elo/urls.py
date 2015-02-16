from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$',                  'elo.views.index'),
    url(r'^admin/',             include(admin.site.urls)),
    url(r'^openid/complete/$',  'elo.views.login'),
    url(r'^openid/',            include('django_openid_auth.urls')),
    url(r'^logout/$',           'elo.views.logout_view'),
    url(r'^l/',                include('ladder.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
