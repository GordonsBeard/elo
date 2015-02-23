"""
Django settings for elo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'YOUR SECRET KEY GOES HERE'    # Remember to change this

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_openid_auth',
    # 'django_evolution',

    'ladder',
    'elo',
    'usercontrol',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'elo.urls'

WSGI_APPLICATION = 'elo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'dbase', 'elo.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'America/Chicago'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/'   # Change this when deployed

# Steam API key
STEAM_API_KEY = 'CHANGE ME TO YOUR STEAM KEY!!!!!!!!' # Get one at http://steamcommunity.com/dev/apikey

# Authentification for OpenID
AUTHENTICATION_BACKENDS = (
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# To create users automatically when a new OpenID is used
OPENID_CREATE_USERS = True

# To have user details updated from OpenID Simple Registration or Attribute Exchange extension data each time they log in
OPENID_UPDATE_DETAILS_FROM_SREG = True

# Login redirect stuff
LOGIN_URL = '/openid/login/'
LOGIN_REDIRECT_URL = '/'

# Redirect to Steam login
OPENID_SSO_SERVER_URL = 'http://steamcommunity.com/openid'

OPENID_FOLLOW_RENAMES = False

# Lets admins log in via openid. NEED A NON-OPENID ADMIN FIRST
OPENID_USE_AS_ADMIN_LOGIN = True

# Extend user profiles using this model
AUTH_PROFILE_MODULE = 'elo.UserProfile'

# To allow sub-domain cross-site authenticating
CSRF_COOKIE_DOMAIN = '127.0.0.1'    # Set this to your domain

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'