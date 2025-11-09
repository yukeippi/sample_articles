import os

import environ
from django.core.management.utils import get_random_secret_key

from .base import *

# 開発は .env.dev を優先して読む
env_path = os.path.join(BASE_DIR, '.env.dev')
if os.path.exists(env_path):
    environ.Env.read_env(env_path)

DEBUG = True

# 開発用 SECRET_KEY（未設定なら一時キーを生成）
SECRET_KEY = env('DJANGO_SECRET_KEY', default=get_random_secret_key())

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# 開発環境でのログ設定
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
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.utils.autoreload': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
