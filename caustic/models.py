import validictory

import schema

from dictshield.document import Document, EmbeddedDocument
from dictshield.base import ShieldException
from dictshield.fields.base import StringField, BooleanField, DictField
from dictshield.fields.compound import ListField, EmbeddedDocumentField
from dictshield.fields.mongo import ObjectIdField

class User(EmbeddedDocument):
    """
    A user who can clone, make push requests, and pull
    instructions.
    """
    id = ObjectIdField(id_field=True)
    name = StringField(required=True)
    delete_token = StringField()
    deleted = BooleanField(default=False)

    _private_fields = [deleted]


class InstructionField(DictField):
    """
    The raw contents of an instruction, independent of its name or tags in
    the database.
    """

    def validate(self, value):
        """
        Validate the instruction with validictory.
        """
        super(DictField, self).validate(value) 
        try:
            validictory.validate(value, schema.INSTRUCTION)
        except ValueError as instruction_err:
            errors = []
            # We don't know which schema it failed against, if it wasn't within
            # a 'then' block we may be able to be more specific.
            try:
                validictory.validate(value, schema.FIND)
            except ValueError as find_err:
                errors.append(find_err)

            try:
                validictory.validate(value, schema.LOAD)
            except ValueError as load_err:
                errors.append(load_err)

            if not errors:
                errors = [instruction_err]

            raise ShieldException("Invalid Instruction: %s" % errors,
                                  'instruction', value)

class Instruction(Document):
    """
    A instruction with a name and tags that belongs to a
    a single user.  It is backed with a Repository,
    corresponding to the internal DB id.
    """
    id = ObjectIdField(id_field=True)
    owner = EmbeddedDocumentField(User, required=True)
    name = StringField(required=True)
    tags = ListField(StringField())

    private = BooleanField(default=False)
    deleted = BooleanField(default=False)

    # This is the most recent commit to the repo
    instruction = InstructionField(required=True)

    _private_fields = [private, deleted]
