#!/usr/bin/env python

"""
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
"""

import json
import logging
import bson
from brubeck.request_handling import Brubeck, WebMessageHandler
from brubeck.auth import authenticated, UserHandlingMixin

from templating import MustacheRendering
from config     import config
from mercurial  import Repository
from models     import Instruction, User

#
# MIXINS
#
class UserMixin(UserHandlingMixin):
    """
    Use this mixin to leverage Brubeck's UserHandlingMixin.  Also
    provides methods to get and persist users.
    """

    def get_current_user(self):
        """
        Return the User DictShield model from the database using
        cookie session.  Returns `None` if there is no current user.
        """
        id = self.get_cookie('session', None, self.application.cookie_secret)
        return User(**self.db_conn.users.find_one(id=id))

    def set_current_user(self, user):
        """
        Set the cookie that will be used for session management.
        `user` is a User.
        """
        self.set_cookie('session', user.id, self.application.cookie_secret)

    def logout_user(self):
        """
        Log out the current user.  Returns None
        """
        self.delete_cookie('session')


class InstructionMixin():
    """
    Use this mixin with to get and persist instructions to the database.
    """

    def get_instruction(self, owner, name):
        """
        Get the instruction for `owner`, a User,  and `name`, a strings.
        Returns the Instruction if it exists, None otherwise.
        """
        instruction = self.db_conn.instruction.find_one({
                'owner.id': owner.id,
                'name': name,
                'deleted': False })
        return Instruction(**instruction) if instruction else None

    def get_tagged_instruction_names(self, owner, tag):
        """
        Get all instructions for `owner`, a User, with
        the tag String `tag`.  Returns an array of instructions,
        of 0 length if there were none for `tag` in `owner`.
        """
        instructions = self.db_conn.templates.find({
                    'owner.id': owner.id,
                    'tags': tag,
                    'deleted': False})
        return [Instruction(**instruction) for instruction in instructions]

    def get_repo(self, instruction):
        """
        Return the mercurial repo for the Instruction `instruction`.
        Will create this repo if it doesn't already exist.
        """
        return Repository(config['mercurial_dir'],
                          str(instruction.owner.id),
                          str(instruction.id))


class JsonMixin():
    """
    Use this mixin to repurpose handlers for both JSON and non-JSON responses.
    """

    def is_json_request(self):
        """
        Returns True if this was a request for JSON, False otherwise.
        """
        return self.message.headers['Accept'] == 'application/json'

#
# HANDLERS
#
class IsAliveHandler(WebMessageHandler):
    """
    This handler provides ping-like functionality, letting clients
    know whether the server is available.
    """
    def trace(self):
        return self.render(status_code=204)


class SignupHandler(MustacheRendering, UserMixin, JsonMixin):
    """
    This handler lets users sign up.  Takes argument `user`.  The
    user is logged in after signing up.
    """

    def post(self):
        logging.warn('Signup not yet implemented.')
        context = {}

        if self.current_user:
            context['error'] = 'You are already signed up.'
            status = 400 
        else:
            user = self.get_argument('user')

            if not user:
                context['error'] = 'You must specify user name to sign up'
                status = 400
            elif self.get_user(user):
                context['error'] = 'User name %s is already in use.' % user
                status = 400
            else:
                self.save_user(user)
                self.set_current_user(user)
                context['user'] = user
                status = 200

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('signup', _status_code=204, **context)


class DeleteAccountHandler(MustacheRendering, UserMixin):
    """
    This handler lets a user delete his/her account.  This does not delete
    their instructions, but will orphan them.
    """

    def post(self):
        context = {}
        if not self.current_user:
            context['error'] = 'You are not signed in.'
            status = 401
        else:
            token = self.get_argument('token')
                
            if token:
                self.delete_user(self.current_user)
                return self.render(status_code=204)

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('signup', _status_code=204, **context)
            


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


config['handler_tuples'] = [
    (r'^/$', IsAliveHandler),
    (r'^/signup$', SignupHandler),
    (r'^/die$', DeleteAccountHandler),
    (r'^/login$', LoginHandler),
    (r'^/logout$', LogoutHandler),
    (r'^/([\w\-]+)/tagged/([\w\-]+)/?$', TagIndexHandler),
    (r'^/([\w\-]+)/instructions/?$', InstructionCollectionHandler),
    (r'^/([\w\-]+)/instructions/([\w\-]+)/?$', InstructionModelHandler),
    (r'^/([\w\-]+)/instructions/([\w\-]+)/tag/([\w\-]+)/?$', InstructionTagHandler)]


app = Brubeck(**config)
app.run()
