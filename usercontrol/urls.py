from django.conf.urls import include, url
from django.contrib import admin
import usercontrol.views

admin.autodiscover()

urlpatterns = [
    url(r'^profile/(?P<username>[-\w]+)$', usercontrol.views.profile,            name = 'profile', prefix='usercontrol.views'),
    url(r'^profile/(?P<username>[-\w]+)/matches$', usercontrol.views.match_list,  name = 'match_list', prefix='usercontrol.views'),
    url(r'^messages/$',                     usercontrol.views.message_list,       name = 'message_list', prefix='usercontrol.views'),
    url(r'^messages/challenges/$',          usercontrol.views.message_challenges, name = 'message_challenges', prefix='usercontrol.views'),
    url(r'^messages/matches/$',             usercontrol.views.message_matches,    name = 'message_matches', prefix='usercontrol.views'),
    url(r'^messages/(?P<message>\d+)/$',    usercontrol.views.message_detail, prefix='usercontrol.views'),
    url(r'^messages/send$',                 usercontrol.views.message_send, prefix='usercontrol.views'),
]
