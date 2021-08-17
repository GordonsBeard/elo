from django.conf.urls import include, url
from django.contrib import admin
import usercontrol.views

admin.autodiscover()

urlpatterns = [
    url(r'^profile/(?P<username>[-\w]+)$', usercontrol.views.profile,             name = 'profile'),
    url(r'^profile/(?P<username>[-\w]+)/matches$', usercontrol.views.match_list,  name = 'match_list'),
    url(r'^messages/$',                     usercontrol.views.message_list,       name = 'message_list'),
    url(r'^messages/challenges/$',          usercontrol.views.message_challenges, name = 'message_challenges'),
    url(r'^messages/matches/$',             usercontrol.views.message_matches,    name = 'message_matches'),
    url(r'^messages/(?P<message>\d+)/$',    usercontrol.views.message_detail),
    url(r'^messages/send$',                 usercontrol.views.message_send),
]
