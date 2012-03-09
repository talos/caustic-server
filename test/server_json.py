import unittest
import requests
import json

HOST = "http://localhost:6767"
LOAD_GOOGLE = '{"load":"http://www.google.com/"}' # valid scraping instruction

class TestServerJSON(unittest.TestCase):
    """
    Test the server's JSON API.
    """

    def _signup(self, user):
        """
        Sign up `user`, while keeping track of the signup for later cleanup.
        """
        self.created_accounts.append(user)
        self.s.post("%s" % HOST, data={
            'action': 'signup',
            'user'  : user
        })

    def _login(self, user):
        """
        Login `user`.
        """
        self.s.post("%s" % HOST, data={
            'action': 'login',
            'user'  : user
        })

    def _logout(self):
        """
        Log out.
        """
        self.s.post("%s" % HOST, data={
            'action': 'logout'
        })

    def setUp(self):
        """
        Keep track of created accounts and session, make sure requests are for
        JSON.
        """
        self.created_accounts = []
        self.s = requests.Session(headers={"Accept":"application/json"})

    def tearDown(self):
        """
        Destroy any created accounts.
        """
        for user in self.created_accounts:
            self._logout()
            self._login(user)
            token = json.loads(self.s.delete("%s/%s" % (HOST, user)).content)['token']
            self.s.delete("%s/%s" % (HOST, user), data={'token': token})

    def test_signup(self):
        """
        Test signing up.  We should have logged in after signing up.
        """
        self._signup('corbusier')
        self.assertTrue('session' in self.s.cookies)

    def test_login(self):
        """
        Test logging in.
        """
        self._signup('mies')
        self._logout()
        self._login('mies')
        self.assertTrue('session' in self.s.cookies)

    def test_logout(self):
        """
        Test logging out.
        """
        self._signup('vitruvius')
        self._logout()
        self.assertFalse('session' in self.s.cookies)

    def test_nonexistent(self):
        """
        Test getting a 404.
        """
        r = self.s.get("%s/lksdjflksdjg" % HOST)
        self.assertEqual(404, r.status_code)

    def test_post_valid_instruction(self):
        self._signup('fuller')
        r = self.s.post("%s/fuller/instructions/" % HOST, data={
            'name': 'manhattan-bubble',
            'instruction': LOAD_GOOGLE
        })
        self.assertEqual(303, r.status_code)
        self.assertEqual('manhattan-bubble', r.headers['Location'])

    def test_put_valid_instruction(self):
        """
        Create an instruction on the server using HTTP PUT.
        """
        self._signup('fuller')
        r = self.s.put("%s/fuller/instructions/manhattan-bubble" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self.assertEqual(201, r.status_code)

    def test_invalid_instruction(self):
        """
        Ensure the server rejects an invalid instruction.
        """
        self._signup('chiang')
        r = self.s.put("%s/chiang/instructions/politics" % HOST, data={
            'instruction': json.dumps({ 'foo':'bar' })
        })
        self.assertEqual(400, r.status_code)

    def test_not_logged_in_no_create(self):
        """
        Ensure the server rejects creating an instruction for a not logged
        in user.
        """
        self._signup('lennon')
        self._logout()
        r = self.s.put("%s/lennon/instructions/nope" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self.assertEqual(401, r.status_code)

    def test_get_instruction_logged_in(self):
        """
        Get an instruction on the server using HTTP GET while logged in.
        """
        self._signup('jacobs')
        self.s.put("%s/jacobs/instructions/life-n-death" % HOST, data={
            'instruction': LOAD_GOOGLE
        })

        r = self.s.get("%s/jacobs/instruction/life-n-death" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(LOAD_GOOGLE, r.content)

    def test_get_instruction_not_logged_in(self):
        """
        Get a instruction on the server using HTTP GET while not logged in.
        """
        self._signup('jacobs')
        self.s.put("%s/jacobs/instructions/life-n-death" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self._logout()

        r = self.s.get("%s/jacobs/instructions/life-n-death" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(LOAD_GOOGLE, r.content)

    def test_update_instruction_json(self):
        """
        Update an instruction by replacing it with PUT.
        """
        self._signup('moses')
        self.s.put("%s/moses/instructions/bqe" % HOST, data={
            'instruction': LOAD_GOOGLE
        })

        load_nytimes = json.dumps({"load":"http://www.nytimes.com/"}) 
        self.s.put("%s/moses/instructions/bqe" % HOST, data={
            'instruction': load_nytimes
        })

        r = self.s.get("%s/moses/instructions/bqe" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(load_nytimes, r.content)

    def test_get_instructions_by_tag(self):
        """
        Get several instructions with one tag.  Returns an array of
        links to the instructions.
        """
        self._signup('trog-dor')
        self.s.put("%s/trog-dor/instructions/pillaging" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self.s.put("%s/trog-dor/instructions/burning" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self.s.put("%s/trog-dor/instructions/pillaging/tags/burnination" % HOST)
        self.s.put("%s/trog-dor/instructions/burning/tags/burnination" % HOST)

        r = self.s.get("%s/trog-dor/tagged/burnination" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(["/trog-dor/instructions/burning",
                          "/trog-dor/instructions/pillaging"],
                         json.loads(r.content))

    def test_get_nonexistent_tag(self):
        """
        Get instructions for nonexistent tag.  Returns an empty array.
        """
        self._signup('vicious')
        self._logout()

        r = self.s.get("%s/vicious/tagged/erudite" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual([], json.loads(r.content))

    def test_delete_tag(self):
        """
        Delete a tag.
        """
        self._signup('fashionista')
        self.s.put("%s/fashionista/instructions/ray-bans" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self.s.put("%s/fashionista/instructions/ray-bans/tags/trendy" % HOST)
        self.s.delete("%s/fashionista/instructions/ray-bans/tags/trendy" % HOST)

        r = self.s.get("%s/fashionista/tagged/trendy" % HOST)
        self.assertEqual([], json.loads(r.content))

    def test_clone_instruction(self):
        """
        One user clones another user's instruction.  Should keep JSON and tags.
        """
        self._signup('muddy')
        self.s.put("%s/muddy/instructions/delta-blues" % HOST, data={
            'instruction': LOAD_GOOGLE
        })
        self.s.put("%s/muddy/instructions/delta-blues/tags/guitar" % HOST)
        self._logout()

        self._signup('crapton')
        r = self.s.post("%s/crapton/instructions/" % HOST, data={
            'clone': '/muddy/instructions/delta-blues'
        })
        self.assertEqual(201, r.status_code)
        self.assertEqual('/crapton/instructions/delta-blues', r.headers['Location'])

        r = self.s.get("%s/crapton/instructions/delta-blues" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(LOAD_GOOGLE, r.content)

        r = self.s.get("%s/crapton/tagged/guitar" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual(["/crapton/instructions/delta-blues"], json.loads(r.content))

    def test_pull_instruction(self):
        """
        One user pulls another user's instruction after cloning it.
        Should replace the current instruction json with that of the
        pulled instruction.
        """
        self._signup('barrett')
        data = json.dumps('{"load":"http://www.saucerful.com/"}')
        self.s.put("%s/barrett/instructions/saucerful" % HOST, data={
            'instruction': data
        })
        self._logout()

        self._signup('gilmour')
        self.s.post("%s/gilmour/instructions/" % HOST, {
            'clone': '/barret/instructions/saucerful'
        })
        self._logout()

        self._login('barrett')
        data = json.dumps('{"load":"http://www.jugband.com/"}')
        self.s.put("%s/barrett/instructions/saucerful" % HOST, data={
            'instruction': data
        })
        self._logout()

        self._login('gilmour')
        r = self.s.post("%s/gilmour/instructions/saucerful" % HOST, data={
            'pull': '/barret/instructions/saucerful' 
        })
        self.assertEqual(204, r.status_code)
        r = self.s.get("%s/gilmour/saucerful" % HOST)
        self.assertEqual(200, r.status_code)
        self.assertEqual('{"loads":"http://www.jugband.com/"}', r.content)


# Primitive runner!
if __name__ == '__main__':
    unittest.main()
