from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('ladder.views',
    url(r'^(?P<ladder>[-\w]+)/$',           'index'),
    url(r'^(?P<ladder>.*)/join/$',          'join_ladder'),
    url(r'^(?P<ladder>.*)/challenge/(?P<challengee>.*)$',     'challenge_list'),
)
