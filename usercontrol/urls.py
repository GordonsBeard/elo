from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('usercontrol.views',
    url(r'^(?P<username>[-\w]+)/$',         'profile', name = 'profile'),
    url(r'^messages/$',                     'message_list'),
    url(r'^messages/(?P<message>\d+)/$',    'message_detail'),
    url(r'^messages/send$',                 'message_send'),
)
