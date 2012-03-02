'''
Configuration dict for caustic.
'''

import uuid
import pymongo

config = {
    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
    'db_conn'  : pymongo.Connection('localhost', 27017).caustic,
    'cookie_secret': str(uuid.uuid4()), # A secret set for encoding
                                        # cookies at runtime.

    'default_commit': 'committed',
    'mercurial_dir' : 'templates'
}
