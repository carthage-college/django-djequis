"""
Django settings for project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from djzbar.settings import INFORMIX_EARL_PROD as INFORMIX_EARL
# sqlserver connection string
MSSQL_EARL = ''
# informix environment for shell scripts that run under cron
INFORMIXSERVER = ''
DBSERVERNAME = ''
INFORMIXDIR = ''
ODBCINI = ''
ONCONFIG = ''
INFORMIXSQLHOSTS = ''
LD_LIBRARY_PATH = '{}/lib:{}/lib/esql:{}/lib/tools:/usr/lib/apache2/modules:{}/lib/cli'.format(
    INFORMIXDIR,INFORMIXDIR,INFORMIXDIR,INFORMIXDIR
)
LD_RUN_PATH = ''

# Debug
#DEBUG = False
DEBUG = True
TEMPLATE_DEBUG = DEBUG
INFORMIX_DEBUG = "debug"
ADMINS = (
    ('', ''),
)
MANAGERS = ADMINS

SECRET_KEY = ""
ALLOWED_HOSTS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
SITE_ID = 1
USE_I18N = False
USE_L10N = False
USE_TZ = False
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'
SERVER_URL = ""
API_URL = "{}/{}".format(SERVER_URL, "api")
LIVEWHALE_API_URL = "https://{}".format(SERVER_URL)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR = os.path.dirname(__file__)
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATIC_URL = "/static/jx/"
ROOT_URL = "/jx/"
MEDIA_ROOT = '{}/assets/'.format(ROOT_DIR)
STATIC_ROOT = '{}/static/'.format(ROOT_DIR)
MEDIA_URL = '{}assets/'.format(STATIC_URL)
UPLOADS_DIR = "{}files/".format(MEDIA_ROOT)
UPLOADS_URL = "{}files/".format(MEDIA_URL)
ROOT_URLCONF = 'djequis.urls'
WSGI_APPLICATION = 'djequis.wsgi.application'
STATICFILES_DIRS = ()
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

DATABASES = {
    'default': {
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'NAME': 'django_djequis',
        'ENGINE': 'django.db.backends.mysql',
        'USER': '',
        'PASSWORD': ''
    },
    'djforms': {
        'HOST': '',
        'PORT': '',
        'NAME': 'django_djforms',
        'ENGINE': 'django.db.backends.mysql',
        'USER': '',
        'PASSWORD': ''
    },
    'rt4': {
        'HOST': '',
        'PORT': '',
        'NAME': 'rt4',
        'ENGINE': 'django.db.backends.mysql',
        'USER': '',
        'PASSWORD': ''
    },
    'admissions': {
        'HOST': '',
        'PORT': '',
        'NAME': 'admissions',
        'ENGINE': 'django.db.backends.mysql',
        'USER': '',
        'PASSWORD': ''
    },
    'tcpayflow': {
        'HOST': '',
        'PORT': '',
        'NAME': 'tcpayflow',
        'ENGINE': 'django.db.backends.mysql',
        'USER': '',
        'PASSWORD': ''
    },
}

INSTALLED_APPS = (
    #'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'djequis',
    'djequis.core',
    # needed for template tags
    'djtools',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # the following should be uncommented unless you are
    # embedding your apps in iframes
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# template stuff
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(os.path.dirname(__file__), 'templates'),
            "/data2/django_templates/djkorra/",
            "/data2/django_templates/djcher/",
            "/data2/django_templates/django-djskins/",
            "/data2/livewhale/includes/",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug':DEBUG,
            'context_processors': [
                "djtools.context_processors.sitevars",
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
            #'loaders': [
            #    # insert your TEMPLATE_LOADERS here
            #]
        },
    },
]
# caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        #'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        #'LOCATION': '127.0.0.1:11211',
        #'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        #'LOCATION': '/var/tmp/django_djequis_cache',
        #'TIMEOUT': 60*20,
        #'KEY_PREFIX': "DJEQUIS_",
        #'OPTIONS': {
        #    'MAX_ENTRIES': 80000,
        #}
    }
}
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
# LDAP Constants
LDAP_SERVER = ''
LDAP_SERVER_PWM = ''
LDAP_PORT = ''
LDAP_PORT_PWM = ''
LDAP_PROTOCOL = ""
LDAP_PROTOCOL_PWM = ""
LDAP_BASE = ""
LDAP_USER = ""
LDAP_PASS = ""
LDAP_EMAIL_DOMAIN = ""
LDAP_OBJECT_CLASS = ""
LDAP_OBJECT_CLASS_LIST = []
LDAP_GROUPS = {}
LDAP_RETURN = []
LDAP_RETURN_PWM = []
LDAP_ID_ATTR = ""
LDAP_CHALLENGE_ATTR = ""
# auth backends
AUTHENTICATION_BACKENDS = (
    'djauth.ldapBackend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
LOGIN_URL = '{}accounts/login/'.format(ROOT_URL)
LOGOUT_URL = '{}accounts/logout/'.format(ROOT_URL)
LOGIN_REDIRECT_URL = ROOT_URL
USE_X_FORWARDED_HOST = True
#SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_DOMAIN=".carthage.edu"
SESSION_COOKIE_NAME ='django_djequis_cookie'
SESSION_COOKIE_AGE = 86400
# SMTP settings
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_FAIL_SILENTLY = False
DEFAULT_FROM_EMAIL = ''
SERVER_EMAIL = ''
SERVER_MAIL=''
# OrgSync
ORGSYNC_HOST=''
ORGSYNC_USER=''
ORGSYNC_PKEY=''
ORGSYNC_PASS=''
ORGSYNC_CSV_OUTPUT=''
ORGSYNC_TO_EMAIL=[]
ORGSYNC_FROM_EMAIL=''
# Schoology
SCHOOLOGY_HOST=''
SCHOOLOGY_USER=''
SCHOOLOGY_API_KEY=''
SCHOOLOGY_API_SECRET=''
SCHOOLOGY_PORT = ''
SCHOOLOGY_PORT=''
SCHOOLOGY_CSV_OUTPUT=''
SCHOOLOGY_CSV_ARCHIVED=''
SCHOOLOGY_TO_EMAIL=[]
SCHOOLOGY_FROM_EMAIL=''
SCHOOLOGY_TEST_GRADES_TRIGGER_JSON_FILE = '{}{}'.format(
    ROOT_DIR, '/core/schoology/tests/grades_trigger.json'
)
SCHOOLOGY_TEST_GRADES_TRIGGER_JSON_FILE_BAD = '{}{}'.format(
    ROOT_DIR, '/core/schoology/tests/grades_trigger_bad.json'
)
SCHOOLOGY_TEST_GRADING_SCALE_FILE = '{}{}'.format(
    ROOT_DIR, '/core/schoology/grading_scale.json'
)
# loan disbursement
FINANCIAL_AID_EMAIL=''
# test
TEST_OUTPUT=''
TEST_USERNAME = ''
TEST_PASSWORD = ''
TEST_EMAIL = ''
# RT
RT_DB_USER = ''
RT_DB_PASS = ''
RT_DB_HOST = ''
RT_DB_NAME = ''
RT_TICKET_STATUS_INCLUDE = ['open (Unchanged)','open','new','stalled']
# admin excludes:
# RT_System
# Nobody
# guest
# cognosadmin@carthage.edu
# cognosadmin
# student
# test
RT_ADMINS = [1,6,93,449,455,707]
# logging
LOG_FILEPATH = os.path.join(os.path.dirname(__file__), "logs/")
LOG_FILENAME = LOG_FILEPATH + "debug.log"
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%Y/%b/%d %H:%M:%S"
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt' : "%Y/%b/%d %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILENAME,
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'include_html': True,
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'djequis': {
            'handlers':['logfile'],
            'propagate': True,
            'level':'DEBUG',
        },
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
