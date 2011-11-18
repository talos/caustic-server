#!/usr/bin/env python

import sys
from brubeck.request_handling import Brubeck, WebMessageHandler
from database import collection
import migrations # temporary
from models import Instruction

class NameHandler(WebMessageHandler):
    ''' This class handles interactions with a single instruction  by name.
    '''
    def get(self, name):
        instruction = collection.find_one({'name' : name})

        if instruction:
            self.set_body(Instruction(**instruction).json)
        else:
            self.set_body("Instruction %s does not exist" % name,
                          status_code=404)

        return self.render()

class TagHandler(WebMessageHandler):
    ''' This class handles the retrieval of instructions by tag.
    '''
    def get(self, tag):
        tagged_instructions = collection.find({'tags': tag})

        if tagged_instructions.count() is 0:
            self.set_body("No instructions with tag %s" % tag,
                          status_code=404)
        else:
            json = '[' + ','.join([
                    Instruction(**instruction).json
                    for instruction in tagged_instructions]) + ']'
            self.set_body(json)

        return self.render()

urls = [
        (r'^/(?P<name>\w+)+$', NameHandler),
        (r'^/(?P<tag>\w+)/$',  TagHandler)]

config = {
    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
    'handler_tuples': urls,
}
app = Brubeck(**config)
app.run()
