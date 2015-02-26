from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('ladder.views',
    url(r'^(?P<ladder_slug>[-\w]+)/$',       'index', name='detail'),
    url(r'^(?P<ladder_slug>[-\w]+)/matches/$','match_list', name='match_list'),
    url(r'^(?P<ladder_slug>[-\w]+)/matches/(?P<match_id>\d+)/$','match_detail', name='match_detail'),
    url(r'^create$',                        'create_ladder'),
    url(r'^(?P<ladder_slug>[-\w]+)/join/$',   'join_ladder'),
    url(r'^(?P<ladder_slug>[-\w]+)/leave/$',  'leave_ladder'),
    url(r'^challenge$',                     'issue_challenge', name='issue_challenge'),
)
