"""
Test caustic/models.py .
"""

import unittest
from caustic.models import User, Instruction
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


class TestInstruction(unittest.TestCase):

    def setUp(self):
        """
        Provide with a convenient owner and valid json.
        """
        self.owner = User(name="pwner")
        self.instruction = {"load": "http://www.google.com/"}

    def test_requires_owner(self):
        """
        Should not validate without an owner
        """
        t = Instruction(name="orphan", instruction=self.instruction)
        with self.assertRaises(ShieldException):
            t.validate()

    def test_requires_name(self):
        """
        Should not validate without a name.
        """
        t = Instruction(owner=self.owner, instruction=self.instruction)
        with self.assertRaises(ShieldException):
            t.validate()

    def test_requires_instruction(self):
        """
        Should not validate without instruction
        """
        t = Instruction(owner=self.owner, name="empty")
        with self.assertRaises(ShieldException):
            t.validate()
    
    def test_requires_valid_instruction(self):
        """
        Should not validate without valid instruction.
        """
        i = Instruction(owner=self.owner, name='invalid', instruction={'foo':'bar'})
        with self.assertRaises(ShieldException):
            i.validate()

    def test_validates(self):
        """
        Should validate if there is a valid instruction, owner, and name.
        """
        i = Instruction(owner=self.owner, instruction=self.instruction, name="valid")
        i.validate() # would throw an exception to fail test.

    def test_is_public_by_default(self):
        """
        Instructions are public by default.
        """
        t = Instruction(name="public", owner=self.owner)
        self.assertFalse(t.private)

    def test_is_not_deleted_by_default(self):
        """
        Instructions are not deleted by default.
        """
        t = Instruction(name="here", owner=self.owner)
        self.assertFalse(t.deleted)


# Primitive runner!
if __name__ == '__main__':
    unittest.main()
