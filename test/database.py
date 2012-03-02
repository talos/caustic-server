"""
Test the database.  Mongod must be running.
"""

import pymongo
import unittest
from caustic.models import User, Instruction

HOST = "http://localhost:6767"
LOAD_GOOGLE = '{"load":"http://www.google.com/"}'

class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up mongod connection.
        """
        cls.db = pymongo.Connection().test_caustic

    def setUp(self):
        """Provide access to collections in test_caustic database, and easy
        user/instruction fixtures.
        """
        self.users = TestDatabase.db.users
        self.instructions = TestDatabase.db.instructions

    def tearDown(self):
        """Drop collections.
        """
        self.users.drop()
        self.instructions.drop()

    def test_save_user_assigns_id(self):
        """Saving a user should assign an id.
        """
        self.assertIsNotNone(self.users.save(User(name="john").to_python()))

    def test_get_user_by_id(self):
        """Get a user by the assigned id.
        """
        id = self.users.save(User(name="fred").to_python())
        u = User(**self.users.find_one(id))
        self.assertEqual("fred", u.name)

    def test_get_user_by_name(self):
        """Get a user by name
        """
        self.users.save(User(name="sally").to_python())
        self.assertIsNotNone(self.users.find_one({'name': 'sally'}))

    def test_save_instruction_assigns_id(self):
        """Saving a instruction should assign an id.
        """
        bobbie = User(name="bobbie")
        self.users.save(bobbie.to_python())
        t = Instruction(owner=bobbie, name="instruction", json=LOAD_GOOGLE)
        self.assertIsNotNone(self.instructions.save(t.to_python()))

    def test_get_instructions_by_owner_name(self):
        """
        Get an owner's instructions.
        """
        chris = User(name='chris')
        self.instructions.save(Instruction(owner=chris, name="first", json=LOAD_GOOGLE).to_python())
        self.instructions.save(Instruction(owner=chris, name="second", json=LOAD_GOOGLE).to_python())
        self.assertEqual(2, self.instructions.find({'owner.name': 'chris'}).count())

    def test_get_instructions_by_tag(self):
        """
        Get instructions by their tag.
        """
        tuten = User(name='tuten')
        mao = User(name='mao')
        self.instructions.save(Instruction(owner=tuten,
                                     name="fiction",
                                     tags=['long march'],
                                     json=LOAD_GOOGLE).to_python())
        self.instructions.save(Instruction(owner=mao,
                                     name="works",
                                     tags=['long march'],
                                     json=LOAD_GOOGLE).to_python())
        self.assertEqual(2, self.instructions.find({'tags':'long march'}).count())

    def test_get_instructions_by_tag_and_name(self):
        """
        Get instructions by their tag and name.
        """
        tuten = User(name='tuten')
        mao = User(name='mao')
        self.instructions.save(Instruction(owner=tuten,
                                     name="fiction",
                                     tags=['long march'],
                                     json=LOAD_GOOGLE).to_python())
        self.instructions.save(Instruction(owner=mao,
                                     name="works",
                                     tags=['long march'],
                                     json=LOAD_GOOGLE).to_python())
        self.assertEqual(1, self.instructions.find({'tags':'long march', 'owner.name': 'mao'}).count())
        t = Instruction(**self.instructions.find_one({'tags':'long march', 'owner.name':'mao'}))
        self.assertEqual('works', t.name)

# Primitive runner!
if __name__ == '__main__':
    unittest.main()
