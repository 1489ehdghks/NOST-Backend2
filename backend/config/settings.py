"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from datetime import timedelta
from pathlib import Path
import os
from . import secret

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secret.SECRET_KEY
OPENAI_API_KEY = secret.OPENAI_API_KEY
DEEPL_API_KEY = secret.DEEPL_API_KEY
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "novel-stella.com",
    "nost-stella.com",
]

# 미디어 파일을 위한 스토리지 설정
# DFFAULT_FILE_STORAGE = "config.asset_storage.MediaStorage"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third Party
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    'rest_framework_simplejwt',
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    # Custom
    "accounts",
    "books",
]

# 사이트 ID
SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# SQLite 사용시
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'NovelStella',
        'USER': 'postgres',
        'PASSWORD': secret.POSTGRESQL_PASSWORD,
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# CORS
CORS_ORIGIN_WHITELIST = [
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "https://novel-stella.com",
    "https://nost-stella.com",
]
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

APPEND_SLASH = False

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# jwt

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# 이메일 백엔드 설정 (개발용)
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# SMTP 설정
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = "587"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = secret.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = secret.EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_CONFIRMATION_REDIRECT_URL = 'https://novel-stella.com'

# 사이트 설정
SITE_NAME = 'Novel Stella'
SITE_DOMAIN = 'novel-stella.com'
FRONTEND_URL = 'https://novel-stella.com'
EMAIL_CONFIRMATION_REDIRECT_URL = f"{FRONTEND_URL}"

# allauth
ACCOUNT_ADAPTER = "accounts.adapters.CustomUserAccountAdapter"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Novel Stella] '
DEFAULT_FROM_EMAIL = 'Novel Stella <ehdghks1489@gmail.com>'
ACCOUNT_EMAIL_CONFIRMATION_URL = f"{FRONTEND_URL}/confirm-email"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = FRONTEND_URL + '/email-confirmed'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = FRONTEND_URL + '/email-confirmed'
EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = FRONTEND_URL


DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.security.csrf': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# rest framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("dj_rest_auth.jwt_auth.JWTAuthentication",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'EXCEPTION_HANDLER': 'accounts.utils.custom_exception_handler',
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 8,
}

# spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "My Django API",
    "DESCRIPTION": "Django DRF API Doc",
    "VERSION": "1.0.0",
}

# dj rest auth
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,
    'JWT_AUTH_SECURE': True,
    'REGISTER_SERIALIZER': 'accounts.serializers.CustomRegisterSerializer',
    'LOGIN_SERIALIZER': 'accounts.serializers.CustomLoginSerializer',
    'USER_DETAILS_SERIALIZER': 'accounts.serializers.CustomUserDetailSerializer',
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'accounts.validators.CustomPasswordValidator',
    }
]
# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# 로컬 스토리지 사용
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# AWS Setting
# if secret.USE_S3:
#     AWS_REGION = "ap-northeast-2"  # AWS서버의 지역
#     AWS_STORAGE_BUCKET_NAME = secret.MY_AWS_STORAGE_BUCKET_NAME  # 생성한 버킷 이름
#     AWS_ACCESS_KEY_ID = secret.MY_AWS_ACCESS_KEY_ID  # 액서스 키 ID
#     AWS_SECRET_ACCESS_KEY = secret.MY_AWS_SECRET_ACCESS_KEY  # 액서스 키 PW
#     # 버킷이름.s3.AWS서버지역.amazonaws.com 형식
#     AWS_S3_CUSTOM_DOMAIN = "%s.s3.%s.amazonaws.com" % (
#         AWS_STORAGE_BUCKET_NAME,
#         AWS_REGION,
#     )
#     # Static Setting
#     STATIC_URL = "https://%s/static/" % AWS_S3_CUSTOM_DOMAIN
#     STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
#     # Media Setting

#     MEDIA_URL = "https://%s/meida/" % AWS_S3_CUSTOM_DOMAIN
#     DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# else:
#     STATIC_URL = "/static/"
#     MEDIA_URL = "/media/"
#     MEDIA_ROOT = BASE_DIR / "media"
