#!/usr/bin/env python

import sys
from brubeck.request_handling import Brubeck, WebMessageHandler
from database import collection
import migrations # temporary
from models import Instruction

class IsAliveHandler(WebMessageHandler):
    ''' This handler provides ping-like functionality, letting clients know
    whether the server is available.
    '''
    def head(self):
        self.set_status(200)
        return self.render()

class NameHandler(WebMessageHandler):
    ''' This handler provides clients a single instruction by name.
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
    ''' This handler provides clients an array of instructions by tag.
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
    (r'^/$', IsAliveHandler),
    (r'^/(?P<name>[\w\s\-]+)+$', NameHandler),
    (r'^/(?P<tag>[\w\s\-]+)/$',  TagHandler)]

config = {
    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
    'handler_tuples': urls,
}
app = Brubeck(**config)
app.run()
