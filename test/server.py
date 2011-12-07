""" Test server.py.  Restarts caustic server each time, but you are
responsible for having mongrel and mongodb online.
"""

import unittest
import os
import base64
import requests
import json
import subprocess

HOST = "http://localhost:6767"


class TestServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Start up the caustic server app.
        """
        cls.proc = subprocess.Popen('python caustic/server.py', shell=True)

    @classmethod
    def tearDownClass(cls):
        """Shut down the caustic server app.
        """
        cls.proc.terminate()
        cls.proc.wait()

    def _signup(self, user):
        """Sign up `user`, while keeping track of the signup for later cleanup.
        """
        self.created_accounts.append(user)
        r = self.s.post("%s/signup" % HOST, data={'user': user})
        return r

    def _login(self, user):
        """Login `user`, return the response object.
        """
        return self.s.post("%s/login" % HOST, data={'user': user})

    def _logout(self):
        """Log out, return the response object.
        """
        return self.s.post("%s/logout" % HOST, data='')

    def setUp(self):
        """Keep track of created accounts and session.
        """
        self.created_accounts = []
        self.s = requests.Session()

    def tearDown(self):
        """Destroy any created accounts.
        """
        for user in self.created_accounts:
            self._logout()
            self._login(user)
            self.s.post("%s/die" % HOST)

    def test_signup(self):
        """Test signing up.  We should have logged in after signing up.
        """
        r = self._signup('corbusier')
        self.assertEqual(204, r.status_code)
        self.assertTrue('session' in self.s.cookies)
        self.assertFalse(self.s.cookies['session'] == '')

    def test_login(self):
        """Test logging in.
        """
        self._signup('mies')
        self._logout()
        r =  self._login('mies')
        self.assertEqual(204, r.status_code)
        self.assertTrue('session' in self.s.cookies)
        self.assertFalse(self.s.cookies['session'] == '')

    def test_logout(self):
        """Test logging out.
        """
        self._signup('vitruvius')
        r = self._logout()
        self.assertEqual(204, r.status_code)
        self.assertTrue('session' in self.s.cookies)
        self.assertTrue(self.s.cookies['session'] == '')

    def test_nonexistent(self):
        """ Test getting a 404.
        """
        r = self.s.get("%s/talos/nope" % HOST)
        self.assertEqual(404, r.status_code)

    def test_create_template(self):
        """ Create a template on the server using HTTP PUT.
        """
        self._signup('fuller')
        data = { 'json': json.dumps({"load":"http://www.google.com"}) }
        r = self.s.put("%s/fuller/manhattan-bubble" % HOST, data=data)
        self.assertEqual(204, r.status_code)

    def test_get_template(self):
        """ Get a template on the server using HTTP GET.
        """
        self._signup('jacobs')
        data = { 'json': json.dumps({"load":"http://www.google.com/"}) }
        self.s.put("%s/jacobs/life-n-death" % HOST, data=data)

        r = self.s.get("%s/jacobs/life-n-death" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(data['json'], r.content)

# Primitive runner!
if __name__ == '__main__':
    unittest.main()
