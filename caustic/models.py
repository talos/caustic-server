import validictory

import schema

from dictshield.document import Document
from dictshield.base import ShieldException
from dictshield.fields.base import StringField, BooleanField, DictField
from dictshield.fields.mongo import ObjectIdField

class InstructionsField(DictField):
    """
    A dict of Instructions where each key is a valid name, and each
    value is an Instruction.
    """

    def validate(self, _dict):
        """
        Validate each value is an Instruction, and each key is a string.
        """
        super(DictField, self).validate(_dict)
        for key, value in _dict.items():
            if not isinstance(key, basestring):
                raise ShieldException("Invalid key: %s" % key, 'instructions', _dict)
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


class User(Document):
    """
    A user who can clone, make push requests, and pull
    instructions.
    """
    id = ObjectIdField(id_field=True)
    name = StringField(required=True)
    delete_token = StringField()
    deleted = BooleanField(default=False)
    instructions = InstructionsField()

    _private_fields = [deleted]
