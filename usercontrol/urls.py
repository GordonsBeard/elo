from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('usercontrol.views',
    url(r'^profile/(?P<username>[-\w]+)$', 'profile',            name = 'profile'),
    url(r'^profile/(?P<username>[-\w]+)/matches$', 'match_list',  name = 'match_list'),
    url(r'^messages/$',                     'message_list',       name = 'message_list'),
    url(r'^messages/challenges/$',          'message_challenges', name = 'message_challenges'),
    url(r'^messages/matches/$',             'message_matches',    name = 'message_matches'),
    url(r'^messages/(?P<message>\d+)/$',    'message_detail'),
    url(r'^messages/send$',                 'message_send'),
)
