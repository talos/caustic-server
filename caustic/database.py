'''Set up database.
'''

from pymongo import Connection

connection = Connection('localhost', 27017)
db         = connection.caustic
collection = db.instructions
