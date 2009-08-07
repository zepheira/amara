########################################################################
# test/lib/__init__.py

import os

def find_file(filename):
    for prefix in ("", "lib/", "test/lib/"):
        if os.path.exists(prefix+filename):
            return prefix+filename
    return filename


