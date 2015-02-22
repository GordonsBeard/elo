from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase, RequestFactory       
from django.test.client import Client
from django.utils.importlib import import_module

# Modules to test more or less
from elo.models import UserProfile

# Needed for tests to run in VS
import django
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

class Test_Login_Views(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # users
        self.user = User.objects.create_user(username='TestUser', email='test@test.com',  password='test')

    def test_login_link(self):
        """Makes sure the option to login is visible at appropriate time."""
        client = TestClient()
        response = client.get( '/' )
        self.assertInHTML( '<a href="/openid/login">Log In</a>', response.content )

    def test_logout_link(self):
        """Makes sure the options to logout is visible at appropriate time."""
        client = TestClient()
        
        # Log the user in first
        client.login_user(self.user)

        response = client.get( '/' )
        self.assertInHTML( '<a href="/logout">logout</a>', response.content )

    def test_login_protection(self):
        """ Tests the login protection/redirect for protected views. """
        client = TestClient()
        protected_urls = ( 
                    "/u/messages/", 
                    "/u/messages/challenges/", 
                    "/u/messages/matches/", 
                    "/l/challenge", 
                    "/l/create", 
                    )
        expected_url = "http://testserver/openid/login/?next={0}"

        for test_url in protected_urls:
            response = client.get( test_url )
            self.assertEqual(expected_url.format(test_url), response.url)
            self.assertEqual(response.status_code, 302)