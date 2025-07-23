from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-1#m%_!aph(^#4s%@3@vf38vyfqn6(-j+n6#@)x$2ogdz=1)3qs'

DEBUG = False

# Corrigir ALLOWED_HOSTS — não pode ter barra, deve ser apenas host/ip
ALLOWED_HOSTS = ['148.230.73.228']

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

INSTALLED_APPS = [
    'site_admin',
    'core',
    "admin_interface",
    "colorfield",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

ADMIN_INTERFACE_CONFIG = {
    'theme': 'light',
    'name': 'DIÁRIO DE CLASSE DIGITAL',
    'logo': 'static/images/logo-escola.png',
    'default_theme': {
        'css_header_background_color': '#2A3F54',
        'css_header_text_color': '#FFFFFF',
        # demais configurações do tema...
    }
}

ADMIN_SITE_HEADER = "DIÁRIO DE CLASSE DIGITAL"
ADMIN_SITE_TITLE = "Painel Administrativo"
ADMIN_INDEX_TITLE = "Bem-vindo ao Painel de Controle"

MIDDLEWARE = [
    'core.middleware.ModalLoginMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'diario_classe.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Atenção ao caminho correto do templates
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

WSGI_APPLICATION = 'diario_classe.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "classe_digital_db",
        "USER": "classe_user",
        "PASSWORD": "@vuc15197575K",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'  # É recomendado iniciar com barra para URL

# Pasta onde ficam arquivos estáticos do projeto durante o desenvolvimento
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Pasta onde arquivos estáticos serão coletados para produção
STATIC_ROOT = BASE_DIR / 'staticfiles'

# URL e diretório para arquivos de mídia (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Evitar usar o os.path.join duplicado

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
