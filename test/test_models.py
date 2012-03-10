"""
Test caustic/models.py .
"""

import unittest
from caustic.models import User, InstructionDocument, InstructionField
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

    def test_deserialize(self):
        """Deserialize a complex user.
        """
        u = User(**{
            'name': 'talos',
            'deleted': False,
            'instructions': [{
                'name': 'grab some stuff',
                'tags': ['utility', 'cool'],
                'instruction': {'load': 'google', 'then': {'find': 'stuff'}}
            }]
        })
        u.validate()
        self.assertEqual('talos', u.name)
        self.assertEqual(False, u.deleted)
        self.assertEqual(
            [InstructionDocument(name='grab some stuff',
                                 tags=['utility', 'cool'],
                                 instruction={'load': 'google', 'then': {'find': 'stuff'}})],
            u.instructions)

class TestInstructionDocument(unittest.TestCase):

    def test_requires_name(self):
        """
        Needs a name.
        """
        doc = InstructionDocument(instruction={"load": "google.com"})
        with self.assertRaises(ShieldException):
            doc.validate()

    def test_requires_instruction(self):
        """
        Needs an instruction.
        """
        doc = InstructionDocument(name='name')
        with self.assertRaises(ShieldException):
            doc.validate()

    def test_requires_valid_instruction(self):
        """
        Should not validate without valid instruction.
        """
        doc = InstructionDocument(name='name',instruction={"foo":"bar"})
        with self.assertRaises(ShieldException):
            doc.validate()

    def test_validates(self):
        """
        Should validate if there is a valid instruction and name.
        """
        doc = InstructionDocument(name='name',instruction={"load":"google.com"})
        doc.validate()

class TestInstructionField(unittest.TestCase):

    def test_invalid(self):
        for invalid in [7,{'foo': 'bar'}]:
            with self.assertRaises(ShieldException):
                InstructionField().validate(invalid)

    def test_valid(self):
        for valid in ['foo', ['foo', 'bar'], {'load':'google.com'}, {'find':'.*'}]:
            InstructionField().validate(valid)
