#!/usr/bin/env python

'''
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
'''

import sys
import json
from brubeck.request_handling import Brubeck, WebMessageHandler

from database   import templates, users
from validation import validate # not the best?
from config     import config
#from exceptions import CausticException, NoTemplateException
from mercurial  import Repository
from models     import Template, User

class HandleCausticExceptionsMixin():
    ''' Use this mixin with WebMessageHandler to render caustic exceptions
    correctly.
    '''

    def error(self, e):

        if isinstance(e, CausticException):
            self.set_status(e.code)
            self.render(e.message)
        else:
            # TODO it would be better if we in this case hit the error(self, e)
            # method of the mixed-in class.
            self.unsupported()

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
        tags = json.loads(self.get_argument('tags'), '[]') # load json array
        template_json = self.get_argument('json') # leave json template as string
        if self.get_argument('commit') is None:
            commit = config['default_commit_message']
        else:
            commit = self.get_argument('commit')

        template = _find_template(user, name)

        # Existing template.  Modify it.
        if(template):
            template.tags = tags
            template.json = template_json
            verb = 'Updated'
        else:
            Template({'json': template_json, 'tags': tags, 'user': user })
            verb = 'Created'

        repo = Repository(config['mercurial_dir'], user.name, template.name)
        repo.commit(json, 'Commit')

        self.set_body("%s template %s/%s" % verb, user.name, name)
        self.render()

    def delete(self, user, name):
        ''' Hide a single template from view.  Does not actually wipe the
        repo, but sets a 'hidden' flag in the database.
        '''

        validate(self, user)
        template = _get_visible_template(user, name)
        template.hidden = True
        templates.save(template)

        self.set_body("Deleted %s/%s" % user, name)
        self.render()

    def _find_template(self, user, name):
        ''' Find a single template by user and name.  Returns null if the
        template does not exist.  Returns templates even if they are hidden.
        '''
        return Template(**templates.find_one({ 'user' : user, 'name' : name }))

    def _get_visible_template(self, user, name):
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
config['handler_tuples'] = urls

app = Brubeck(**config)
app.run()
