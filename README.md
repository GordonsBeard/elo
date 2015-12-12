ELO
===
Electronic Ladder Organizer

Allows users to create arbitrary ladders for any game they wish, and then challenge each other for positions on the ladder. 

*Pronounced "E. L. O." as it's an actual acronym, unlike Elo.*

___


To get setup:

* Rename and edit ``elo\settings.template.py`` to ``elo\settings.py``
* Create databases ``> python manage.py migrate --run-syncdb``
* Create superuser ``> python manage.py createsuperuser``
* Update ``django-openid-auth/views.py``. Find all instances of ``request.REQUEST.`` and change to ``request.GET.``
* *(optional)* Log in as Steam user, set this user as admin, then set ``OPENID_USE_AS_ADMIN_LOGIN`` to ``True``
* *(optional)* Remove annoying warnings by updating ``django-openid-auth/urls.py``

___

    from __future__ import unicode_literals

	from django.conf.urls import url
	import django_openid_auth.views

	urlpatterns = [
		url(r'^login/$', django_openid_auth.views.login_begin, name='openid-login', prefix='django_openid_auth.views'),
		url(r'^complete/$', django_openid_auth.views.login_complete, name='openid-complete', prefix='django_openid_auth.views'),
		url(r'^logo.gif$', django_openid_auth.views.logo, name='openid-logo', prefix='django_openid_auth.views'),
	]