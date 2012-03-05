"""
Test caustic/jsongit.py .
"""

import os
import unittest
import shutil
from caustic.jsongit import JSONRepository

TEST_DIR = os.path.join('test', 'tmp')

class TestJSONRepository(unittest.TestCase):

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        if os.path.isdir(TEST_DIR):
            self.fail('There was already a repo at %s.' % TEST_DIR)
        os.makedirs(TEST_DIR)

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        shutil.rmtree(TEST_DIR)

    def test_new_repo(self):
        """
        Create a repo.  Make sure it exists.
        """
        JSONRepository(TEST_DIR)
        self.assertTrue(os.path.isdir(TEST_DIR)

    def test_get_initial_content_blank(self):
        """The content should be blank to start.
        """
        repo = Repository(TEST_DIR, 'socrates', 'foo')
        self.assertEqual('', repo.get())

    def test_commit(self):
        """Commit to the repo.  Make sure the commit happened.
        """
        repo = Repository(TEST_DIR, 'hegel', 'foo')
        repo.commit('the quick brown fox', 'committed')

        self.assertEqual('the quick brown fox', repo.get())

    def test_existing_repo(self):
        """Retrieve a repo that already exists.
        """
        repo = Repository(TEST_DIR, 'marx', 'foo')
        repo.commit('I exist', 'committed')
        repo = None

        exists = Repository(TEST_DIR, 'marx', 'foo')
        self.assertEqual('I exist', exists.get())

    def test_fail_create(self):
        """Ensure an exception is thrown if the constructor is not told to
        create missing repos.
        """
        with self.assertRaises(NoRepositoryException):
            Repository(TEST_DIR, 'ayn_rand', 'thoughts', False)

    def test_multiple_commits(self):
        """Make a few commits and make sure we get the most recent content.
        """
        repo = Repository(TEST_DIR, 'schiller', 'foo')
        repo.commit('foo', 'commit 1')
        repo.commit('bar', 'commit 2')
        repo.commit('baz', 'commit 3')

        self.assertEqual('baz', repo.get())

    def test_clone(self):
        """Clone an existing repo.
        """
        aristotle = Repository(TEST_DIR, 'aristotle', 'ideas')
        aristotle.commit('foo', '300BC')

        ayn_rand = aristotle.clone('ayn_rand', 'ideas')
        self.assertEqual('foo', ayn_rand.get())

    def test_clone_self_fails(self):
        """Cloning repo by same user fails if same name specified.
        """
        repo = Repository(TEST_DIR, 'baudrillard', 'self')
        with self.assertRaises(AlreadyExistsException):
            repo.clone('baudrillard', 'self')

    def test_clone_self_with_different_name(self):
        """Cloning repo by same user works if different name is specified.
        """
        foo = Repository(TEST_DIR, 'baudrillard', name='foo')
        foo.commit('foo', 'first commit')
        bar = foo.clone('baudrillard', 'bar')
        self.assertEquals('foo', bar.get())

    def test_pull(self):
        """Pull from another repo.
        """
        hegel = Repository(TEST_DIR, 'hegel', 'dialectic')
        marx = Repository(TEST_DIR, 'marx', 'dialectic')

        hegel.commit('thesis antithesis synthesis', 'revelation')
        marx.pull(hegel)

        self.assertEqual('thesis antithesis synthesis', marx.get())

