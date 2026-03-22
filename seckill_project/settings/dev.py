from .base import *

# 开发环境配置
DEBUG = True

ALLOWED_HOSTS = ['*']

# 数据库配置 - 使用 MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'seckill_db',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'sql_mode': 'STRICT_TRANS_TABLES',
        },
    }
}

# Redis 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'socket_timeout': 30,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 30,
        }
    }
}

# 使用 Redis 存储 Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
