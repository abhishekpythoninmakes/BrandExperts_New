"""
Django settings for BrandExpertsEcommerce project.
SECURITY ENHANCED VERSION - Addresses all vulnerabilities from security report
"""

from pathlib import Path
from celery.schedules import crontab
import os
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Cloudflare compatibility settings
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = [
    'dash.brandexperts.ae',
    'www.brandexperts.ae',
    'brandexperts.ae',
    'api.brandexperts.ae',
    'designer.brandexperts.ae',
    '.brandexperts.ae',
]

# Add localhost only for development
if DEBUG:
    ALLOWED_HOSTS.extend([
        'localhost',
        '127.0.0.1',
        '65.2.66.156',
    ])

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
    'csp',  # Added for Content Security Policy
]

# SECURITY ENHANCED MIDDLEWARE
MIDDLEWARE = [
    'BrandExpertsEcommerce.middleware.FixCloudflareHostMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BrandExpertsEcommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default=3306, cast=int),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
    }
}

AUTH_USER_MODEL = 'products_app.CustomUser'

# =============================================================================
# SECURITY CONFIGURATIONS - ADDRESSING ALL VULNERABILITIES
# =============================================================================

# 1. CONTENT SECURITY POLICY (CSP) CONFIGURATION
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            'https://www.google-analytics.com',
            'https://www.googletagmanager.com',
            'https://cdnjs.cloudflare.com',
            'https://cdn.jsdelivr.net',
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            'https://fonts.googleapis.com',
            'https://cdnjs.cloudflare.com',
            'https://cdn.jsdelivr.net',
        ],
        'img-src': [
            "'self'",
            'data:',
            'https:',
            'https://www.google-analytics.com',
        ],
        'font-src': [
            "'self'",
            'https://fonts.gstatic.com',
            'https://cdnjs.cloudflare.com',
        ],
        'connect-src': [
            "'self'",
            'https://www.google-analytics.com',
            'https://api.brandexperts.ae',
        ],
        'frame-src': ["'none'"],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
    }
}

# 2. CLICKJACKING PROTECTION
X_FRAME_OPTIONS = 'DENY'

# 3. CORS CONFIGURATION - FIXED (NO DUPLICATES)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://brandexperts.ae",
    "https://www.brandexperts.ae",
    "https://dash.brandexperts.ae",
    "https://designer.brandexperts.ae",
    "https://be-editor-one.vercel.app",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS.extend([
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://65.2.66.156",
    ])

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# 4. CSRF PROTECTION - FIXED (NO DUPLICATES)
CSRF_TRUSTED_ORIGINS = [
    "https://brandexperts.ae",
    "https://api.brandexperts.ae",
    "https://dash.brandexperts.ae",
    "https://www.brandexperts.ae",
    "https://be-editor-one.vercel.app",
    "https://designer.brandexperts.ae",
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://65.2.66.156",
    ])

# 5. HTTPS AND SECURITY SETTINGS - COMPLETELY DISABLE REDIRECTS
# DISABLE ALL SSL REDIRECTS TO PREVENT API LOOPS
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Cookie security - only in production
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Always secure regardless of DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Additional security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# =============================================================================
# END SECURITY CONFIGURATIONS
# =============================================================================

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration - PUBLIC API ENDPOINTS
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # PUBLIC ACCESS FOR ALL ENDPOINTS
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '2000/hour',  # High limit for public APIs
        'user': '5000/hour'   # High limit for authenticated users
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

DOMAIN = 'https://dash.brandexperts.ae'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# CKEditor Configuration
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
            ['Placeholders'],
            ['EmojiPanel'],
        ],
        'height': 300,
        'width': '100%',
        'extraPlugins': 'emoji,textwatcher,textmatch,autocomplete,placeholders',
        'filebrowserUploadUrl': '/ckeditor/upload/',
        'filebrowserBrowseUrl': '/ckeditor/browse/',
        'appName': 'pep_app',
        'extraAllowedContent': 'span(*)[*]{*};',
        'entities': False,
        'entities_latin': False,
        'forceSimpleAmpersand': True,
        'basicEntities': False,
    },
}

CKEDITOR_UPLOAD_PATH = "uploads/"

# API Keys and External Services
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
YOUTUBE_API_KEY = config('YOUTUBE_API_KEY', default='')

# Twilio Configuration
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
CONTENT_SID = config('CONTENT_SID', default='')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER', default='')
EMERGENCY_CONTACT = config('EMERGENCY_CONTACT', default='')

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID = config('WHATSAPP_PHONE_NUMBER_ID', default='')
WHATSAPP_PERMANENT_TOKEN = config('WHATSAPP_PERMANENT_TOKEN', default='')

# Jazzmin Admin Configuration
JAZZMIN_SETTINGS = {
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
    "icons": {
        "auth.Group": "fas fa-users-cog",
        "auth.User": "fas fa-user-shield",
        "customers.Cart_items": "fas fa-shopping-cart",
        "customers.Carts": "fas fa-shopping-basket",
        "customers.Claim_warrantys": "fas fa-clipboard-check",
        "customers.Customer_addresss": "fas fa-map-marker-alt",
        "customers.Customers": "fas fa-user",
        "customers.Orders": "fas fa-box",
        "customers.Warranty_registrations": "fas fa-shield-alt",
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
    "order_with_respect_to": [
        "dashboard",
        "auth",
        "customers",
        "products_app",
    ],
    "copyright": "Copyright © 2025 BrandExperts. All rights reserved.",
    "show_version": False,
}

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
TIMEZONE = 'UTC'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_EAGER_PROPAGATES = True

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Celery Beat Configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BEAT_SCHEDULE = {
    'check-cron-jobs-daily': {
        'task': 'pep_app.tasks.check_and_execute_cron_jobs',
        'schedule': crontab(hour=7, minute=30),
    },
    'backup-database-weekly': {
        'task': 'products_app.tasks.backup_database',
        'schedule': crontab(minute=0, hour=2, day_of_week='sunday'),
    },
}

# Debug print for troubleshooting
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"SECURE_SSL_REDIRECT: {SECURE_SSL_REDIRECT}")
