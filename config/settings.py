from pathlib import Path
import environ
BASE_DIR=Path(__file__).resolve().parent.parent
env=environ.Env(DEBUG=(bool,False)); environ.Env.read_env(BASE_DIR/".env")
SECRET_KEY=env("SECRET_KEY",default="unsafe-dev-key-change-me")
DEBUG=env("DEBUG",default=True); ALLOWED_HOSTS=env.list("ALLOWED_HOSTS",default=["127.0.0.1","localhost"])
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "library",
    "ai_runtime",
]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="config.wsgi.application"; ASGI_APPLICATION="config.asgi.application"
if env("DB_NAME",default="mizan_al_tahqiq"):
 DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":env("DB_NAME"),"USER":env("DB_USER",default="postgres"),"PASSWORD":env("DB_PASSWORD",default=""),"HOST":env("DB_HOST",default="127.0.0.1"),"PORT":env("DB_PORT",default="5432"),"CONN_MAX_AGE":60}}
else: DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS=[{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE="en-us"; TIME_ZONE="Asia/Kolkata"; USE_I18N=True; USE_TZ=True
STATIC_URL="static/"; STATIC_ROOT=BASE_DIR/"staticfiles"; MEDIA_URL="media/"; MEDIA_ROOT=BASE_DIR/env("MEDIA_ROOT",default="media")
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
REST_FRAMEWORK={"DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.IsAuthenticatedOrReadOnly"],"DEFAULT_AUTHENTICATION_CLASSES":["rest_framework.authentication.SessionAuthentication","rest_framework.authentication.BasicAuthentication"],"DEFAULT_PAGINATION_CLASS":"rest_framework.pagination.PageNumberPagination","PAGE_SIZE":25}

# Local AI Runtime — Ollama
OLLAMA_BASE_URL = env(
    "OLLAMA_BASE_URL",
    default="http://127.0.0.1:11434"
)

OLLAMA_TIMEOUT = env.int(
    "OLLAMA_TIMEOUT",
    default=120
)