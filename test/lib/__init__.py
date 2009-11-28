########################################################################
# test/lib/__init__.py

import os

class file_finder(object):
    def __init__(self, context):
        self.context = context

    def __call__(self, fname):
        stem = os.path.split(self.context)[0]
        return os.path.join(stem, fname)
        return 

#    for prefix in ("", "lib/", "test/lib/"):
#        if os.path.exists(os.path.join(prefix, filename)):
#            return prefix+filename
#    return filename

