from django.conf.urls import include, url
from django.contrib import admin
import ladder.views

admin.autodiscover()

urlpatterns = [
    url(r'^(?P<ladder_slug>[-\w]+)/$', ladder.views.index, name='detail', prefix='ladder.views'),

    url(r'^(?P<ladder_slug>[-\w]+)/matches/$', ladder.views.match_list,   name='match_list',  prefix='ladder.views'),

    url(r'^(?P<ladder_slug>[-\w]+)/matches/(?P<match_id>\d+)/$', ladder.views.match_detail, name='match_detail',prefix='ladder.views'),

    url(r'^add_game$', ladder.views.add_game, prefix='ladder.views'),

    url(r'^(?P<ladder_slug>[-\w]+)/join/$', ladder.views.join_ladder, prefix='ladder.views'),

    url(r'^(?P<ladder_slug>[-\w]+)/leave/$', ladder.views.leave_ladder, prefix='ladder.views'),

    url(r'^challenge$', ladder.views.issue_challenge, name='issue_challenge', prefix='ladder.views'),
]
