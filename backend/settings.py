import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

# Détection environnement Railway
USE_PRODUCTION_DB = os.environ.get("USE_PRODUCTION_DB", "").lower() in ["1", "true", "yes"]
DATABASE_URL = os.environ.get("DATABASE_URL")

# Base dir
BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-59xg396)ocz*e_sr*1133)wgdq-u_kr0n&wmc5f1y!(*^+-tbc")

# Debug (désactive en prod)
DEBUG = True

# Hôtes autorisés
ALLOWED_HOSTS = [
    "localhost", "127.0.0.1", "192.168.0.137", "192.168.2.114",
    "saas-whatsapp-backend-production.up.railway.app"
]

# Apps installées
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "bot",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_yasg",
    "corsheaders",
]

# Middlewares
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "backend.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Base de données
if USE_PRODUCTION_DB and DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'nom_local',
            'USER': 'utilisateur_local',
            'PASSWORD': 'mot_de_passe_local',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

# Auth user
AUTH_USER_MODEL = 'accounts.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# Internationalisation
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Fichiers statiques & médias
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Clé primaire auto
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Swagger
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
}

# Whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Sécurité (à adapter si prod)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
