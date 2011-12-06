""" Test server.py.  Make sure that a caustic-server instance is running before
trying this.
"""

import unittest
# import httplib
# import urllib
import os
import base64
import requests
import json

HOST = "localhost"
PORT = 6767

def random_string(length):
    """Generate a random string of specified length.
    """
    base64.urlsafe_b64encode(os.urandom(length))

class TestServer(unittest.TestCase):

    def _signup(self, user):
        """Sign up `user`, while keeping track of the sign up for later cleanup.
        """
        self.created_accounts.push(user)
        return r.post("%s/signup" % HOST, data={'user' : user})

    def _login(self, user):
        """Login `user`, return the response object.
        """
        return r.post("%s/login" % HOST, data={'user' : user})

    def _logout(self):
        """Log out, return the response object.
        """
        return r.post("%s/logout" % HOST)

    def _die(self):
        return r.post("%s/die" % HOST)

    def setUp(self):
        self.created_accounts = []

    def tearDown(self):
        """Destroy any created accounts.
        """
        for user in self.created_accounts:
            self._logout()
            self._login(user)
            self._die()

    def test_signup(self):
        """Test signing up.
        """
        r = self.assertEqual(200, self._signup('corbusier'))

    def test_login(self):
        """Test logging in.
        """
        self._signup('mies')
        r = self.assertEqual(200, self._login('mies'))
        self.assertEqual(200, r.status)
        self.assertTrue('session' in r.cookies)

    def test_logout(self):
        """Test logging out.
        """
        self._signup('vitruvius')
        self._login('vitruvius')
        self._login('talos')
        r = self._logout()
        self.assertEqual(200, r.status)
        self.assertFalse('session' in r.cookies)

    def test_nonexistent(self):
        """ Test getting a 404.
        """
        r = requests.get("%s/%s/%s" % (HOST, 'talos', 'nope'))
        self.assertEqual(404, r.status)

    def test_create_template(self):
        """ Create a template on the server using HTTP PUT.
        """
        name = random_string(10)
        data = { 'json': json.dumps({"load":"http://www.google.com"}) }
        r = requests.put("%s/%s/%s" % (HOST, 'talos', name), data=data)

        self.assertEqual(200, r.status)
        #self.assertEqual("Created template %s/%s" % ('talos', random_string), r.content)

    def test_get_template(self):
        """ Get a template on the server using HTTP GET.
        """
        name = random_string(10)
        data = { 'json': json.dumps({"load":"http://www.google.com/"}) }
        requests.put("%s/%s/%s" % (HOST, 'talos', name), data=data)

        r = requests.get("%s/%s/%s" % (HOST, 'talos', name))
        self.assertEqual(200, r.status)
        self.assertEqual({"load":"http://www.google.com"}, json.loads(r.content))

# Primitive runner!
if __name__ == '__main__':
    unittest.main()
