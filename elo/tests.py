import django
from django.conf import settings
from django.contrib.auth import login
from django.http import HttpRequest
from django.test import TestCase, RequestFactory       
from django.test.client import Client
from django.contrib.auth.models import User
from django.utils.importlib import import_module

# Modules to test more or less
from elo.models import UserProfile

# Needed for tests to run in VS
django.setup()

class TestClient(Client):

    def login_user(self, user):
        """
        Login as specified user, does not depend on auth backend (hopefully)

        This is based on Client.login() with a small hack that does not
        require the call to authenticate()
        """
        if not 'django.contrib.sessions' in settings.INSTALLED_APPS:
            raise AssertionError("Unable to login without django.contrib.sessions in INSTALLED_APPS")
        user.backend = "%s.%s" % ("django.contrib.auth.backends", "ModelBackend")
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        if self.session:
            request.session = self.session
        else:
            request.session = engine.SessionStore()
        login(request, user)

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.cookies[session_cookie].update(cookie_data)

        # Save the session values.
        request.session.save()

#client.login_user(self.user1)

class Test_User_Control(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # users
        self.user = User.objects.create_user(username='TestUser', email='test@test.com',  password='test')

    #def test_login_logout_view(self):
    #    """Makes sure the options to login/logout are visible at appropriate times."""

    def test_login_protection(self):
        """ Tests  the login protection for protected views. """
        client = TestClient()
        protected_urls = ( 
                    "/u/messages", 
                    "/u/messages/challenges", 
                    "/u/messages/matches", 
                    "/l/challenge", 
                    "/l/create", 
                    )
        expected_url = "http://testserver/openid/login/?next={0}"

        for test_url in protected_urls:
            response = client.get( test_url )
            self.assertEqual(expected_url.format(test_url), response.url)
            self.assertEqual(response.status_code, 302)
            print "URL [ {0} ]:\tOK!".format( test_url )