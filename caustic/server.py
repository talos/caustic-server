#!/usr/bin/env python

"""
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
"""

import sys
import json
import logging
import bson
from brubeck.request_handling import Brubeck, WebMessageHandler
from brubeck.auth import authenticated, UserHandlingMixin

from config    import config
from mercurial import Repository
from models    import Template, User


class UserMixin(UserHandlingMixin):
    """Use this mixin to leverage Brubeck's UserHandlingMixin.  Also
    provides methods to get and persist users.
    """

    def get_user(self, user_name):
        """Returns the DictShield User object from the database
        corresponding to the String `user_name`, or None if there is
        no user with the specified `user_name`.  Will also return None
        if the passed `user_name` is None.
        """
        user = self.db_conn.users.find_one({
                'name': user_name,
                'deleted': False})
        return User(**user) if user else None

    def get_current_user(self):
        """Return the User DictShield object from the database using
        cookie session.  Returns `None` if there is no current user.
        """
        user_id = self.get_cookie(config['session_cookie_name'],
                                  None,
                                  self.application.cookie_secret)
        user = self.db_conn.users.find_one(bson.ObjectId(user_id)) if user_id else None

        return User(**user) if user else None

    def set_current_user(self, user):
        """Set the cookie that will be used for session management.
        `user` is a User DictShield object. Returns None.
        """
        self.set_cookie(config['session_cookie_name'],
                        unicode(user.id),
                        self.application.cookie_secret)
        return None

    def logout_user(self):
        """Log out the current user.  Returns None
        """
        self.delete_cookie(config['session_cookie_name'])
        return None

    def persist_user(self, user):
        """Persist `user`, a DictShield User.  Returns None.
        """
        # update the DictShield User in-place
        user.id = self.db_conn.users.save(user.to_python())
        return None

    def delete_user(self, user):
        """Delete `user`, a DictShield User, by setting their
        'deleted' flag to True. Returns None.
        """
        user.deleted = True
        self.db_conn.users.save(user.to_python())
        return None


class TemplateMixin():
    """Use this mixin with WebMessageHandler to get and persist
    templates to the database.
    """

    def get_template(self, owner, name):
        """Get the template for `owner`, a DictShield User, and
        `name`, a String.  Returns a DictShield Template if the
        template exists, None otherwise.
        """
        template = self.db_conn.templates.find_one({
                'owner.id': owner.id,
                'name': name,
                'deleted': False})
        return Template(**template) if template else None

    def get_tagged_templates(self, owner, tag):
        """Get all templates for `owner`, a DictShield User, with
        the tag String `tag`.  Returns an array of DictShield Templates,
        of 0 length if there were none for `tag` in `owner`.
        """
        return [Template(**template)
                for template in self.db_conn.templates.find({
                    'owner.id': owner.id,
                    'tags': tag,
                    'deleted': False})]

    def get_repo(self, template):
        """Return the mercurial repo for the DictShield template `template`.
        Will create this repo if it doesn't already exist.
        """
        return Repository(config['mercurial_dir'],
                          str(template.owner.id),
                          str(template.id))


    def persist_template(self, template):
        """Persist the DictShield `template` to the DB.  returns None.
        """
        # modify template in-place
        template.id = self.db_conn.templates.save(template.to_python())
        return None


class IsAliveHandler(WebMessageHandler):
    """This handler provides ping-like functionality, letting clients
    know whether the server is available.
    """
    def head(self):
        return self.render(status_code=204)


class SignUpHandler(WebMessageHandler, UserMixin):
    """This handler lets users sign up.  Takes argument `user`.  The
    user is logged in after signing up.
    """

    def post(self):
        logging.warn('Signup not yet implemented.')

        if self.current_user:
            self.set_body('You cannot be logged in to sign up.')
            return self.render(status_code=400)

        user_name = self.get_argument('user')

        if not user_name:
            self.set_body('You must specify user name to sign up')
            return self.render(status_code=400)

        if self.get_user(user_name):
            self.set_body('User name %s is already in use.' % user_name)
            return self.render(status_code=400)

        user = User(name=user_name)
        self.persist_user(user)

        self.set_current_user(user)
        return self.render(status_code=204)


class DeleteAccountHandler(WebMessageHandler, UserMixin):
    """This handler lets a user delete his/her account.  This does not delete
    their templates, but will orphan them.
    """

    @authenticated
    def post(self):
        self.delete_user(self.current_user)
        return self.render(status_code=204)


class LogInHandler(WebMessageHandler, UserMixin):
    """This handler lets users log in.
    """

    def post(self):
        logging.warn('Login not yet implemented.')

        if self.current_user:
            self.set_body('You are already logged in as %s'
                          % self.current_user.name)
            return self.render(status_code=400)

        user = self.get_user(self.get_argument('user'))
        if not user:
            self.set_body('User does not exist')
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


class NameHandler(WebMessageHandler, UserMixin, TemplateMixin):
    """This handler provides clients access to a single template by name.
    """

    def get(self, owner_name, name):
        """Get the JSON of a single template.
        """

        owner = self.get_user(owner_name)
        if not owner:
            self.set_body('No user %s' % owner_name)
            return self.render(status_code=404)

        template = self.get_template(owner, name)
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

        json_template = self.get_argument('json') # leave json
                                                  # template as string
        if not json_template:
            self.set_body('You must specify json for the template.')
            return self.render(status_code=400)
        #TODO validation for template.

        tags = json.loads(self.get_argument('tags', '[]')) # load json array
        commit = self.get_argument('commit', config['default_commit'])

        template = self.get_template(self.current_user, name)
        if template: # modify existing template
            template.tags = tags
            template.json = json_template
        else: # new template
            template = Template(
                name=name,
                tags=tags,
                json=json_template,
                owner=current_user)

        self.persist_template(template)

        repo = self.get_repo(template)
        repo.commit(json_template, commit)

        return self.render(status_code=204)

    @authenticated
    def delete(self, owner_name, name):
        """Hide a single template from view.  Does not actually wipe the
        repo, but sets a 'deleted' flag for the template.
        """
        if not owner_name == self.current_user.name:
            self.set_body('You cannot delete someone else\'s template')
            return self.render(status_code=400)

        template = self.get_template(self.current_user, name)

        if not template:
            self.set_body('No template')
            return self.render(status_code=404)

        template.deleted = True
        self.persist_template(template)

        return self.render(status_code=204)


class CloneHandler(WebMessageHandler, UserMixin, TemplateMixin):
    """This handler clones an existing repo for the logged in user,
    with the same name.
    """
    @authenticated
    def post(self, owner_name, name):
        template = self.get_template(self.get_user(owner_name), name)
        if not template:
            self.set_body('Template %s/%s does not exist.' % (owner_name, name))
            return self.render(status_code=404)

        repo_to_clone = self.get_repo(template)

        template.id = None # Force mongo to create a new template.
        self.persist_template(template) # This assigns a new ID.

        repo_to_clone.clone(self.current_user.id, template.id)
        return self.render(status_code=204)


class PullHandler(WebMessageHandler, UserMixin, TemplateMixin):
    """This handler pulls one repo into another.
    """

    pass


class TagHandler(WebMessageHandler, UserMixin, TemplateMixin):
    """This handler serves an array of template links by tag.
    """
    def get(self, owner_name, tag):
        owner = self.get_user(owner_name)
        if not owner:
            self.set_body('User %s does not exist.' % owner_name)
            return self.render(status_code=404)

        tagged_templates = self.get_tagged_templates(owner, tag)

        self.set_body(json.dumps([
                    "../%s" % template.name for template in tagged_templates]))
        return self.render(status_code=200)


urls = [
    (r'^/$', IsAliveHandler),
    (r'^/signup$', SignUpHandler),
    (r'^/die$', DeleteAccountHandler),
    (config['login_url'], LogInHandler),
    (r'^/logout', LogOutHandler),
    (r'^/(?P<owner_name>[\w\-]+)/(?P<name>[\w\-]+)$', NameHandler),
    (r'^/(?P<owner_name>[\w\-]+)/(?P<name>[\w\-]+)/clone$',  CloneHandler),
    (r'^/(?P<owner_name>[\w\-]+)/(?P<name>[\w\-]+)/pull/(?P<from_owner_name>[\w\-]+)/(?P<from_name>[\w\-]+)$',  PullHandler),
    (r'^/(?P<owner_name>[\w\-]+)/tagged/(?P<tag>[\w\-]+)$',  TagHandler)]

# Add handler tuples to the imported config.
config['handler_tuples'] = urls

app = Brubeck(**config)
app.run()
