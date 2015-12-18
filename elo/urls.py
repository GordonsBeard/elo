from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
import django.views
import ladder.views
import elo.views

admin.autodiscover()

urlpatterns = [
    url(r'^$',                      ladder.views.index),
    url(r'^l/',                     include('ladder.urls', namespace = "ladder")),
    url(r'^u/',                     include('usercontrol.urls', namespace = "user")),
    url(r'^admin/',                 include(admin.site.urls)),
    url(r'^openid/complete/$',      elo.views.login),
    url(r'^openid/',                include('django_openid_auth.urls')),
    url(r'^logout/$',               elo.views.logout_view),
    url(r'^create/$',               ladder.views.create_ladder),
    url(r'^add_game/$',             ladder.views.add_game),
]