from dictshield.document        import Document
from dictshield.fields.base     import StringField
from dictshield.fields.compound import ListField

class Instruction(Document):
    name = StringField()
    tags = ListField(StringField())
    json = StringField()

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
