#!/usr/bin/env python

"""
Caustic server.

Store caustic JSON templates in little repos and let users shoot 'em round.
"""

import json
import logging
import uuid
from jsongit import JsonGitRepository
from dictshield.base import ShieldException
from brubeck.request_handling import Brubeck
from brubeck.auth import UserHandlingMixin

from brubeck.templating import MustacheRendering, load_mustache_env
from config     import DB_NAME, DB_HOST, DB_PORT, COOKIE_SECRET, RECV_SPEC, \
                       SEND_SPEC, JSON_GIT_DIR, TEMPLATE_DIR
from database   import Users, Instructions, get_db

class Handler(MustacheRendering, UserHandlingMixin):
    """
    An extended handler.
    """

    def get_current_user(self):
        """
        Return the User DictShield model from the database using
        cookie session.  Returns `None` if there is no current user.
        """
        id = self.get_cookie('session', None, self.application.cookie_secret)
        return self.application.users.get(id)

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
                user_name = self.get_argument('user')

                if not user_name:
                    context['error'] = 'You must specify user name to sign up'
                    status = 400
                elif self.application.users.find(user_name):
                    context['error'] = "User name '%s' is already in use." % user_name
                    status = 400
                else:
                    user = self.application.users.create(user_name)
                    self.set_current_user(user)
                    context['user'] = user.name
                    status = 200
        elif action == 'login':
            logging.warn('Login not yet implemented.')

            if self.current_user:
                context['error'] = 'You are already logged in as %s' % self.current_user.name
                status = 403

            user = self.application.users.find(self.get_argument('user'))
            if user:
                self.set_current_user(user)
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

    def get(self, user):
        """
        Get the user's homepage.
        """
        return self.render_template('user', user=user)

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
                self.application.users.delete(user)
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

class InstructionCollectionHandler(Handler):
    """
    This handler provides access to all of a user's instructions.
    """

    def get(self, user_name):
        """
        Provide a listing of all this user's instructions.
        """
        context = { 'user': user_name }
        instructions = self.application.instructions.for_creator(user_name)
        if instructions == None:
            context['error'] = "User %s does not exist." % user_name
            status = 404
        else:
            context['instructions'] = instructions
            status = 200

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
        user = self.application.users.find(user_name)
        if user != self.current_user:
            context['error'] = 'You cannot modify these resources.'
            status = 403
        else:
            action = self.get_argument('action')
            if action == 'create':
                name = self.get_argument('name')
                if self.application.instructions.find(user_name, name):
                    status = 409
                    context['error'] = "There is already an instruction with that name"
                else:
                    status = 302
                    self.headers['Location'] = name  # they will be able to create it there
            # elif action == 'clone':
            #     owner = self.application.users.find(self.get_argument('owner'))
            #     name = self.get_argument('name')

            #     if not owner:
            #         status = 404
            #         context['error'] = "There is no user %s" % owner
            #     elif name in user.instructions:
            #         status = 409
            #         context['error'] = "You already have an instruction with that name"
            #     elif name in owner.instructions:
            #         user.instructions[name] = owner.instructions[name]
            #         self.db_conn.users.save(user.to_python())
            #         self.repo.create('/'.join(user, name), user.instructions[name])
            #         status = 303 # forward to page for instruction
            #         self.headers['Location'] = name
            #     else:
            #         status = 409
            #         context['error'] = "Could not clone the instruction."
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
        context = {'tag': tag, 'user': user_name}
        instructions = self.application.instructions.tagged(user_name, tag)
        if instructions == None:
            status = 404
            context['error'] = "No user %s" % user_name
        else:
            status = 200
            context['instructions'] = instructions

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
        user = self.application.users.find(user_name)
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
                doc = self.application.instructions.find(user.name, name)
                if doc:
                    doc.instruction = instruction
                    self.application.instructions.update(doc)
                else:
                    doc = self.application.instructions.create(user, name, instruction)
                status = 201
                context['instruction'] = instruction
            except ShieldException as error:
                context['error'] = "Invalid instruction: %s." % error
                status = 400
            except ValueError as error:
                context['error'] = 'Invalid JSON: %s.' % error
                status = 400

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
            instruction = self.application.instructions.find(user, name)
            if instruction:
                self.application.instructions.delete(instruction)
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


config = {
    'mongrel2_pair': (RECV_SPEC, SEND_SPEC),
    'handler_tuples': [
        (r'^/?$', IndexHandler),
        (r'^/([\w\-]})/?$', UserHandler),
        (r'^/([\w\-]+)/instructions/?$', InstructionCollectionHandler),
        (r'^/([\w\-]+)/instructions/([\w\-]+)/?$', InstructionModelHandler),
        (r'^/([\w\-]+)/tagged/([\w\-]+)/?$', TagCollectionHandler)],
    'template_loader': load_mustache_env(TEMPLATE_DIR),
    'cookie_secret': COOKIE_SECRET,
}

app = Brubeck(**config)
db = get_db(DB_HOST, DB_PORT, DB_NAME)
app.users = Users(db)
app.instructions = Instructions(app.users, JsonGitRepository(JSON_GIT_DIR), db)
app.run()
