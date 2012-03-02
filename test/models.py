"""
Test caustic/models.py .
"""

import unittest
from caustic.models import User, instruction
from dictshield.base import ShieldException

class TestUser(unittest.TestCase):

    def test_requires_name(self):
        """Should not validate without name.
        """
        u = User()
        with self.assertRaises(ShieldException):
            u.validate()

    def test_validates(self):
        """Should validate if it has a name.
        """
        u = User(name="valid")
        u.validate()

    def test_not_deleted(self):
        """Should start out not deleted.
        """
        u = User(name="exists")
        self.assertFalse(u.deleted)


class Testinstruction(unittest.TestCase):

    def setUp(self):
        """
        Provide with a convenient owner and valid json.
        """
        self.owner = User(name="pwner")
        self.json = '{"load"="http://www.google.com/"}'

    def test_requires_owner(self):
        """
        Should not validate without an owner
        """
        t = instruction(name="orphan", json=self.json)
        with self.assertRaises(ShieldException):
            t.validate()

    def test_requires_name(self):
        """
        Should not validate without a name.
        """
        t = instruction(owner=self.owner, json=self.json)
        with self.assertRaises(ShieldException):
            t.validate()

    def test_requires_json(self):
        """
        Should not validate without json.
        """
        t = instruction(owner=self.owner, name="empty")
        with self.assertRaises(ShieldException):
            t.validate()

    def test_validates(self):
        """
        Should validate if there is json, owner, and name.
        """
        t = instruction(owner=self.owner, json=self.json, name="valid")
        t.validate() # would throw an exception to fail test.

    def test_is_public_by_default(self):
        """
        Instructions are public by default.
        """
        t = instruction(name="public", owner=self.owner)
        self.assertFalse(t.private)

    def test_is_not_deleted_by_default(self):
        """
        Instructions are not deleted by default.
        """
        t = instruction(name="here", owner=self.owner)
        self.assertFalse(t.deleted)


# Primitive runner!
if __name__ == '__main__':
    unittest.main()
