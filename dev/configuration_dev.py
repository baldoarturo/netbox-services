"""
NetBox configuration to develop a plugin: self-contained (it does not need the
configuration.py of the NetBox checkout), with its own database so the plugin's
migrations never run against any other database.

Used through NETBOX_CONFIGURATION=configuration_dev, see dev/run.sh, which sets
PLUGIN_MODULE and PLUGIN_DEV_DB from dev/plugin.conf.
"""

import os

ALLOWED_HOSTS = ['*']

DATABASE = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ['PLUGIN_DEV_DB'],
    'USER': 'netbox',
    'PASSWORD': 'netbox',
    'HOST': os.environ.get('NETBOX_DB_HOST', 'localhost'),
    'PORT': '',
    'CONN_MAX_AGE': 300,
}

REDIS = {
    'tasks': {
        'HOST': os.environ.get('NETBOX_REDIS_HOST', 'localhost'),
        'PORT': 6379,
        'USERNAME': '',
        'PASSWORD': '',
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'HOST': os.environ.get('NETBOX_REDIS_CACHE_HOST', 'localhost'),
        'PORT': 6380,
        'USERNAME': '',
        'PASSWORD': '',
        'DATABASE': 1,
        'SSL': False,
    },
}

# Development only: this instance is never exposed
SECRET_KEY = 'netbox-plugin-development-only-secret-key-0123456789abcdef'

DEBUG = True
DEVELOPER = True

PLUGINS = [os.environ['PLUGIN_MODULE']]
