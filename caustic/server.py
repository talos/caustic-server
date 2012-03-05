#!/usr/bin/env python

"""
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
"""

import json
import logging
import uuid
from dictshield.base import ShieldException
from brubeck.request_handling import Brubeck
from brubeck.auth import UserHandlingMixin

from templating import MustacheRendering
from config     import config
from vcs        import Repository
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

    def _get_user(self, name):
        """
        Get the User document for a given name, or None if there is none.
        """
        user = self.db_conn.users.find_one({'name': name, 'deleted': False})
        return User(**user) if user else None

    def find_instructions(self, owner, deleted=False, **kwargs):
        """
        Get the non-deleted Instructions for user of name `owner` and optional
        additional kwargs. Returns None if the user doesn't exist, an empty
        list if the user has no instructions.
        """
        user = self._get_user(owner)
        if not user:
            return None 
        kwargs['owner.id'] = user.id
        kwargs['deleted'] = deleted
        instructions = self.db_conn.instructions.find(kwargs)
        return [Instruction(**instruction) for instruction in instructions]

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
class IndexHandler(MustacheRendering):
    def trace(self):
        """
        Trace provides ping-like functionality, letting clients
        know whether the server is available.
        """
        return self.render(status_code=204)

    def post(self):
        """
        Logging in and out.
        """
        action = self.get_argument('action')
        context = {}
        if action == 'signup':
            if self.current_user:
                context['error'] = 'You are already signed up.'
                status = 400 
            else:
                user = self.get_argument('user')

                if not user:
                    context['error'] = 'You must specify user name to sign up'
                    status = 400
                elif self.get_user(user):
                    context['error'] = "User name '%s' is already in use." % user
                    status = 400
                else:
                    self.save_user(user)
                    self.set_current_user(user)
                    context['user'] = user
                    status = 200
        elif action == 'login':
            logging.warn('Login not yet implemented.')

            if self.current_user:
                context['error'] = 'You are already logged in as %s' % self.current_user.name
                status = 403

            user = self.db_conn.find_one({'name': self.get_argument('user')})
            if user:
                self.set_current_user(User(**user))
                status = 200
            else:
                context['error'] = 'User does not exist'
                status = 403

        elif action == 'logout':
            self.logout_user()
            status = 200
        else:
            context['error'] = 'Invalid action'
            status = 400

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('user', _status_code=status, **context)


class UserHandler(MustacheRendering, UserMixin, JsonMixin):

    def delete(self, user):
        """
        This handler lets a user delete his/her account.  This does not delete
        instructions, but will orphan them.  S/he must match a deletion token.
        """
        context = {'user': user}
        if not self.current_user:
            context['error'] = 'You are not signed in.'
            status = 401
        else:
            user = self.current_user
            token = self.get_argument('token', str(uuid.uuid4()))

            if token == self.get_cookie('token', None, self.application.cookie_secret):
                self.delete_cookie('token')
                user.deleted = True
                self.db_conn.save(user.to_python())
                status = 204
            else:
                self.set_cookie('token', token, self.application.cookie_secret)
                context['token'] = token
                status = 204

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('user', _status_code=status, **context)
            
    def get(self, user):
        """
        Get the user's homepage.
        """
        return self.render_template('user', user=user)


class InstructionCollectionHandler(MustacheRendering, UserMixin, InstructionMixin, JsonMixin):
    """
    This handler provides access to all of a user's instructions.
    """

    def get(self, user):
        """
        Provide a listing of all this user's instructions.
        """
        context = { 'user': user }
        instructions = self.find_instructions(user)
        if instructions == None:
            context['error'] = "User %s does not exist." % user
            status = 404
        else:
            context['instructions'] = [i.instruction for i in instructions]
            status = 200

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('instruction_collection',
                                        _status_code=status,
                                        **context)

    def post(self, user):
        """
        Allow for cloning and creation.
        """
        context = {} 
        if user != self.current_user:
            context['error'] = 'You cannot modify these resources.'
            status = 403
        else:
            action = self.get_argument('action')
            if action == 'create': 
                name = self.get_argument('name')
                if self.create_instruction(user, name=name):
                    status = 303
                    self.headers['Location'] = name 
                else:
                    status = 409
                    context['error'] = "There is already an instruction with that name"
            elif action == 'clone': 
                owner = self.get_argument('owner')
                name = self.get_argument('name')
                if self.clone_instruction(owner, user, name):
                    status = 303
                    self.headers['Location'] = name 
                else:
                    status = 409
                    context['error'] = "Could not clone the instruction."
            else:
                context['error'] = 'Unknown action'
                status = 400

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('created', _status_code=status, **context)

class TagCollectionHandler(MustacheRendering, InstructionMixin, JsonMixin):
    """
    This handler provides access to all of a user's instructions with a certain
    tag.
    """
    def get(self, user, tag):
        instructions = self.find_instructions(user, tag=tag)
        if self.is_json_request():
            self.set_body(json.dumps([i.instruction for i in instructions]))
            return self.render()
        else:
            context = {
                'tag': tag,
                'user': user,
                'instructions': instructions
            }
            return self.render_template('tagged', **context)


class InstructionModelHandler(MustacheRendering, UserMixin, InstructionMixin, JsonMixin):
    """
    This handler provides clients access to a single instruction by name.
    """

    def get(self, user, name):
        """
        Display a single instruction.
        """
        context = {}
        instructions = self.find_instructions(user, name=name)
        if instructions:
            context['instruction'] = instructions[0].to_python()
            status = 200
        else:
            context['error'] = "Instruction does not exist"
            status = 404

        if self.is_json_request():
            # for JSON, only include the instruction proper
            self.set_body(json.dumps(instructions[0].instruction))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('instruction', _status_code=status, **context)

    def put(self, owner, name):
        """
        Update a single instruction, creating it if it doesn't exist.
        """
        user = self.current_user 
        context = {}
        if not user:
            context['error'] = "You are not logged in."    
            status = 403
        elif owner != user.name:
            context['error'] = 'This is not your template.'
            status = 403
        else:
            instruction = self.find_instruction(user, name) 
            try:
                instruction = self.find_instruction(user, name)
                if instruction:
                    commit = self.get_argument('commit', 'First commit')
                else:
                    commit = self.get_argument('commit', '')
                    instruction = Instruction(name=name, owner=user)

                instruction.tags = json.loads(self.get_argument('tags', '[]')),
                instruction.instruction = json.loads(self.get_argument('instruction'))

                repo = Repository(config['vcs_dir'],
                          str(instruction.owner.id),
                          str(instruction.id))
                repo.commit(json.dumps(instruction.instruction,
                                       indent=4,
                                       sort_keys=True),
                           commit)
                self.save_instruction(instruction)

            except ShieldException as error:
                context['error'] = "Invalid instruction: %s." % error
                status = 400
            except ValueError as error:
                context['error'] = 'Invalid JSON: %s.' % error
                status = 400
            context['instruction'] = instruction

        if self.is_json_request():
            # for JSON, only include the instruction proper
            self.set_body(json.dumps(context['instruction']))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('instruction', _status_code=status, **context)

    def delete(self, owner, name):
        """
        Hide a single template from view.  Does not actually wipe the
        repo, but sets a 'deleted' flag for the template.
        """
        user = self.current_user
        context = {}
        if not user:
            context['error'] = 'You are not logged in'
        elif not owner == user.name:
            context['error'] = "You cannot delete someone else's template"
            status = 403
        else:
            instruction = self.find_instruction(owner, name)
            if instruction:
                instruction.deleted = True
                self.db_conn.instructions.save(instruction)
                status = 200
            else:
                status['error'] = "Instruction does not exist"
                status = 404

        if self.is_json_request():
            self.set_body(json.dumps(context['instruction']))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('instruction', _status_code=status, **context)


config['handler_tuples'] = [
    (r'^/?$', IndexHandler),
    (r'^/([\w\-]})/?$', UserHandler),
    (r'^/([\w\-]+)/instructions/?$', InstructionCollectionHandler),
    (r'^/([\w\-]+)/instructions/([\w\-]+)/?$', InstructionModelHandler),
    (r'^/([\w\-]+)/tagged/([\w\-]+)/?$', TagCollectionHandler)]

app = Brubeck(**config)
app.run()
