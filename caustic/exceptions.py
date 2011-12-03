'''
Exceptions for caustic.
'''

class CausticException(Exception):
    ''' Parent class for caustic exceptions.
    '''

    def __init__(self, code = 500, message = "There was an error"):
        self.code = code
        self.message = message

class NoTemplateException(CausticException):
    ''' This exception is thrown when we hit a missing template.
    '''

    def __init__(self, user, name):
        code    = 404
        message = "Template '%s' not found for user '%s'." % user, name
        super(NoTemplateException, self).__init__(code, message)
