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
from gitdict    import DictRepository, DictAuthor
from models     import User

class Handler(MustacheRendering, UserHandlingMixin):
    """
    An extended handler.
    """
    def _get_user(self, name):
        """
        Get the User document for a given name, or None if there is none.
        """
        user = self.db_conn.users.find_one({'name': name, 'deleted': False})
        return User(**user) if user else None

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

    def is_json_request(self):
        """
        Returns True if this was a request for JSON, False otherwise.
        """
        # print 'IS JSON REQUEST:'
        # print self.message.headers
        # print 'IS JSON REQUEST:'
        return self.message.headers.get('accept').rfind('application/json') > -1

#
# HANDLERS
#
class IndexHandler(Handler):
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

            user = self.db_conn.users.find_one({'name': self.get_argument('user')})
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


class UserHandler(Handler):

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
                self.db_conn.users.save(user.to_python())
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


class InstructionCollectionHandler(Handler):
    """
    This handler provides access to all of a user's instructions.
    """

    def get(self, user_name):
        """
        Provide a listing of all this user's instructions.
        """
        context = { 'user': user_name }
        user = self._get_user(user_name)
        if user:
            context['instructions'] = user.instructions
            status = 200
        else:
            context['error'] = "User %s does not exist." % user_name
            status = 404

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('instruction_collection',
                                        _status_code=status,
                                        **context)

    def post(self, user_name):
        """
        Allow for cloning and creation.
        """
        context = {}
        user = self._get_user(user_name)
        if user != self.current_user:
            context['error'] = 'You cannot modify these resources.'
            status = 403
        else:
            action = self.get_argument('action')
            if action == 'create':
                name = self.get_argument('name')
                if name in user.instructions:
                    status = 409
                    context['error'] = "There is already an instruction with that name"
                else:
                    status = 303
                    self.headers['Location'] = name
            elif action == 'clone':
                owner = self._get_user(self.get_argument('owner'))
                name = self.get_argument('name')

                if not owner:
                    status = 404
                    context['error'] = "There is no user %s" % owner
                elif name in user.instructions:
                    status = 409
                    context['error'] = "You already have an instruction with that name"
                elif name in owner.instructions:
                    user.instructions[name] = owner.instructions[name]
                    self.db_conn.users.save(user.to_python())
                    self.repo.create('/'.join(user, name), user.instructions[name])
                    status = 303 # forward to page for instruction
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

class TagCollectionHandler(Handler):
    """
    This handler provides access to all of a user's instructions with a certain
    tag.
    """
    def get(self, user_name, tag):
        user = self._get_user(user_name)
        context = {'tag': tag, 'user': user_name}
        if user:
            status = 200
            context['instructions'] = self.find_instructions(user, tag=tag)
        else:
            status = 404
            context['error'] = "No user %s" % user_name

        if self.is_json_request():
            self.set_body(json.dumps(context['instructions'] if 'instructions' in context else context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('tagged', _status_code=status, **context)


class InstructionModelHandler(Handler):
    """
    This handler provides clients access to a single instruction by name.
    """

    def get(self, user_name, name):
        """
        Display a single instruction.
        """
        context = {}
        user = self._get_user(user_name)
        if user and name in user.instructions:
            context['instruction'] = user.instruction[name].to_python()
            status = 200
        else:
            context['error'] = "Instruction does not exist"
            status = 404

        if self.is_json_request():
            self.set_body(context['instruction'] if 'instruction' in context else context)
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
            try:
                instruction = json.loads(self.get_argument('instruction'))

                repo = self.application.repo
                key = '/'.join([owner, name])
                if repo.has(key):
                    git_dict = repo.get(key)
                    git_dict.clear()
                    git_dict.update(instruction)
                    git_dict.commit(author=DictAuthor(str(user.id), str(user.id)).signature())
                else:
                    repo.create(key, instruction)
                status = 201
                context['instruction'] = instruction
            except ShieldException as error:
                context['error'] = "Invalid instruction: %s." % error
                status = 400
            except ValueError as error:
                context['error'] = 'Invalid JSON: %s.' % error
                status = 400
            context['instruction'] = instruction

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('instruction', _status_code=status, **context)

    def delete(self, owner, name):
        """
        Delete an instruction.
        """
        user = self.current_user
        context = {}
        if not user:
            context['error'] = 'You are not logged in'
        elif not owner == user.name:
            context['error'] = "You cannot delete someone else's template"
            status = 403
        else:
            if name in user.instructions:
                user.instructions.pop(name)
                self.db_conn.users.save(user.to_python())
                status = 200
            else:
                status['error'] = "Instruction does not exist"
                status = 404

        if self.is_json_request():
            self.set_body(json.dumps(context))
            self.set_status(status)
            return self.render()
        else:
            return self.render_template('delete_instruction', _status_code=status, **context)


config['handler_tuples'] = [
    (r'^/?$', IndexHandler),
    (r'^/([\w\-]})/?$', UserHandler),
    (r'^/([\w\-]+)/instructions/?$', InstructionCollectionHandler),
    (r'^/([\w\-]+)/instructions/([\w\-]+)/?$', InstructionModelHandler),
    (r'^/([\w\-]+)/tagged/([\w\-]+)/?$', TagCollectionHandler)]

app = Brubeck(**config)
app.repo = DictRepository(config['git_dir'])
app.run()
