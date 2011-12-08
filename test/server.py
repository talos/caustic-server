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

    def test_get_template_logged_in(self):
        """ Get a template on the server using HTTP GET while logged in.
        """
        self._signup('jacobs')
        data = { 'json': json.dumps({"load":"http://www.google.com/"}) }
        self.s.put("%s/jacobs/life-n-death" % HOST, data=data)

        r = self.s.get("%s/jacobs/life-n-death" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(data['json'], r.content)

    def test_get_template_not_logged_in(self):
        """ Get a template on the server using HTTP GET while not logged in.
        """
        self._signup('jacobs')
        data = { 'json': json.dumps({"load":"http://www.google.com/"}) }
        self.s.put("%s/jacobs/life-n-death" % HOST, data=data)
        self._logout()

        r = self.s.get("%s/jacobs/life-n-death" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(data['json'], r.content)

    def test_update_template_json(self):
        """ Update a template using HTTP PUT.
        """
        self._signup('moses')
        data = { 'json': json.dumps({"load":"http://www.google.com/"}) }
        self.s.put("%s/moses/bqe" % HOST, data=data)

        data = { 'json': json.dumps({"load":"http://www.nytimes.com/"}) }
        self.s.put("%s/moses/bqe" %HOST, data=data)

        r = self.s.get("%s/moses/bqe" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(data['json'], r.content)

    def test_get_templates_by_tag(self):
        """ Get several templates with one tag.  Returns an array of
        relative links to the templates.
        """
        self._signup('trog-dor')
        burning = {
            'json': json.dumps({"load":"http://www.burning.com/"}),
            'tags': ['burnination', 'wonton destruction']
            }
        self.s.put("%s/trog-dor/burning" % HOST, data=villagers)

        pillaging = {
            'json': json.dumps({"load":"http://www.pillaging.com/"}),
            'tags': ['theft', 'burnination']
            }
        self.s.put("%s/trog-dor/pillaging" %HOST, data=pitchforks)

        self._logout()

        r = self.s.get("%s/trog-dor/tagged/burnination" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual('["/trog-dor/burning","/trog-dor/pillaging"]',
                         r.content)

    def test_get_nonexistent_tag(self):
        """Get templates for nonexistent tag.  Returns an empty array.
        """
        self._signup('vicious')
        self._logout()

        r = self.s.get("%s/vicious/tagged/erudite")
        self.assertEqual(200, r.status_code)
        self.assertEqual('[]', r.content)

    def test_clone_template(self):
        """One user clones another user's template.  Should keep JSON and tags.
        """
        self._signup('muddy')
        data = {'json':json.dumps('{"loads":"http://en.wikipedia.org/"}'),
                'tags':['music', 'guitar']}
        self.s.put("%s/muddy/delta-blues" % HOST, data=data)
        self._logout()

        self._signup('crapton')
        r = self.s.post("%s/muddy/delta-blues/clone" % HOST)
        self.assertEqual(204, r.status_code)
        self._logout()

        r = self.s.get("%s/crapton/delta-blues" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(data['json'], r.content)

        r = self.s.get("%s/crapton/tagged/guitar" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual('["../delta-blues"]', r.content)

    def test_pull_template(self):
        """One user pulls another user's template after cloning it.
        Should replace the current template json with that of the
        pulled template.
        """
        self._signup('barrett')
        data = {'json':json.dumps('{"loads":"http://www.saucerful.com/"}')}
        self.s.put("%s/barrett/saucerful" % HOST)
        self._logout()

        self._signup('gilmour')
        self.s.post("%s/barret/saucerful/clone" % HOST)
        self._logout()

        self._login('barrett')
        data = {'json':json.dumps('{"loads":"http://www.jugband.com/"}')}
        self.s.put("%s/barrett/saucerful" % HOST)
        self._logout()

        self._login('gilmour')
        r = self.s.post("%s/gilmour/saucerful/pull/barrett/saucerful" % HOST)
        self.assertEqual(204, r.status_code)
        r = self.s.get("%s/gilmour/saucerful" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual('{"loads":"http://www.jugband.com/"}', r.content)


# Primitive runner!
if __name__ == '__main__':
    unittest.main()
