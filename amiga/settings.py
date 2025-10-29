"""
Django settings for amiga project.
Works locally (SQLite) and on Render / Railway (PostgreSQL).
"""

import os
from pathlib import Path

# ------------------------------------------------------------
# Optional: python-decouple with graceful fallback
# ------------------------------------------------------------
try:
    from decouple import config
except ImportError:                     # decouple not installed → use os.environ
    def config(key, default=None, cast=None):
        value = os.getenv(key, default)
        if cast is bool:
            return str(value).lower() in ("true", "1", "yes", "on")
        if cast is int:
            return int(value) if value else default
        return value

# ------------------------------------------------------------
# Base Directory
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------
# Security
# ------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key')

DEBUG = config('DEBUG', default=False, cast=bool)

# Allow your domain + local dev + Render/Railway
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='amigos-gh5d.onrender.com,127.0.0.1,localhost'
).split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://amigos-gh5d.onrender.com',
    'https://purple-field-production.up.railway.app',
]


# ------------------------------------------------------------
# Application Definition
# ------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'votes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'amiga.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'amiga.wsgi.application'


# ------------------------------------------------------------
# Database Configuration
# ------------------------------------------------------------
import dj_database_url

# Default: SQLite (local development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# -----------------------------------------------------------------
# ONLY switch to PostgreSQL when a **valid** DATABASE_URL is provided
# -----------------------------------------------------------------
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL and DATABASE_URL.strip():          # <-- IMPORTANT CHECK
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True if 'render.com' in DATABASE_URL else False
    )


# ------------------------------------------------------------
# Password Validation
# ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------
# Static Files
# ------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ------------------------------------------------------------
# Default Primary Key Field Type
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ------------------------------------------------------------
# Authentication redirects
# ------------------------------------------------------------
LOGIN_REDIRECT_URL = '/votes/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'