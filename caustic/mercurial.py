'''
Provide a python interface to mercurial.
'''

from hgapi import hgapi
import os

# The name of the template file within the repo.
TEMPLATE_FILE_NAME = 'content'

class CommitException(Exception):
    ''' This exception is thrown when a commit fails.
    '''
    pass

class Repository(object):
    ''' An object to commit, pull, and push single-file Mercurial
    repos.
    '''

    def __init__(self, base_path, user, name):
        ''' Checks base_path joined with the user and name for a repo.
        If no repo exists there, creates it with the specified user.  Otherwise,
        works with the existing repo.
        '''

        self.path = os.path.join(base_path, user, name)
        self.user = user
        self.file_path = os.path.join(self.path, TEMPLATE_FILE_NAME)

        # Create path & repo if it doesn't exist yet.
        if(not os.path.isdir(self.path)):
            os.makedirs(self.path)
            self.repo = hgapi.Repo(self.path)

            # initialize repo
            self.repo.hg_init()

            # add our single file
            with open(self.file_path, 'w') as f:
                f.write('')

            self.repo.hg_add(TEMPLATE_FILE_NAME)

        else:
            self.repo = hgapi.Repo(self.path)

    def commit(self, content, message):
        ''' Commits the specified content to this repo.
        '''

        # Truncate & write the file.
        with open(self.file_path, 'w') as f:
            f.write(content)

        try:
            self.repo.hg_commit(message, user = self.user)
        except Exception as e:
            # hgapi returns a generic exception, which is sub-optimal.
            raise CommitException(e)

    def pull(self, path, id):
        ''' Pulls the content from the specified repo.
        '''

        raise NotImplementedError, 'Pull not yet implemented'

    def get(self):
        ''' Get the latest content from this repo.
        '''

        with open(self.file_path, 'r') as f:
            return f.read()
