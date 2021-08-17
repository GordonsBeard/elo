from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
import ladder.views
import elo.views
from django.urls import include, path

app_name = 'elo'
urlpatterns = [
    url(r'^$',          ladder.views.index,                             name='index'),
    url(r'^l/',         include(('ladder.urls', 'ladder'),              namespace = 'ladder')),
    url(r'^u/',         include(('usercontrol.urls', 'usercontrol'),    namespace = 'user')),
    url(r'^logout/$',   elo.views.logout_view,                          name='logout'),
    url(r'^admin/',     admin.site.urls,                                name='admin'),
]