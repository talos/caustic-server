#!/usr/bin/env python

'''
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
'''

import sys
import json
from brubeck.request_handling import Brubeck, WebMessageHandler
from database import templates, users

#import migrations # temporary
from validation import validate # not the best?

from config     import config
from exceptions import HandleCausticExceptionsMixin, NoTemplateException
from mercurial  import Repository
from models     import Template, User

class IsAliveHandler(WebMessageHandler):
    ''' This handler provides ping-like functionality, letting clients know
    whether the server is available.
    '''
    def head(self):
        self.set_status(200)
        return self.render()

class NameHandler(WebMessageHandler, HandleCausticExceptionsMixin):
    ''' This handler provides clients access to a single template by name.
    '''
    def get(self, user, name):
        ''' Get the JSON of a single template.
        '''

        template = find_template(user, name)
        self.set_body(template.json)

        return self.render()

    def put(self, user, name):
        ''' Update a single template.
        '''

        validate(self, user)

        user = users.find_one({'name' : user})
        tags = json.loads(self.get_argument('tags')) # load json array
        json = self.get_argument('json') # leave json template as string

        template = __find_template(user, name)

        # Existing template.  Modify it.
        if(template):
            template.tags = tags
            template.json = json
            verb = 'Updated'
        else:
            Template({'json': json, 'tags': tags, 'user': user })
            verb = 'Created'

        repo = Repository(config.mercurial_dir, template._id)
        repo.commit(json)

        self.set_body("%s template %s/%s" % verb, user, name)
        self.render()

    def delete(self, user, name):
        ''' Hide a single template from view.  Does not actually wipe the
        repo, but sets a 'hidden' flag in the database.
        '''

        validate(self, user)
        template = __get_visible_template(user, name)
        template.hidden = True
        templates.save(template)

        self.set_body("Deleted %s/%s" % user, name)
        self.render()

    def __find_template(self, user, name):
        ''' Find a single template by user and name.  Returns null if the
        template does not exist.  Returns templates even if they are hidden.
        '''
        return Template(**templates.find_one({ 'user' : user, 'name' : name }))

    def __get_visible_template(self, user, name):
        ''' Find a single template by user and name.  Throws an exception if
        not found, or if the template is hidden.
        '''

        if(template):
            if(template.hidden is False):
                return template

        raise NoTemplateException(user, name)

class TagHandler(WebMessageHandler, HandleCausticExceptionsMixin):
    ''' This handler provides clients an array of templates by tag.
    '''
    def get(self, user, tag):
        tagged_templatess = templates.find({'tags': tag})

        if tagged_templates.count() is 0:
            self.set_body("No templates with tag '%s'" % tag,
                          status_code=404)
        else:
            json = '[' + ','.join([
                    Template(**template).json
                    for template in tagged_templates]) + ']'
            self.set_body(json)

        return self.render()

urls = [
    (r'^/$', IsAliveHandler),
    (r'^/(?P<user>[\w\-]+)/(?P<name>[\w\-]+)+$', NameHandler),
    (r'^/(?P<user>[\w\-]+)/(?P<tag>[\w\-]+)/$',  TagHandler)]

config = {
    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
    'handler_tuples': urls,
}
app = Brubeck(**config)
app.run()
