from django.conf.urls import include, url
from django.contrib import admin
import ladder.views

admin.autodiscover()

urlpatterns = [
    url(r'^create/$',       ladder.views.create_ladder,     name='create'),
    url(r'^add_game/$',     ladder.views.add_game,          name='add_game'),

    url(r'^(?P<ladder_slug>[-\w]+)/', include([
        url(r'^$',                              ladder.views.index,                 name='detail'),
        url(r'^matches/$',                      ladder.views.match_list,            name='match_list'),
        url(r'^matches/(?P<match_id>\d+)/$',    ladder.views.match_detail,          name='match_detail'),
        url(r'^join/$',                         ladder.views.join_ladder,           name='join'),
        url(r'^leave/$',                        ladder.views.leave_ladder,          name='leave'),
        url(r'^edit/$',                         ladder.views.update_ladder,         name='update_ladder'),
        url(r'^challenge/$',                    ladder.views.issue_challenge,       name='issue_challenge'),
    ])),
]