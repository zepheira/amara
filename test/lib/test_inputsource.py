########################################################################
# test/xslt/test_inputsource.py

from amara.lib import inputsource, iri, treecompare

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
    filename = __file__
    for i in range(rlimit_nofile):
        try:
            sources.append(inputsource(filename))
        except:
            print "Failed after", i, "files"
            raise
