from .base import *

SECRET_KEY = 'django-insecure-+&fdiuj#6)k=gctcp*@jcl*ckiu66u3m$!g7bfqa_0+&tj0g5f'
DEBUG = False
ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'iqraa',
        'USER': 'postgres',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
