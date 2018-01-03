DATABASE_ENGINE = "sqlite3"

ROOT_URLCONF = "user_messages.urls"

TEMPLATE_CONTEXT_PROCESSORS = [
    "user_messages.context_processors.user_messages"
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "user_messages",
]
