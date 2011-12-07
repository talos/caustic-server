#!/usr/bin/env python

"""
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
"""

import sys
import json
from brubeck.request_handling import Brubeck, WebMessageHandler
from brubeck.auth import authenticated, UserHandlingMixin

from config    import config
from mercurial import Repository
from models    import Template, User

class UserMixin(UserHandlingMixin):
    """Use this mixin to leverage Brubeck's UserHandlingMixin.  Returns `None`
    if there is no user.
    """

    def get_current_user(self):
        """Return the user object from the database using cookie session.
        Returns `None` if there is no current user.
        """
        user_name = self.get_cookie(config['session_cookie_name'],
                             secret=self.application.cookie_secret)

        return User(**self.db_conn.users.find_one(user_name)) if user_name else None

    def set_current_user(self, user):
        """Set the cookie that will be used for session management.
        `user` is a User DictShield object.
        """
        self.set_cookie(config['session_cookie_name'],
                        user.name,
                        secret=self.application.cookie_secret)

    def logout_user(self):
        """Log out the current user.
        """
        self.delete_cookie(config['session_cookie_name'])


class IsAliveHandler(WebMessageHandler):
    """This handler provides ping-like functionality, letting clients know
    whether the server is available.
    """
    def head(self):
        return self.render(status_code=204)


class SignUpHandler(WebMessageHandler, UserMixin):
    """This handler lets users sign up.  Takes argument `user`.  The user is
    logged in after signing up.
    """

    def post(self):
        print "Warning: signup not yet implemented."

        if self.current_user:
            self.set_body('You cannot be logged in to sign up.')
            return self.render(status_code=400)

        user_name = self.get_argument('user')

        if not user_name:
            self.set_body('You must specify user name to sign up')
            return self.render(status_code=400)

        if self.db_conn.users.find_one({'name': user_name}):
            self.set_body('User name %s is already in use.' % user_name)
            return self.render(status_code=400)

        user = User(name=user_name)
        self.db_conn.users.save(user.to_python())

        self.set_current_user(user)
        return self.render(status_code=204)


class DeleteAccountHandler(WebMessageHandler, UserMixin):
    """This handler lets a user delete his/her account.  This does not delete
    their templates, but will orphan them.
    """

    @authenticated
    def post(self):
        self.db_conn.users.remove(self.current_user.name)


class LogInHandler(WebMessageHandler, UserMixin):
    """This handler lets users log in.
    """

    def post(self):
        print "Warning: login not yet implemented."

        if self.current_user:
            self.set_body('You are already logged in as %s'
                          % self.current_user.name)
            return self.render(status_code=400)

        user_name = self.get_argument('user')
        if not user_name:
            self.set_body('User not specified')
            return self.render(status_code=400)

        user = self.db_conn.users.find_one({'name': user_name})
        if not user:
            self.set_body('User %s does not exist' % user_name)
            return self.render(status_code=400)

        self.set_current_user(user)
        return self.render(status_code=204)


class LogOutHandler(WebMessageHandler, UserMixin):
    """This handler lets users log out.
    """

    @authenticated
    def post(self):
        self.logout_user()
        return self.render(status_code=204)


class NameHandler(WebMessageHandler, UserMixin):
    """This handler provides clients access to a single template by name.
    """

    def get(self, owner_name, name):
        """Get the JSON of a single template.
        """

        # owner = self.db_conn.users.find_one({'name': owner_name})
        # if not owner:
        #     self.set_body('No user %s' % owner_name)
        #     return self.render(status_code=404)

        template = self.db_conn.templates.find_one({
                'owner': owner_name,
                'name': name,
                'hidden': False})
        if template:
            self.set_body(template.json)
            return self.render(status_code=200)
        else:
            self.set_body('No template')
            return self.render(status_code=404)

    @authenticated
    def put(self, owner_name, name):
        """Update a single template, creating it if it doesn't exist.
        """

        if not owner_name == self.current_user.name:
            self.set_body( 'This is not your template.')
            return self.render(status_code=400)

        tags = json.loads(self.get_argument('tags', '[]')) # load json array
        json_template = self.get_argument('json') # leave json template as string
        commit = self.get_argument('commit', config['default_commit'])

        if json_template:
            template = self.db_conn.templates.find_one({
                    'owner': self.current_user.name, 'name': name
                    })
        if template: # modify existing template
            template.tags = tags
            template.json = json_template
        else: # new template
            template = Template(tags=tags,
                                json=json_template,
                                owner=self.current_user.name)

        self.db_conn.templates.save(template.to_python())

        # This will create the repo if it doesn't already exist.
        repo = Repository(config['mercurial_dir'],
                          self.current_user.name,
                          str(template.id))
        repo.commit(json_template, commit)
        return self.render(status_code=204)

    @authenticated
    def delete(self, owner_name, name):
        """Hide a single template from view.  Does not actually wipe the
        repo, but sets a 'hidden' flag for the template.
        """

        if not owner_name is self.current_user.name:
            self.set_body('You cannot delete someone else\'s template')
            return self.render(status_code=400)

        template = Template(**self.db_conn.templates.find_one({
                'owner': self.current_user.name,
                'name': name}))
        if not template:
            self.set_body('No template')
            return self.render(status_code=404)

        template.hidden = True
        self.db_conn.templates.save(template.to_python())

        return self.render(status_code=204)


class TagHandler(WebMessageHandler):
    """This handler provides clients an array of templates by tag.
    """
    def get(self, owner_name, tag):
        owner = self.db_conn.users.find_one({'name': owner_name})
        if not owner:
            self.set_body('User %s does not exist.' % owner_name)
            return self.render(status_code=404)

        tagged_templates = self.db_conn.templates.find(
            {'owner': owner.name, 'tags': tag})

        if tagged_templates: # TODO pymongo len() doesn't work
            self.set_body(json.dumps([
                Template(**template).json for template in tagged_templates
                ]))
            return self.render(status_code=200)
        else:
            self.set_body('User %s has no templates with tag "%s"'
                          % (user, tag))
            return self.render(status_code=404)


urls = [
    (r'^/$', IsAliveHandler),
    (r'^/signup$', SignUpHandler),
    (r'^/die$', DeleteAccountHandler),
    (config['login_url'], LogInHandler),
    (r'^/logout', LogOutHandler),
    (r'^/(?P<owner_name>[\w\-]+)/(?P<name>[\w\-]+)$', NameHandler),
    (r'^/(?P<owner_name>[\w\-]+)/(?P<tag>[\w\-]+)/$',  TagHandler)]

# Add handler tuples to the imported config.
config['handler_tuples'] = urls

app = Brubeck(**config)
app.run()
