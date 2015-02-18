from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('ladder.views',
    url(r'^(?P<ladderslug>[-\w]+)/$',       'index'),
    url(r'^create$',                        'create_ladder'),
    url(r'^(?P<ladderslug>[-\w]+)/join$',   'join_ladder'),
    url(r'^(?P<ladderslug>[-\w]+)/leave$',  'leave_ladder'),
    url(r'^challenge$',                     'issue_challenge', name='issue_challenge'),
)
