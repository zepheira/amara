import amara
from itertools import chain
from amara import bindery
import time
import datetime
import sys

N = 5000

SIMPLEDOC = ''.join(chain(['<a>'], [ '<b/>' for i in xrange(N) ], ['</a>']))
ATTRDOC = ''.join(chain(['<a>'], [ "<b c='%i'/>"%i for i in xrange(N) ], ['</a>']))


def timeit(f, *args):
    count = 1
    while 1:
        t1 = time.time()
        for x in range(count):
            result = f(*args)
        t2 = time.time()
        dt = t2-t1
        if dt >= 0.1:
            break
        count *= 10

    best = [dt]

    for i in "12":
        t1 = time.time()
        for x in range(count):
            result = f(*args)
        t2 = time.time()
        best.append(t2-t1)

    return result, min(best)/count * 1000 # in ms

#EXERCISE 1: Testing speed of parse
def amara_parse1():
    result, dt = timeit(amara.parse, SIMPLEDOC)
    return dt

#EXERCISE 2: Parse once and test speed of XPath using descendant-or-self, with large result
def amara_parse2():
    doc = amara.parse(SIMPLEDOC)
    result, dt = timeit(doc.xml_select, u'//b')
    assert len(result) == N
    return dt

#EXERCISE 3: Parse once and test speed of XPath using descendant-or-self, with empty result
def amara_parse3():
    doc = amara.parse(SIMPLEDOC)
    result, dt = timeit(doc.xml_select, u'//c')
    assert len(result) == 0
    return dt

#EXERCISE 4: Testing speed of parse, part 2
def amara_parse4():
    result, dt = timeit(amara.parse, ATTRDOC)
    return dt

#EXERCISE 5: Parse once and test speed of XPath using descendant-or-self with attribute predicate (small result)
def amara_parse5():
    doc = amara.parse(ATTRDOC)
    result, dt = timeit(doc.xml_select, u"//b[@c='10']")
    assert len(result) == 1
    return dt

#EXERCISE 1: Testing speed of parse
def bindery_parse1():
    result, dt = timeit(bindery.parse, SIMPLEDOC)
    return dt

#EXERCISE 2: Parse once and test speed of XPath using descendant-or-self, with large result
def bindery_parse2():
    doc = bindery.parse(SIMPLEDOC)
    result, dt = timeit(doc.xml_select, u'//b')
    assert len(result) == N
    return dt

#EXERCISE 3: Parse once and test speed of XPath using descendant-or-self, with empty result
def bindery_parse3():
    doc = bindery.parse(SIMPLEDOC)
    result, dt = timeit(doc.xml_select, u'//c')
    assert len(result) == 0
    return dt

#EXERCISE 4: Testing speed of parse, part 2
def bindery_parse4():
    result, dt = timeit(bindery.parse, ATTRDOC)
    return dt

#EXERCISE 5: Parse once and test speed of XPath using descendant-or-self with attribute predicate (small result)
def bindery_parse5():
    doc = bindery.parse(ATTRDOC)
    result, dt = timeit(doc.xml_select, u"//b[@c='10']")
    assert len(result) == 1
    return dt

row_names = [
    "Parse once (no attributes)",
    " descendant-or-self, many results",
    " descendant-or-self, no results",
    "Parse once (with attributes)",
    " descendant-or-self w/ attribute, 1 result",
    ]
colwidth = max(len(name) for name in row_names)
header_format = "%" + str(colwidth) + "s   %10s  %10s"
row_format = "%-" + str(colwidth) + "s:" + " %8.2f ms  %8.2f ms"

amara_parse_tests = [amara_parse1, amara_parse2, amara_parse3, amara_parse4, amara_parse5]
bindery_parse_tests = [bindery_parse1, bindery_parse2, bindery_parse3, bindery_parse4,
                       bindery_parse5]

now = datetime.datetime.now().isoformat().split("T")[0]

class TextReporter(object):
    def start(self):
        print "Parse and select timings for Amara", amara.__version__
        print "Started on %s. Reporting best of 3 tries" % (now,)
    def header(self):
        print header_format % ("", "core tree", "bindery")
    def row(self, cols):
        print row_format % cols

class MarkupReporter(object):
    def __init__(self):
        self.exercise = 1
    def start(self):
        print "== Amara", amara.__version__, "on", now, "=="
    def header(self):
        print "||Exercise||N||Amara 2.x core tree||Amara 2.x bindery||"
    def row(self, cols):
        label, dt1, dt2 = cols
        print "||%d||%d||%.2f msec||%.2f msec||" % (self.exercise, N,
                                                    dt1, dt2)
        self.exercise += 1

def report(reporter):
    reporter.start()
    reporter.header()
    for (label, f1, f2) in zip(row_names, amara_parse_tests, bindery_parse_tests):
        reporter.row( (label, f1(), f2()) )

def main():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("--markup", dest="markup", action="store_true")
    parser.add_option("--profile", dest="profile")
    options, args = parser.parse_args()
    if options.profile:
        # See if I can find the function.
        func = globals()[options.profile]
        # 
        import profile, pstats
        profile.run(options.profile + "()", "profile.out")
        p = pstats.Stats("profile.out")
        p.strip_dirs().sort_stats(-1).print_stats()
        print "Profile saved in 'profile.out'"
        return
    if options.markup:
        reporter = MarkupReporter()
    else:
        reporter = TextReporter()
    report(reporter)
    

if __name__ == "__main__":
    main()
