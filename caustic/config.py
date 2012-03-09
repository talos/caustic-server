'''
Configuration dict for caustic.
'''

import uuid
import pymongo
from brubeck.templating import load_mustache_env

config = {
    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
    'db_conn'  : pymongo.Connection('localhost', 27017).caustic,
    'cookie_secret': str(uuid.uuid4()),
    'template_loader': load_mustache_env('./templates'),
    'git_dir': 'git'
}
