from .base import *

SECRET_KEY = 'django-insecure-+&fdiuj#6)k=gctcp*@jcl*ckiu66u3m$!g7bfqa_0+&tj0g5f'
DEBUG = True
ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
