# Django settings for pocketbook project.

import os
import pocketbook

if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
            os.getenv('SETTINGS_MODE') == 'prod'):
    DEBUG = False
else:
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Matt McCaskey', 'mattmccaskey@gmail.com'),
    )

MANAGERS = ADMINS

    # Running in development, so use a local MySQL database.
if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
    os.getenv('SETTINGS_MODE') == 'prod' or os.getenv('HOME') == '/home3/pbfinancials'):
    # Running on production App Engine, so use a Google Cloud SQL database.
    DATABASES = {
        'default': {
           # 'ENGINE': 'google.appengine.ext.django.backends.rdbms',
           # 'INSTANCE': 'x2-second-inquiry-3:pbfinancials',
           # 'NAME': 'pocketbook',
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'pocketbook',
           'USER': 'pocketbookuser',
           'PASSWORD': '!9229ma((((',
           'HOST': 'localhost',
           'PORT': '',          # Set to empty string for default. Not used with sqlite3.
            }
    }
else:
    # Running in development, so use a local MySQL database.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'pocketbook',
            'USER': 'root',
            'PASSWORD': 'RezSched1234',
            'HOST': 'localhost',
            'PORT': '',          # Set to empty string for default. Not used with sqlite3.
        }
    }


# Local time zone for this installation. Choices can be found here:
# static://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# static://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'site_media/'),

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "static://media.lawrence.com/media/", "static://example.com/media/"
if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
            os.getenv('SETTINGS_MODE') == 'prod'):
    MEDIA_URL = 'static://site_media/'
else:
    MEDIA_URL = 'static://localhost:8000/site_media/'
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"


SETTINGS_PATH = os.path.normpath(os.path.dirname(__file__))


STATICFILES_DIRS = (
    "/Users/mattmccaskey/PycharmProjects/pocketbook/http/site/",
    )
# Additional locations of static files

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8hu0j-=v7!diijql9t1dt*a0--vk*o%!y4lt)k_8x4rstor+8+'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)


# Find templates in the same folder as settings.py.
TEMPLATE_DIRS = (
    os.path.join(SETTINGS_PATH, 'templates'),
    )

ANONYMOUS_USER_ID = -1

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'pocketbook.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'pocketbook.wsgi.application'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'pocketbook',
    'pbfinancials',
)

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'pocketbookincorporated@gmail.com'
EMAIL_HOST_PASSWORD = 'pbfinancials!234'


# URL prefix for static files.
# Example: "static://media.lawrence.com/static/"
STATIC_ROOT = 'static'

STATIC_URL = 'static/'




