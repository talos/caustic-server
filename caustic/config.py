'''
Configuration dict for caustic.
'''

config = {
    'mercurial_dir' : 'templates',
    'mongo_host'    : 'localhost',
    'mongo_port'    : 27017,

    'default_commit_message' : 'commit',

    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
}
