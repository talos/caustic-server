# """
# Exceptions for caustic.
# """

# class CausticException(Exception):
#     """Parent class for caustic exceptions.
#     """

#     def __init__(self, code = 500, message = "There was an error"):
#         self.code = code
#         self.message = message


# class NoTemplateException(CausticException):
#     """This exception is thrown when we hit a missing template.
#     """

#     def __init__(self, user, name):
#         super(NoTemplateException, self).__init__(
#             404,
#             "Template '%s' not found for user '%s'." % (user, name))


# class NoUserException(CausticException):
#     """This exception is thrown when a user doesn't exist.
#     """

#     def __init__(self, user):
#         super(NoUserException, self).__init(
#             400,
#             message = "User %s does not exist." % user))


# class NoJSONException(CausticException):
#     """This exception is thrown when the user doesn't specify any JSON when
#     updating a template.
#     """

#     def __init__(self):
#         super(CausticException, self).__init(
#             400,
#             message = "You must provide JSON."))


# class BadSessionException(CausticException):
#     """This exception is thrown when a user can't be retrieved from a session
#     cookie.
#     """

#     def __init__(self):
#         super(CausticException, self).__init(
#             500,
#             message = "Session missing, please log in."))
