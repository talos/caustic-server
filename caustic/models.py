from dictshield.document import Document, EmbeddedDocument

# Depends which version of Dictshield we have.
try:
    from dictshield.fields.base     import StringField, BooleanField
    from dictshield.fields.compound import ListField, EmbeddedDocumentField
except ImportError:
    from dictshield.fields import StringField, \
                                  BooleanField, \
                                  EmbeddedDocumentField, \
                                  ListField

class User(EmbeddedDocument):
    ''' A user who can clone, make push requests, and pull
    instructions.
    '''

    name = StringField(required = True, uniq_field = True)

class Template(Document):
    ''' A template with a name and tags that belongs to a
    a single user.  It is backed with a mercurial repo,
    corresponding to the internal DB id.
    '''

    user = EmbeddedDocumentField(User, required = True )
    name = StringField(required = True, uniq_field = True)
    tags = ListField(StringField())

    private = BooleanField(default = False)
    hidden  = BooleanField(default = False)

    # This is the most recent commit to the mercurial repo
    json = StringField(required = True)

    _private_fields = [ private, hidden ]
