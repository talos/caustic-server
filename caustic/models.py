from dictshield.document import Document, EmbeddedDocument, diff_id_field

from dictshield.fields.base import StringField, BooleanField
from dictshield.fields.compound import ListField, EmbeddedDocumentField
from dictshield.fields.mongo import ObjectIdField

@diff_id_field(ObjectIdField, ['id'])
class User(EmbeddedDocument):
    ''' A user who can clone, make push requests, and pull
    instructions.
    '''

    #id = ObjectIdField(id_field=True)
    name = StringField(required=True)
    deleted = BooleanField(default=False)

    _private_fields = [deleted]


@diff_id_field(ObjectIdField, ['id'])
class Template(Document):
    ''' A template with a name and tags that belongs to a
    a single user.  It is backed with a mercurial repo,
    corresponding to the internal DB id.
    '''

    #id = ObjectIdField(id_field=True)
    #owner_id = ObjectIdField(required=True)
    owner = EmbeddedDocumentField(User, required=True)
    name = StringField(required=True)
    tags = ListField(StringField())

    private = BooleanField(default=False)
    deleted = BooleanField(default=False)

    # This is the most recent commit to the mercurial repo
    json = StringField(required=True)

    _private_fields = [private, deleted]
