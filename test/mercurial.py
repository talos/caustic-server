""" Test caustic/mercurial.py .
"""

import os
import unittest
import shutil
from caustic.mercurial import Repository, \
                              NoRepositoryException, \
                              AlreadyExistsException

TEST_DIR = os.path.join('test', 'tmp')

if(os.path.isdir(TEST_DIR)):
    shutil.rmtree(TEST_DIR)  # Kid of messy, but make sure we start
                             # with a clean test directory

class TestMercurialRepository(unittest.TestCase):

    def setUp(self):
        """ Build a new test dir for each run.
        """
        os.makedirs(TEST_DIR)

    def tearDown(self):
        """ Kill the old test dir after each run.
        """
        shutil.rmtree(TEST_DIR)

    def test_new_repo(self):
        """ Create a repo.  Make sure it exists.
        """
        repo = Repository(TEST_DIR, 'plato', 'foo')

    def test_get_initial_content_blank(self):
        """ The content should be blank to start.
        """
        repo = Repository(TEST_DIR, 'socrates', 'foo')
        self.assertEqual('', repo.get())

    def test_commit(self):
        """ Commit to the repo.  Make sure the commit happened.
        """
        repo = Repository(TEST_DIR, 'hegel', 'foo')
        repo.commit('the quick brown fox', 'committed')

        self.assertEqual('the quick brown fox', repo.get())

    def test_existing_repo(self):
        """ Retrieve a repo that already exists.
        """
        repo = Repository(TEST_DIR, 'marx', 'foo')
        repo.commit('I exist', 'committed')
        repo = None

        exists = Repository(TEST_DIR, 'marx', 'foo')
        self.assertEqual('I exist', exists.get())

    def test_fail_create(self):
        """ Ensure an exception is thrown if the constructor is not told to
        create missing repos.
        """
        with self.assertRaises(NoRepositoryException):
            Repository(TEST_DIR, 'ayn_rand', 'thoughts', False)

    def test_multiple_commits(self):
        """ Make a few commits and make sure we get the most recent content.
        """
        repo = Repository(TEST_DIR, 'schiller', 'foo')
        repo.commit('foo', 'commit 1')
        repo.commit('bar', 'commit 2')
        repo.commit('baz', 'commit 3')

        self.assertEqual('baz', repo.get())

    def test_clone(self):
        """ Clone an existing repo.
        """
        aristotle = Repository(TEST_DIR, 'aristotle', 'ideas')
        aristotle.commit('foo', '300BC')

        ayn_rand  = aristotle.clone('ayn_rand')
        self.assertEqual('foo', ayn_rand.get())

    def test_clone_self_fails(self):
        """ Cloning repo by same user fails if no name is specified.
        """
        repo = Repository(TEST_DIR, 'baudrillard', 'self')
        with self.assertRaises(AlreadyExistsException):
            repo.clone('baudrillard')

    def test_clone_self_with_different_name(self):
        """ Cloning repo by same user works if different name is specified.
        """
        foo = Repository(TEST_DIR, 'baudrillard', name='foo')
        foo.commit('foo', 'first commit')
        bar = foo.clone('baudrillard', 'bar')
        self.assertEquals('foo', bar.get())

    def test_pull(self):
        """ Pull from another repo.
        """
        hegel = Repository(TEST_DIR, 'hegel', 'dialectic')
        marx = Repository(TEST_DIR, 'marx', 'dialectic')

        hegel.commit('thesis antithesis synthesis', 'revelation')
        marx.pull(hegel)

        self.assertEqual('thesis antithesis synthesis', marx.get())

# Primitive runner!
if __name__ == '__main__':
    unittest.main()
