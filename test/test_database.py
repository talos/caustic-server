"""
Test the database.  Mongod must be running.
"""

import unittest
import shutil
from caustic.database import get_db, Users, Instructions
from jsongit import JsonGitRepository

db = get_db('localhost', 27017, 'caustic_test')
REPO_DIR = 'tmp_git'
INSTRUCTION = {'load':'google'}  # valid instruction for convenience

class TestUsers(unittest.TestCase):

    def setUp(self):
        self.users = Users(db)

    def tearDown(self):
        for name in set(db.collection_names()) - set([u'system.indexes']):
            db[name].drop()

    def test_create_user(self):
        """Saving a user should assign an id.
        """
        u = self.users.create('joe')
        self.assertEquals('joe', u.name)

    def test_get_user_by_id(self):
        """Get a user by the assigned id.
        """
        u = self.users.create('steve')
        self.assertEquals('steve', self.users.get(u.id).name)

    def test_find_user_by_name(self):
        """Find a user by name
        """
        self.users.create('sally')
        self.assertIsNotNone(self.users.find('sally'))

    def test_no_duplicate_names(self):
        """Cannot create two users with same name.
        """
        self.users.create('dave')
        self.assertIsNone(self.users.create('dave'))

    def test_delete_user(self):
        """Cannot find user by ID or name after being deleted.
        """
        george = self.users.create('george')
        self.users.delete(george)
        self.assertIsNone(self.users.get(george.id))
        self.assertIsNone(self.users.find('george'))


class TestInstructions(unittest.TestCase):

    def setUp(self):
        repo = JsonGitRepository(REPO_DIR)
        self.users = Users(db)
        self.creator = self.users.create('creator')
        self.instructions = Instructions(self.users, repo, db)

    def tearDown(self):
        for name in set(db.collection_names()) - set([u'system.indexes']):
            db[name].drop()
        shutil.rmtree(REPO_DIR)

    def test_create_instruction(self):
        """Creating an instruction.
        """
        doc = self.instructions.create(self.creator, 'google', INSTRUCTION)
        self.assertIsNotNone(doc)
        self.assertEquals('google', doc.name)
        self.assertEquals({'load':'google'}, doc.instruction)
        self.assertEquals([], doc.tags)
        doc.validate()

    def test_duplicate_names_ok(self):
        """Duplicate names are OK provided the creators are different.
        """
        joe = self.users.create('joe')
        bobo = self.users.create('bobo')

        self.assertIsNotNone(self.instructions.create(joe, 'name',
                                                      INSTRUCTION))
        self.assertIsNotNone(self.instructions.create(bobo, 'name',
                                                      INSTRUCTION))

    def test_duplicate_creator_and_name_not_ok(self):
        """Duplicate names forbidden if the creator is the same.
        """
        self.instructions.create(self.creator, 'name', INSTRUCTION)
        self.assertIsNone(self.instructions.create(self.creator, 'name',
                                                   INSTRUCTION))

    def test_find_instruction(self):
        """Find an instruction.
        """
        self.instructions.create(self.creator, 'google', INSTRUCTION)
        doc = self.instructions.find(self.creator.name, 'google')
        self.assertEqual('google', doc.name)
        self.assertEqual(INSTRUCTION, doc.instruction)

    def test_find_creator_instructions(self):
        """Find instructions created by a name.
        """
        self.instructions.create(self.creator, 'foo', INSTRUCTION)
        self.instructions.create(self.creator, 'bar', INSTRUCTION)
        self.instructions.create(self.creator, 'baz', INSTRUCTION)
        docs = self.instructions.for_creator(self.creator.name)
        self.assertEqual(3, len(docs))
        self.assertItemsEqual(['foo', 'bar', 'baz'], [d.name for d in docs])

    def test_save_instruction_tags(self):
        """Update the tags in an instruction.
        """
        doc = self.instructions.create(self.creator, 'foo', INSTRUCTION)
        doc.tags = ['bar', 'baz']
        self.assertIsNone(self.instructions.save(doc))

    def test_bad_instruction(self):
        """Don't update bad instruction.
        """
        doc = self.instructions.create(self.creator, 'foo', INSTRUCTION)
        for bad in [{'foo':'bar'}, 7]:
            doc.instruction = bad
            self.assertIsNotNone(self.instructions.save(doc))

    def test_valid_instructions(self):
        """Instructions come in all shapes & sizes.
        """
        doc = self.instructions.create(self.creator, 'foo', INSTRUCTION)
        for valid in ['bare string', ['some', 'array'], {'load':'google'}]:
            doc.instruction = valid
            self.assertIsNone(self.instructions.save(doc))

    def test_bad_tags(self):
        """Don't update with bad tags.
        """
        doc = self.instructions.create(self.creator, 'foo', INSTRUCTION)
        for bad in [7, 'string', {}]:
            doc.tags = bad
            self.assertIsNotNone(self.instructions.save(doc))

    def test_tagged_instructions(self):
        """ Get instructions by their tag.
        """
        roses = self.instructions.create(self.creator, 'roses', INSTRUCTION)
        violets = self.instructions.create(self.creator, 'violets', INSTRUCTION)
        lilacs = self.instructions.create(self.creator, 'lilacs', INSTRUCTION)

        roses.tags = ['red', 'white']
        violets.tags = ['blue', 'purple']
        lilacs.tags = ['purple', 'white']

        for doc in [roses, violets, lilacs]:
            self.assertIsNone(self.instructions.save(doc))

        whites = self.instructions.tagged(self.creator.name, 'white')
        self.assertEqual(2, len(whites))
        self.assertItemsEqual(['roses', 'lilacs'], [d.name for d in whites])

    def test_delete(self):
        """Deleting eliminates, allows creation of new with same name.
        """
        doomed = self.instructions.create(self.creator, 'doomed', INSTRUCTION)
        self.assertTrue(self.instructions.delete(doomed))
        self.assertFalse(self.instructions.delete(doomed))
        dup = self.instructions.create(self.creator, 'doomed', INSTRUCTION)
        self.assertIsNotNone(dup)
