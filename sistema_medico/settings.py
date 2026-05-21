from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
import os
from django.contrib.messages import constants as messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', default=False) == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1','web-production-b3d8.up.railway.app']

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'admin_extra_buttons',
    'whitenoise.runserver_nostatic',
]

LOCAL_APPS = [
    'apps.usuarios',
    'apps.consultas',
    'apps.publicaciones',
    'apps.reportes',
    'chatbot',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

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

ROOT_URLCONF = 'sistema_medico.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'sistema_medico.wsgi.application'


# Database
#https://docs.djangoproject.com/en/4.1/ref/settings/#databases

if DEBUG:
    print("Estas en modo DEBUG con la base de datos local")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.getenv('NAME_BD'),
            'USER': os.getenv('USER_BD'),
            'PASSWORD': os.getenv('PASSWORD_BD'),
            'HOST': os.getenv('HOST_BD'),
            'PORT': os.getenv('PORT_BD'),
        }
    }
else:
    print("Estas en modo producción con la base de datos remota")
    DATABASES = {
        'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
    }

# Para que Django use el modelo "Usuario"
# en lugar del modelo predeterminado "user"
AUTH_USER_MODEL = 'usuarios.Usuario'

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS':{'min_length': 12},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [  # para cargar los archivos estáticos
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuración para archivos subidos por usuarios
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'apps.usuarios.authentication.ClaveBackend',  # Reemplaza 'tu_app' con el nombre de tu aplicación
    'django.contrib.auth.backends.ModelBackend',  # Mantén el backend por defecto
]

# Opción segura por defecto
X_FRAME_OPTIONS = 'DENY'

# Opción si se usan iframes en el mismo dominio
# X_FRAME_OPTIONS = 'SAMEORIGIN'

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# SESSION_COOKIE_SECURE = True     # Solo si usas HTTPS
# CSRF_COOKIE_SECURE = True        # Solo si usas HTTPS

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


CSRF_TRUSTED_ORIGINS = ['http://*', 'https://web-production-b3d8.up.railway.app']


DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD')

LOGIN_REDIRECT_URL = '/'  # redirige a la página principal al iniciar sesión
LOGOUT_REDIRECT_URL = '/'  # redirige a la página principal al cerrar sesión

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 10  # Tiempo de espera para la conexión SMTP en segundos
PASSWORD_RESET_TIMEOUT = 3600  # Tiempo de validez del token de recuperación (1 hora)

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_PLANTILLA_R09 = BASE_DIR / 'plantilla_reporte' / 'R09.xlsx'