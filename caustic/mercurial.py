'''
Provide a python interface to mercurial.
'''

from hgapi import hgapi
import os

# The name of the template file within the repo.
TEMPLATE_FILE_NAME = 'template.json'

class Repository(object):

    def __init__(self, path, id):
        ''' Checks path for a repo with the specified id.
        If no repo exists there, creates it.  Otherwise,
        works with the existing repo.
        '''

        self.file_path = os.path.join(path, TEMPLATE_FILE_NAME)

        print file_path

        # Create path & repo if it doesn't exist yet.
        if(not os.path.isdir(path)):
            os.mkdir(path)
            self.repo = hgapi.Repo(path)

            # initialize repo
            repo.hg_init()

            # add our single file
            with(open(self.file_path, 'w')) as f:
                f.write('')
                repo.hg_add(self.file_path)

        else:
            self.repo = hgapi.Repo(path)

    def commit(self, json, message, user):
        ''' Commits the specified JSON to this repo.
        '''

        # Truncate & write the file.
        with open(self.file_path, 'w') as f:
            f.write(json)
            repo.hg_commit(message, user = user)

    def pull(self, path, id):
        ''' Pulls the JSON from the specified repo.
        '''

        raise NotImplementedError, 'Pull not yet implemented'

    def get_json(self):
        ''' Get the latest JSON from this repo.
        '''

        with open(self.file_path, 'r') as f:
            return f.read()
