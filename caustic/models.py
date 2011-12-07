from dictshield.document import Document, EmbeddedDocument

# Depends which version of Dictshield we have.
# try:
#     from dictshield.fields.base     import StringField, BooleanField
#     from dictshield.fields.compound import ListField
# except ImportError:
#     from dictshield.fields import StringField, \
#                                   BooleanField, \
#                                   ListField

from dictshield.fields.base import StringField, BooleanField
from dictshield.fields.compound import ListField
#from dictshield.fields.mongo import ObjectIdField

class User(Document):
    ''' A user who can clone, make push requests, and pull
    instructions.
    '''

    name = StringField(required=True, id_field=True)

class Template(Document):
    ''' A template with a name and tags that belongs to a
    a single user.  It is backed with a mercurial repo,
    corresponding to the internal DB id.
    '''

    owner = StringField(required=True)
    name = StringField(required=True)
    tags = ListField(StringField())

    private = BooleanField(default=False)
    hidden  = BooleanField(default=False)

    # This is the most recent commit to the mercurial repo
    json = StringField(required=True)

    _private_fields = [ private, hidden ]
