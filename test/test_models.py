"""
Test caustic/models.py .
"""

import unittest
from caustic.models import User
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


class TestInstructionsField(unittest.TestCase):

    def setUp(self):
        """
        Provide with a convenient owner and valid json.
        """
        self.owner = User(name="pwner")

    def test_requires_string_key(self):
        self.owner.instructions[100] = {"load":"google.com"}
        with self.assertRaises(ShieldException):
            self.owner.validate()

    def test_requires_valid_instruction(self):
        """
        Should not validate without valid instruction.
        """
        self.owner.instructions['google'] = {"foo":"bar"}
        with self.assertRaises(ShieldException):
            self.owner.validate()

    def test_validates(self):
        """
        Should validate if there is a valid instruction, owner, and name.
        """
        self.owner.instructions['valid'] = {'load':'google.com'}
        self.owner.validate()

