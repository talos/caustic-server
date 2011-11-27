from dictshield.document import Document

# Depends which version of Dictshield we have.
try:
    from dictshield.fields.base     import StringField
    from dictshield.fields.compound import ListField
except ImportError:
    from dictshield.fields import StringField, ListField

class Instruction(Document):
    name = StringField(required = True)
    tags = ListField(StringField())
    json = StringField(required = True)

# class Instruction(EmbeddedDocument):
#     name        = StringField()
#     tags        = ListField(StringField())
#     description = StringField()
#     then        = ListField(EmbeddedDocumentField(Instruction))


# class Load(Instruction):
#     load   = StringField() # substitutions mean invalid URLs must be
#                            # acceptable (they could be substituted into valid
#                            # urls)
#     method  = StringField()
#     posts   = DictField()
#     headers = DictField()
#     cookies = DictField()

# class Find(Instruction, RecursiveMixin):
#     find             = StringField()
#     case_insensitive = BooleanField()
#     multiline        = BooleanField()
#     dot_matches_all  = BooleanField()
#     replace          = BooleanField()
#     match            = IntField()
#     min              = IntField()
#     max              = IntField()
