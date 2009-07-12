########################################################################
# test/xslt/test_inputsource.py

import os
from amara.lib import inputsource, iri, treecompare

module_dir = os.path.dirname(os.path.abspath(__file__))

rlimit_nofile = 300
try:
    import resource
except ImportError:
    pass
else:
    rlimit_nofile = resource.getrlimit(resource.RLIMIT_NOFILE)[0] + 10

def test_many_inputsources():
    assert rlimit_nofile < 20000, "is your file limit really that large?"

    # Amara's inputsource consumes a filehandle, in the 'stream' attribute
    # See what happens if we run out of file handles.
    sources = []
    filename = os.path.join(module_dir, "borrowed", "da_20000714_02.xslt")
    for i in range(rlimit_nofile):
        try:
            sources.append(inputsource(filename))
        except:
            print "Failed after", i, "files"
            raise
