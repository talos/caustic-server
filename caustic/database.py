'''Set up database.
'''

from config  import config
from pymongo import Connection

connection = Connection(config['mongo_host'], config['mongo_port'])
db         = connection.caustic

templates = db.templates
users     = db.users
