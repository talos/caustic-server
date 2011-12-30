""" Test the database.  Mongod must be running.
"""

import pymongo
import unittest
from caustic.models import User, Template

HOST = "http://localhost:6767"


class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up mongod connection.
        """
        cls.db = pymongo.Connection().test_caustic

    def setUp(self):
        """Provide access to collections in test_caustic database, and easy
        user/template fixtures.
        """
        self.users = TestDatabase.db.users
        self.templates = TestDatabase.db.templates

        self.u = User(name="user")
        self.t = Template(owner=self.u,
                          name="template",
                          json='{"load":"http://www.google.com/"}')

    def tearDown(self):
        """Drop collections.
        """
        self.users.drop()
        self.templates.drop()

    def test_save_user_assigns_id(self):
        """Saving a user should assign an id.
        """
        self.assertIsNotNone(self.users.save(self.u.to_python()))

    def test_get_user_by_id(self):
        """Get a user by the assigned id.
        """
        id = self.users.save(self.u.to_python())
        u = User(**self.users.find_one(id))
        self.assertEqual(self.u.name, u.name)

    def test_get_user_by_name(self):
        """Get a user by name
        """
        id = self.users.save(self.u.to_python())

        u = User(**self.users.find_one({'name': self.u.name}))
        self.assertEqual(id, u.id)
        self.assertEqual(self.u.name, u.name)

    def test_save_template_assigns_id(self):
        """Saving a template should assign an id.
        """
        self.u.id = self.users.save(self.u.to_python())
        self.assertIsNotNone(self.templates.save(self.t.to_python()))

    def test_get_template_by_id(self):
        """Get a template by the assigned id.
        """
        self.u.id = self.users.save(self.u.to_python())
        id = self.templates.save(self.t.to_python())
        t = Template(**self.templates.find_one(id))
        self.assertEqual(self.t.name, t.name)
        self.assertEqual(self.t.json, t.json)

    def test_get_template_by_owner_id_and_name(self):
        """Get a template by its owner's id and its name.
        """
        self.u.id = self.users.save(self.u.to_python()) # have to do
                                                        # this to
                                                        # assign id to
                                                        # self.u
        self.templates.save(self.t.to_python())

        t = Template(**self.templates.find_one({
                    'owner.id': self.u.id,
                    'name': self.t.name,
                    'deleted': False}))
        self.assertEqual(self.t.name, t.name)
        self.assertEqual(self.t.json, t.json)

    def test_get_templates_by_owner_id_and_tag(self):
        """Get several templates by owner's id and tag name.
        """
        self.u.id = self.users.save(self.u.to_python()) # have to do
                                                        # this to
                                                        # assign id to
                                                        # self.u
        t1 = Template(owner=self.u,
                      name="first",
                      tags=['awesome'],
                      json=self.t.json)
        t2 = Template(owner=self.u,
                      name="second",
                      tags=['awesome'],
                      json=self.t.json)

        self.templates.save(self.t1.to_python())
        self.templates.save(self.t2.to_python())

        tagged = [Template(**t) for t in templates.find({
                    'owner.id': self.u.id,
                    'tag': 'awesome',
                    'deleted': False
                    })]

        self.assertEqual(2, len(tagged))


# Primitive runner!
if __name__ == '__main__':
    unittest.main()
