#!/usr/bin/env python

"""
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
"""

import sys
import json
import uuid
from brubeck.request_handling import Brubeck, WebMessageHandler
from brubeck.auth import web_authenticated, UserHandlingMixin

from database   import templates, users
from mercurial  import Repository
from models     import Template, User


class HandleCausticUserMixin(UserHandlingMixin):
    """Use this mixin to leverage Brubeck's UserHandlingMixin.  Returns `None`
    if there is no user.
    """

    def get_current_user(self):
        """Return the user object from the database using cookie session.
        """
        user_id = get_cookie('session', secret=self.application.secret)

        if not user_name:
            return None
            #raise BadSessionException()

        return User.find_one(user_id)


class IsAliveHandler(WebMessageHandler):
    """This handler provides ping-like functionality, letting clients know
    whether the server is available.
    """
    def head(self):
        self.set_status(200)
        return self.render()


class SignUpHandler(WebMessageHandler, HandleCausticExceptionsMixin):
    """This handler lets users sign up.  Takes argument `user`.  The user is
    logged in after signing up.
    """

    def post(self):
        print "Warning: signup not yet implemented."

        user_name = self.get_argument('user')

        if not self.get_argument('user'):
            return self.render_error(400, 'Must specify user name to sign up')

        if users.find_one({'name': user_name}).count():
            return self.render_error(400,
                                     "User name %s is already in use."
                                     % user_name)

        user = User(name=user_name)
        users.save(user.to_python())

        self.set_cookie('session', user._id, )
        return self.render()


class DeleteAccountHandler(WebMessageHandler, HandleCausticExceptionsMixin):
    """This handler lets a user delete his/her account.  This does not delete
    their templates, but will orphan them.
    """

    @authenticated
    def post(self):
        users.remove(self.current_user._id)


class LogInHandler(WebMessageHandler, HandleCausticExceptionsMixin):
    """This handler lets users log in.
    """

    def post(self):
        print "Warning: login not yet implemented."

        user_name = self.get_argument('user')
        if user_name:
            user = users.find_one({'name': user_name})
            if user:
                self.set_cookie('session', user._id,
                                secret=self.application.secret)
                self.render()
            else:
                self.render_error(400, "User %s does not exist" % user_name)
        else:
            self.render_error(400, "User not specified")


class LogOutHandler(WebMessageHandler):
    """This handler lets users log out.
    """

    @authenticated
    def post(self):
        self.delete_cookie('session')


class NameHandler(WebMessageHandler,
                  HandleCausticExceptionsMixin,
                  UserHandlingMixin):
    """This handler provides clients access to a single template by name.
    """

    def get(self, user, name):
        """Get the JSON of a single template.
        """

        user_id = users.find_one({'name': user})
        template = templates.find_one({
                'user_id': user_id,
                'name': name,
                'hidden': False})
        if template:
            self.set_body(template.json)
            return self.render()
        else:
            return self.render_error(404, "No template")

    @authenticated
    def put(self, user, name):
        """Update a single template, creating it if it doesn't exist.
        """

        if not user is self.current_user:
            return self.render_error(400, "You cannot modify someone else's"
                                          "template.")

        tags = json.loads(self.get_argument('tags'), '[]') # load json array
        json = self.get_argument('json') # leave json template as string
        commit = self.get_argument('commit', self.application.default_commit)

        if json:
            template = templates.find_one({
                    'user_id': self.current_user._id, 'name': name
                    })
        if template: # modify existing template
            template.tags = tags
            template.json = json
        else: # new template
            template = Template(tags=tags,
                                json=json,
                                user_id=self.current_user._id)

        templates.save(template.to_python())

        repo = Repository(self.application.mercurial_dir,
                          self.current_user.name,
                          template.name)
        repo.commit(json, commit)
        return self.render()

    @authenticated
    def delete(self, user, name):
        """Hide a single template from view.  Does not actually wipe the
        repo, but sets a 'hidden' flag for the template.
        """

        if not user is self.current_user:
            return self.render_error(400, "You cannot delete someone else's"
                                     " template")

        template = Template(**templates.find_one({
                'user_id': self.current_user._id,
                'name': name}))
        if not template:
            return self.render_error(404, "No template")

        template.hidden = True
        templates.save(template.to_python())

        self.set_body("Deleted %s/%s" % (self.current_user, name))
        self.render()


class TagHandler(WebMessageHandler, HandleCausticExceptionsMixin):
    """This handler provides clients an array of templates by tag.
    """
    def get(self, user, tag):
        tagged_templates = templates.find({'tags': tag})

        if tagged_templates.count(): # TODO len() doesn't work
            json = '[' + ','.join([
                    Template(**template).json
                    for template in tagged_templates]) + ']'
            self.set_body(json)
            return self.render()
        else:
            return self.render_error(404,
                                     "User %s has no templates with tag '%s'"
                                     % (user, tag))

config = {
    'secret': str(uuid.uuid4()), # A secret set for encoing cookies at
                                 # runtime.
    'login_url': r'^/login',
    'default_commit': 'committed',
    'mercurial_dir': 'templates'
}

urls = [
    (r'^/$', IsAliveHandler),
    (r'^/signup$', SignUpHandler),
    (r'^/die$', DeleteAccountHandler),
    (config['login_url'], LogInHandler),
    (r'^/logout', LogOutHandler),
    (r'^/(?P<user>[\w\-]+)/(?P<name>[\w\-]+)$', NameHandler),
    (r'^/(?P<user>[\w\-]+)/(?P<tag>[\w\-]+)/$',  TagHandler)]
config['handler_tuples'] = urls

app = Brubeck(**config)
app.run()
