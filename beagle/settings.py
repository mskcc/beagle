"""
Django settings for beagle project.

Generated by 'django-admin startproject' using Django 2.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import ldap
import datetime
from django_auth_ldap.config import LDAPSearch

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '4gm1)1&0x71+^vwo)rf=%%b)f3l$%u893bs$scif+h#nj@eyx('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['silo', 'localhost']

CORS_ORIGIN_ALLOW_ALL = True

# CORS_ORIGIN_WHITELIST = (
#     'http//:localhost:8000',
# )

# Application definition

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'runner.apps.RunnerConfig',
    'beagle_etl.apps.BeagleEtlConfig',
    'file_system.apps.FileSystemConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_multiple_model',
    'rest_framework_swagger'
]


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': "secret_key",
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': datetime.timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=1),
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_LDAP_SERVER_URI = os.environ.get('BEAGLE_AUTH_LDAP_SERVER_URI', "url_goes_here")

AUTH_LDAP_AUTHORIZE_ALL_USERS = True

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0}
AUTH_LDAP_START_TLS = False

AUTH_LDAP_CACHE_TIMEOUT = 0

AUTH_LDAP_USER_DN_TEMPLATE = '%(user)s@mskcc.org'

AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = True

# AUTH_LDAP_GROUP_TYPE = MemberDNGroupType()
# AUTH_LDAP_GROUP_SEARCH = LDAPSearchUnion(
#     LDAPSearch('DC=MSKCC,DC=ROOT,DC=MSKCC,DC=ORG', ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)"),
# )

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    'DC=MSKCC,DC=ROOT,DC=MSKCC,DC=ORG',
    ldap.SCOPE_SUBTREE,
    '(sAMAccountName=%(user)s)',
    ['sAMAccountName', 'displayName', 'memberOf', 'title']
)

# AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
#     'DC=MSKCC,DC=ROOT,DC=MSKCC,DC=ORG',
#     ldap.SCOPE_SUBTREE,
#     '(sAMAccountName=%(user)s)',
#     '(objectClass=posixGroup)',)

AUTH_LDAP_ALWAYS_UPDATE_USER = True

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# AUTH_LDAP_USER_ATTR_MAP = {
#     "first_name": "givenName",
#     "last_name": "sn",
#     "email": "mail",
# }

# AUTH_LDAP_FIND_GROUP_PERMS = True

# AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn", "email": "mail"}

# AUTH_LDAP_MIRROR_GROUPS = True

# AUTH_LDAP_USER_FLAGS_BY_GROUP = {
#     "is_active": "DC=MSKCC,DC=ROOT,DC=MSKCC,DC=ORG",
#     "is_staff": (
#         LDAPGroupQuery("cn=active,ou=groups,dc=ROOT,dc=com")
#         | LDAPGroupQuery("cn=active,ou=groups,dc=ROOT,dc=com")
#     ),
#     "is_superuser": "cn=active,ou=groups,dc=ROOT,dc=com",
# }

ROOT_URLCONF = 'beagle.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'beagle.wsgi.application'


DB_NAME = os.environ['BEAGLE_DB_NAME']
DB_USERNAME = os.environ['BEAGLE_DB_USERNAME']
DB_PASSWORD = os.environ['BEAGLE_DB_PASSWORD']
DB_HOST = os.environ.get('BEAGLE_DB_URL', 'localhost')
DB_PORT = os.environ.get('BEAGLE_DB_PORT', 5432)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

PAGINATION_DEFAULT_PAGE_SIZE = 10

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'beagle.pagination.BeaglePagination',
    'PAGE_SIZE': PAGINATION_DEFAULT_PAGE_SIZE,
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

RABIX_URL = os.environ.get('BEAGLE_RABIX_URL')
RABIX_PATH = os.environ.get('BEAGLE_RABIX_PATH')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'beagle-cache',
    }
}

RABBITMQ_USERNAME = os.environ.get('BEAGLE_RABBITMQ_USERNAME', 'guest')
RABBITMQ_PASSWORD = os.environ.get('BEAGLE_RABBITMQ_PASSWORD', 'guest')
RABBITMQ_URL = os.environ.get('BEAGLE_RABBITMQ_URL', 'localhost')

CELERY_BROKER_URL = 'amqp://%s:%s@%s/' % (RABBITMQ_USERNAME, RABBITMQ_PASSWORD, RABBITMQ_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_CONCURRENCY = 1
CELERY_EVENT_QUEUE_PREFIX = os.environ.get('BEAGLE_CELERY_QUEUE_PREFIX', 'beagle.production')

LIMS_USERNAME = os.environ.get('BEAGLE_LIMS_USERNAME')
LIMS_PASSWORD = os.environ.get('BEAGLE_LIMS_PASSWORD')

LIMS_URL = os.environ.get('BEAGLE_LIMS_URL', 'https://igolims.mskcc.org:8443')

IMPORT_FILE_GROUP = os.environ.get('BEAGLE_IMPORT_FILE_GROUP', '1a1b29cf-3bc2-4f6c-b376-d4c5d701166a')

POOLED_NORMAL_FILE_GROUP = os.environ.get('BEAGLE_POOLED_NORMAL_FILE_GROUP', '1552617b-3b06-46de-921a-a000a9129385')

RIDGEBACK_URL = os.environ.get('BEAGLE_RIDGEBACK_URL', 'http://localhost:5003')

LOG_PATH = os.environ.get('BEAGLE_LOG_PATH', 'beagle-server.log')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_PATH,
            "maxBytes": 209715200,
            "backupCount": 10
        }
    },
    "loggers": {
        "django_auth_ldap": {
            "level": "DEBUG", "handlers": ["console"]
        },
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

BEAGLE_URL = 'http://silo:5001'

BEAGLE_RUNNER_QUEUE = os.environ.get('BEAGLE_RUNNER_QUEUE', 'beagle_runner_queue')
BEAGLE_DEFAULT_QUEUE = os.environ.get('BEAGLE_DEFAULT_QUEUE', 'beagle_default_queue')
BEAGLE_JOB_SCHEDULER_QUEUE = os.environ.get('BEAGLE_JOB_SCHEDULER_QUEUE', 'beagle_job_scheduler_queue')

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PROJECT_DIR)
TEST_FIXTURE_DIR = os.path.join(ROOT_DIR, "fixtures", "tests")
DUMP_JSON = os.environ.get('DUMP_JSON') == 'True'
