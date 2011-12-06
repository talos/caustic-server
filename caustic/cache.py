"""
Better user sessions through caching.
"""

# from brubeck.caching import BaseCacheStore
# from uuid import uuid4
# from datetime import datetime, timedelta

# class UserStore(BaseCacheStore):
#     """Store user's name in cache.
#     """

#     def save(user):
#         """ Save a user in the cache.  Receives a `User` object, not
#         the user name.  Returns the uuid where this user is located in cache,
#         and when the state expires.
#         """
#         uuid = uuid4()
#         expire = datetime.now() + timedelta(days=1)
#         super(UserStore, self).save(uuid, user.name, expire)

#         return uuid, expire

# user_store = UserStore()
