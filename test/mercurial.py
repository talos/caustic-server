'''
Test caustic/mercurial.py . This won't run on Windows due to call so to
subprocess.call()
'''

import os
import unittest
from subprocess import call
from caustic.mercurial import Repository

TEST_DIR = os.path.join('test', 'repos')

class TestMercurialRepository(unittest.TestCase):

    def setUp(self):
        ''' Build a new test dir for each run.
        '''
        #call(['mkdir', '-p', TEST_DIR])
        os.makedirs(TEST_DIR)

    def tearDown(self):
        ''' Kill the old test dir after each run.
        '''
        call(['rm', '-rf', TEST_DIR])

    def test_new_repo(self):
        ''' Create a repo.  Make sure it exists.
        '''
        repo = Repository(TEST_DIR, 'plato', 'foo')

    def test_get_initial_content_blank(self):
        ''' The content should be blank to start.
        '''
        repo = Repository(TEST_DIR, 'socrates', 'foo')
        self.assertEqual('', repo.get())

    def test_commit(self):
        ''' Commit to the repo.  Make sure the commit happened.
        '''
        repo = Repository(TEST_DIR, 'hegel', 'foo')
        repo.commit('the quick brown fox', 'committed')

        self.assertEqual('the quick brown fox', repo.get())

    def test_existing_repo(self):
        ''' Retrieve a repo that already exists.
        '''
        repo = Repository(TEST_DIR, 'marx', 'foo')
        repo.commit('I exist', 'committed')
        repo = None

        exists = Repository(TEST_DIR, 'marx', 'foo')
        self.assertEqual('I exist', exists.get())

# Primitive runner!
if __name__ == '__main__':
    unittest.main()
