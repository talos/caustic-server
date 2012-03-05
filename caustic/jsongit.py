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


class JSONRepository(object):
    """
    An interface to JSON git repo.
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

    def _ref(self, name):
        """
        Returns the String ref that should point to the most recent commit for
        data of name.
        """
        return 'refs/%s/HEAD' % name

    def _last_commit(self, name):
        """
        Retrieve the last commit for dict `name`.

        Returns None if there is no last commit (it's new).
        """
        try:
            return self.repo.lookup_reference(self._ref(name))
        except KeyError:
            return None

    def _instruction(self, commit):
        """
        Returns the instruction as a dict from a Commit.
        """
        return json.loads(self.repo[commit.tree[DATA].oid].data)

    def _commit_diff(self, commit1, commit2):
        """
        Returns the json_diff between the instructions linked to two different
        commits.
        """
        instr1 = self._instruction(commit1)
        instr2 = self._instruction(commit2)

        return json_diff.Comparator().compare_dicts(instr1, instr2)

    def commit(self, name, author_sig, committer_sig, message, data, parents=None):
        """
        Commits the dict `data` to this repo.

        Defaults to the last commit for the dict of this name.
        """
        blob = self.repo.write(GIT_OBJ_BLOB, json.dumps(data))

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree = self.repo.write(GIT_OBJ_TREE, '100644 %s\x00%s' % (DATA, blob.oid))

        # Default to last commit for this if no parents specified
        if not parents:
            last_commit = self._last_commit(name)
            parents = [last_commit] if last_commit else []

        self.repo.create_commit(self._ref(name), author_sig,
                                committer_sig, message, tree, parents)

    def diff(self, name1, name2):
        """
        Compute a JSON diff between two instructions.
        """
        return self._commit_diff(self._last_commit(name1),
                                 self._last_commit(name2))

    def merge(self, author_sig, committer_sig, from_name, to_name):
        """
        Merge from_data into to_data.  This will
        succeed if from_data can be fast-forwarded, or if the
        modifications since their shared parent don't conflict.

        Returns True if the merge succeeded, False otherwise.
        """
        from_commit = self._last_commit(from_name)
        to_commit = self._last_commit(to_name)

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
                self.repo.create_reference(self._ref(to_name), to_commit.oid)
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
            merged = self._instruction(shared_parent)
            for k, v in dict(from_diff['_remove'].items() + to_diff['_remove'].items()):
                merged.pop(k)
            for k, v in dict(from_diff['_update'].items() + to_diff['_update'].items()):
                merged[k] = v
            for k, v in dict(from_diff['_append'].items() + to_diff['_append'].items()):
                merged[k] = v
            self.commit(to_name, author_sig, committer_sig, 'Auto-merge',
                        merged, [from_commit, to_commit])

    def clone(self, from_name, to_name):
        """
        Clone from_name into to_name.
        """
        self.repo.create_reference(self._ref(to_name),
                                   self._last_commit(from_name).oid)

    def get(self, name):
        """
        
        """
