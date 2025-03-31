"""
Django settings for BrandExpertsEcommerce project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-t7*2el()8a*qrz%!p#quy8m-%6rlgb(7m@#xk*!(tk+m95#dk9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'dash.brandexperts.ae',
    'www.brandexperts.ae',
    'brandexperts.ae',
    'localhost',
    '127.0.0.1',
    'http://localhost:5173',
    'http://localhost:5174',
]



# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'corsheaders',
    'django.contrib.contenttypes',
    'whitenoise.runserver_nostatic',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ckeditor',
    'ckeditor_uploader',
    'django_json_widget',
    'customer',
    'products_app',
    'django_celery_results',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'pep_app',
    'partner_app',
    'django_celery_beat',
    'dbbackup',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
import os
ROOT_URLCONF = 'BrandExpertsEcommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,"templates")],
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

WSGI_APPLICATION = 'BrandExpertsEcommerce.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'MYBE',
        'USER': 'admin',
        'PASSWORD': 'database1brandexperts',
        'HOST':'databasebe.cz6qg420mik4.ap-south-1.rds.amazonaws.com',
        'PORT':3306
    }
}


AUTH_USER_MODEL = 'products_app.CustomUser'


CORS_ALLOWED_ORIGINS = [
    "https://brandexperts.ae",
    "http://localhost:5173",
    "https://www.brandexperts.ae",
    "https://dash.brandexperts.ae",
    "http://localhost:5174",
    "http://localhost:3000",
    "https://be-editor-one.vercel.app",
    "https://designer.brandexperts.ae",
    "http://designer.brandexperts.ae",
]



CORS_ALLOW_CREDENTIALS = True


CSRF_TRUSTED_ORIGINS = [
    "https://brandexperts.ae",
    "https://api.brandexperts.ae",
    "https://dash.brandexperts.ae",
    "https://www.brandexperts.ae",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "https://be-editor-one.vercel.app",
    "https://designer.brandexperts.ae",
    "http://designer.brandexperts.ae",
]



CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "origin",
    "x-requested-with",
    "x-csrftoken"
]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',  # Use local memory cache
        'LOCATION': 'unique-snowflake',  # Unique identifier for the cache
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
import os

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
DOMAIN = 'https://dash.brandexperts.ae'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.ap-south-1.amazonaws.com'  # AWS SES SMTP server
EMAIL_PORT = 587  # Use STARTTLS
EMAIL_USE_TLS = True  # Enable TLS
EMAIL_USE_SSL = False  # Ensure SSL is disabled for STARTTLS
EMAIL_HOST_USER = 'AKIA3C6FL5S2HPHYRYNN'  # AWS SES SMTP user name
EMAIL_HOST_PASSWORD = 'BJ+TcRmykGY8TWMTkFrt9nG3c3NW1HTL2iRtXpTRKpx6'  # AWS SES SMTP password
DEFAULT_FROM_EMAIL = 'hello@brandexperts.ae'  # Your official email

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'toolbar_Custom': [
            ['Source', '-', 'Save', 'NewPage', 'Preview', '-', 'Templates'],
            ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'],
            ['Find', 'Replace', '-', 'SelectAll'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Table', 'HorizontalRule', 'SpecialChar'],
            ['Styles', 'Format', 'Font', 'FontSize'],
            ['TextColor', 'BGColor'],
            ['Maximize', 'ShowBlocks'],
            ['Placeholders'],  # Add our custom dropdown
        ],
        'height': 300,
        'width': '100%',
        'extraPlugins': 'placeholders',  # Use a string instead of join for a single plugin
        'filebrowserUploadUrl': '/ckeditor/upload/',
        'filebrowserBrowseUrl': '/ckeditor/browse/',
        # Pass your app name to the plugin
        'appName': 'pep_app',  # Replace with your actual app name
    },
}

CKEDITOR_UPLOAD_PATH = "uploads/"


from decouple import config

# Retrieve the Stripe secret key from the .env file
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')


GEMINI_API_KEY = config('GEMINI_API_KEY')
YOUTUBE_API_KEY = config('YOUTUBE_API_KEY')

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')
CONTENT_SID = config('CONTENT_SID')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER')
EMERGENCY_CONTACT = config('EMERGENCY_CONTACT')

WHATSAPP_PHONE_NUMBER_ID = config('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_PERMANENT_TOKEN = config('WHATSAPP_PERMANENT_TOKEN')





JAZZMIN_SETTINGS = {
    # General Settings
    "site_title": "BrandExperts Admin",
    "site_header": "BrandExperts Dashboard",
    "site_brand": "BrandExperts",
    "site_logo": "img/logos/br_logo-JUO0DtaB.png",
    "site_icon": "img/logos/br_logo-JUO0DtaB.png",
    "theme": "cyborg",
    "custom_css": "css/custom_admin.css",
    "custom_js": "js/custom_admin.js",
    "primary_color": "#BF1A1C",
    "secondary_color": "#590C0D",
    "dark_mode_toggle": True,
    "show_ui_builder": False,
    "welcome_sign": "Welcome to BrandExperts Admin",

    # Icons Configuration (Ensure Font Awesome is loaded via local font.css)
    "icons": {
        # Auth
        "auth.Group": "fas fa-users-cog",
        "auth.User": "fas fa-user-shield",

        # Customers App
        "customers.Cart_items": "fas fa-shopping-cart",
        "customers.Carts": "fas fa-shopping-basket",
        "customers.Claim_warrantys": "fas fa-clipboard-check",
        "customers.Customer_addresss": "fas fa-map-marker-alt",
        "customers.Customers": "fas fa-user",
        "customers.Orders": "fas fa-box",
        "customers.Warranty_registrations": "fas fa-shield-alt",

        # Products App
        "products_app.Categorys": "fas fa-tags",
        "products_app.Designer_rates": "fas fa-paint-brush",
        "products_app.Higher_designers": "fas fa-user-tie",
        "products_app.Parent_categorys": "fas fa-folder-tree",
        "products_app.Product_offer_sliders": "fas fa-percent",
        "products_app.Product_statuss": "fas fa-check-circle",
        "products_app.Products": "fas fa-box-open",
        "products_app.Standard_sizess": "fas fa-ruler-combined",
        "products_app.Users": "fas fa-user-circle",
        "products_app.Vats": "fas fa-receipt",
        "products_app.Warranty_plans": "fas fa-file-invoice-dollar",
    },

    # Menu Structure
    "order_with_respect_to": [
        "dashboard",
        "auth",
        "customers",
        "products_app",
    ],

    # Footer
    "copyright": "Copyright © 2025 BrandExperts. All rights reserved.",
    "show_version": False,
}


# Celery settings
# CELERY_BROKER_URL = 'amqp://your_user:your_password@35.174.174.152//'
# CELERY_ACCEPT_CONTENT = ['json']
# ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# RESULT_SERIALIZER = 'json'
# TIMEZONE = 'UTC'
# CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# CELERY_RESULT_BACKEND = 'django-db'



# Celery settings for local RabbitMQ
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'  # Store results in Django DB
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
TIMEZONE = 'UTC'

# CELERY_BROKER_URL = 'amqp://your_user:your_password@65.1.248.191:5672//'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_BACKEND = 'django-db'
# CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# TIMEZONE = 'UTC'



# CELERY_TASK_ALWAYS_EAGER = True  # Temporary - tasks run synchronously
CELERY_TASK_EAGER_PROPAGATES = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}


# CELERY BEAT SETTINGS


CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


from celery.schedules import crontab


BACKUP_NOTIFICATION_EMAIL = 'me@subodh.co.in'

from datetime import timedelta

CELERY_BEAT_SCHEDULE = {
    'backup-database-weekly': {
        'task': 'products_app.tasks.backup_database',
        'schedule': crontab(minute=0, hour=2, day_of_week='sunday'),  # Runs every Sunday at 2 AM
    },
}

