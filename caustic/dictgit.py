import os
import time
import json_diff
try:
    import simplejson as json
    json; # appease the uncaring pyflakes god
except ImportError:
    import json
from pygit2 import init_repository, GIT_OBJ_BLOB, GIT_OBJ_TREE, \
                   Repository, Signature

# The name of the only blob within the tree.
DATA = 'data'

def signature(name, email):
    """
    Convenience method to generate a pygit2.Signature.
    """
    offset_sec = time.altzone if time.daylight else time.timezone
    return Signature(name, email, int(time.time()), offset_sec / 60)


class DictRepository(object):
    """
    An interface to dict git repo.
    """

    def __init__(self, path):
        """
        Initialize the repo with path.  Creates a bare repo there if none
        exists yet.
        """
        if os.path.isdir(path):
            self.repo = Repository(path)
        else:
            self.repo = init_repository(path, True) # bare repo

    def _ref(self, path):
        """
        Returns the String ref that should point to the most recent commit for
        data of path.
        """
        return 'refs/%s/HEAD' % path

    def _last_commit(self, path):
        """
        Retrieve the last commit for `path`.

        Returns None if there is no last commit (it doesn't exist).
        """
        try:
            return self.repo.lookup_reference(self._ref(path))
        except KeyError:
            return None

    def _dict(self, commit):
        """
        Returns the dict from a Commit. Returns None if no commit.
        """
        return json.loads(self.repo[commit.tree[DATA].oid].data) if commit else None

    def _commit_diff(self, commit1, commit2):
        """
        Returns the json_diff between the dicts of two arbitrary commits.
        """
        dict1, dict2 = self._dict(commit1), self._dict(commit2)

        return json_diff.Comparator().compare_dicts(dict1, dict2)

    def commit(self, path, data, author_sig, committer_sig, message, parents=None):
        """
        Commits the dict `data` to this repo.

        Defaults to the last commit for the dict of this path.
        """
        if not isinstance(data, dict):
            raise ValueError('Cannot commit non-dict values.')

        blob = self.repo.write(GIT_OBJ_BLOB, json.dumps(data))

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree = self.repo.write(GIT_OBJ_TREE, '100644 %s\x00%s' % (DATA, blob.oid))

        # Default to last commit for this if no parents specified
        if not parents:
            last_commit = self._last_commit(path)
            parents = [last_commit] if last_commit else []

        self.repo.create_commit(self._ref(path), author_sig,
                                committer_sig, message, tree, parents)

    def diff(self, path1, path2):
        """
        Compute a JSON diff between two instructions.
        """
        return self._commit_diff(self._last_commit(path1),
                                 self._last_commit(path2))

    def merge(self, author_sig, committer_sig, from_path, to_path):
        """
        Merge from_data into to_data.  This will
        succeed if from_data can be fast-forwarded, or if the
        modifications since their shared parent don't conflict.

        Returns True if the merge succeeded, False otherwise.
        """
        from_commit = self._last_commit(from_path)
        to_commit = self._last_commit(to_path)

        # No difference
        if from_commit.oid == to_commit.oid:
            return True

        # Test if a fast-forward is possible
        parent = to_commit
        to_parents = []
        while len(parent.parents) == 1:
            parent = parent.parents[0]
            to_parents.append(parent.oid)
            # No conflicting commits, fast forward this sucka by moving the ref
            if parent.oid == from_commit.oid:
                self.repo.create_reference(self._ref(to_path), to_commit.oid)
                return True

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        shared_parent = None
        for to_parent in to_parents:
            parent = from_commit
            while len(parent.parents) == 1:
                parent = parent.parents[0]
                if parent.oid == to_parent.oid:
                    shared_parent = parent
                    break
            if shared_parent:
                break
        if not shared_parent:
            return False # todo warn there's no shared parent

        # Now, see if the diffs conflict
        from_diff = self._commit_diff(shared_parent, from_commit)
        to_diff = self._commit_diff(shared_parent, to_commit)
        conflicts = {}
        for from_mod_type, from_mods in from_diff:
            for to_mod_type, to_mods in to_diff:
                for from_mod_key, from_mod_value in from_mods:
                    if from_mod_key in to_mods:
                        to_mod_value = to_mods[from_mod_key]
                        # if the mod type is the same, it's OK if the actual
                        # modification was the same.
                        if from_mod_type == to_mod_type:
                            if from_mod_value == to_mods[from_mod_key]:
                                pass
                            else:
                                conflicts[from_mod_key] = {
                                    'from': { from_mod_type: from_mod_value },
                                    'to'  : { to_mod_type: to_mod_value }
                                }
                        # if the mod type was not the same, it's a conflict no
                        # matter what
                        else:
                            conflicts[from_mod_key] = {
                                'from': { from_mod_type: from_mod_value },
                                'to'  : { to_mod_type: to_mod_value }
                            }

        # No-go, the user's gonna have to figure this one out
        if len(conflicts):
            return False
        # Sweet. we can apply all the diffs.
        else:
            merged = self._dict(shared_parent)
            for k, v in dict(from_diff['_remove'].items() + to_diff['_remove'].items()):
                merged.pop(k)
            for k, v in dict(from_diff['_update'].items() + to_diff['_update'].items()):
                merged[k] = v
            for k, v in dict(from_diff['_append'].items() + to_diff['_append'].items()):
                merged[k] = v
            self.commit(to_path, author_sig, committer_sig, 'Auto-merge',
                        merged, [from_commit, to_commit])

    def clone(self, from_path, to_path):
        """
        Clone from_path into to_path.  Raises a KeyError if from_path does not
        exist, and a ValueError if to_path already already exists.
        """
        if self._last_commit(to_path):
            raise ValueError('Cannot clone to %s, there is already a dict there.' % to_path)
        if self._last_commit(from_path):
            self.repo.create_reference(self._ref(to_path),
                                       self._last_commit(from_path).oid)
        else:
            raise KeyError('Cannot clone %s, there is no dict there.' % from_path)

    def get(self, path):
        """
        Retrieve the most recent dict at path.  Returns None if there is none.
        """
        return self._dict(self._last_commit(path))
