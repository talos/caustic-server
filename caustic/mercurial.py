"""Class to handle single-file Mercurial repos with a single user.
"""

import os
from hgapi import hgapi

# The name of the template file within the repo.
TEMPLATE_FILE_NAME = 'content'


class CommitException(Exception):
    """This exception is thrown when a commit fails.
    """
    pass


class NoRepositoryException(Exception):
    """This exception is thrown when a repo does not exist.
    """
    pass


class AlreadyExistsException(Exception):
    """This exception is thrown when a repo already exists with the
    same name and owner.
    """
    pass


class Repository(object):
    """
    An object to commit, pull, and push single-file Mercurial repos.
    """

    def __init__(self, base_path, user, name, create=True):
        """Checks base_path joined with the user and name for a repo.
        If no repo exists there, creates it with the specified user.
        Otherwise, works with the existing repo.
        """

        self.base_path = base_path
        self.owner = user
        self.name = name
        path = os.path.join(base_path, user, name)
        self.file_path = os.path.join(path, TEMPLATE_FILE_NAME)

        if(os.path.isdir(path)):
            self.repo = hgapi.Repo(path)
        elif(create is True):
            self.repo = self._create_repo(path)
        else:
            raise NoRepositoryException(
                "No repo %s for user %s" % (name, user))

    def _create_repo(self, path):
        """
        Initialize a new repo at `path`.
        """
        os.makedirs(path)

        repo = hgapi.Repo(path)
        repo.hg_init()
        # add our single (blank) file
        with open(self.file_path, 'w') as f:
            f.write('')

        repo.hg_add(TEMPLATE_FILE_NAME)
        return repo

    def commit(self, content, message):
        """
        Commits the specified content to this repo.
        """
        # Truncate & write the file.
        with open(self.file_path, 'w') as f:
            f.write(content)

        try:
            self.repo.hg_commit(message, user=self.owner)
        except Exception as e:
            # hgapi returns a generic exception, which is sub-optimal.
            raise CommitException(e)

    def pull(self, from_repo):
        """
        Pulls from the specified mercurial.Repository.
        """
        from_path = os.path.abspath(from_repo.repo.path)  # a bit hacky.
        self.repo.hg_command('pull', from_path)
        self.repo.hg_command('update')

    def get(self):
        """
        Get the latest content from this repo.
        """
        return open(self.file_path, 'r').read()

    def clone(self, user, name):
        """
        Clone this repo into `name` for `user`.  Returns the cloned
        repo.  Raises an AlreadyExistsException if a user clones their
        own repo and doesn't specify a new name.
        """
        if (user == self.owner) and (name == self.name):
            raise AlreadyExistsException("You must specify a new name"
                                         " to clone your own repo.")

        cloned = Repository(self.base_path, user, name)
        cloned.pull(self)
        return cloned
