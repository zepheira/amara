import os
from Xml.Xslt import test_harness
from Ft.Lib import Uri
from Ft.Xml.InputSource import DefaultFactory
from Ft.Xml.Lib import TreeCompare
from Ft.Xml.Xslt import Processor, Error

uri = Uri.OsPathToUri(os.path.abspath(__file__))

tests = []

title = 'PI after prolog'
source = """<?xml version="1.0" encoding="utf-8"?><dummy/><?xml-stylesheet href="mb_20030915.xslt"?>"""
result = None
tests.append((title, source, result, Error.NO_STYLESHEET))


title = 'PI with no type'
source = """<?xml version="1.0" encoding="utf-8"?><?xml-stylesheet href="mb_20030915.xslt"?><dummy/>"""
result = None
tests.append((title, source, result, Error.NO_STYLESHEET))

title = 'PI with type="text/xsl"'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="text/xsl" href="mb_20030915.xslt"?>
<dummy/>"""
result = None
tests.append((title, source, result, Error.NO_STYLESHEET))

title = 'PI with type="application/xslt+xml"'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915.xslt"?>
<dummy/>"""
result = """<dummy/>"""
tests.append((title, source, result))

title = 'import order when 2 PIs (1)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915.xslt"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915a.xslt"?>
<dummy/>"""
result = """<a><dummy/></a>"""
tests.append((title, source, result))

title = 'import order when 2 PIs (2)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915a.xslt"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915.xslt"?>
<dummy/>"""
result = """<dummy/>"""
tests.append((title, source, result))

title = '2 alt PIs only; no media; different types (1)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet alternate="yes" type="application/xslt+xml" href="mb_20030915a.xslt"?>
<?xml-stylesheet alternate="yes" type="application/xml" href="mb_20030915.xslt"?>
<dummy/>"""
# type differences are ignored; both are considered to be at the same level
# since both are alternate="yes" we just use first one
result = """<a><dummy/></a>"""
tests.append((title, source, result))

title = '2 alt PIs only; no media; different types (2)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet alternate="yes" type="application/xml" href="mb_20030915.xslt"?>
<?xml-stylesheet alternate="yes" type="application/xslt+xml" href="mb_20030915a.xslt"?>
<dummy/>"""
# type differences are ignored; both are considered to be at the same level
# since both are alternate="yes" we just use first one
result = """<dummy/>"""
tests.append((title, source, result))

title = '1 PI + 1 alt PI; no media; same type'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915.xslt"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915a.xslt" alternate="yes"?>
<dummy/>"""
result = """<dummy/>""" # the non-alternate one should be selected
tests.append((title, source, result))

title = '1 PI + 1 alt PI; no media; different types (1)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="application/xml" href="mb_20030915.xslt"?>
<?xml-stylesheet alternate="yes" type="application/xslt+xml" href="mb_20030915a.xslt"?>
<dummy/>"""
# type differences are ignored; both are considered to be at the same level
# but we give preference to the one that's not alternate="yes"
result = """<dummy/>"""
tests.append((title, source, result))

title = '1 PI + 1 alt PI; no media; different types (2)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet alternate="yes" type="application/xslt+xml" href="mb_20030915a.xslt"?>
<?xml-stylesheet type="application/xml" href="mb_20030915.xslt"?>
<dummy/>"""
# type differences are ignored; both are considered to be at the same level
# but we give preference to the one that's not alternate="yes"
result = """<dummy/>"""
tests.append((title, source, result))

title = '1 PI + 1 alt PI; no media; different types (3)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet type="text/xsl" href="mb_20030915.xslt"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915a.xslt" alternate="yes"?>
<dummy/>"""
result = """<a><dummy/></a>""" # because text/xsl will be ignored
tests.append((title, source, result))

title = '1 PI + 2 alt PIs; different media; no preference'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet media="screen" type="application/xslt+xml" href="mb_20030915a.xslt" alternate="yes"?>
<?xml-stylesheet media="mobile" type="application/xslt+xml" href="mb_20030915b.xslt" alternate="yes"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915.xslt"?>
<dummy/>"""
result = """<dummy/>""" # the one with no media should be selected
tests.append((title, source, result))


title = '1 PI + 2 alt PIs; different media; preference (1)'
source = """<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet media="screen" type="application/xslt+xml" href="mb_20030915a.xslt" alternate="yes"?>
<?xml-stylesheet media="mobile" type="application/xslt+xml" href="mb_20030915b.xslt" alternate="yes"?>
<?xml-stylesheet type="application/xslt+xml" href="mb_20030915.xslt"?>
<dummy/>"""
result = """<b><dummy/></b>""" # the one with the matching preference should be selected
media_pref = 'mobile'
tests.append((title, source, result, None, media_pref))

title = '1 PI + 2 alt PIs; different media; preference (2)'
result = """<a><dummy/></a>""" # the one with the matching preference should be selected
media_pref = 'screen'
tests.append((title, source, result, None, media_pref))

def Test(tester):
    tester.startGroup('pick stylesheet from xml-stylesheet PIs')
    for tup in tests:
        (title_st, source_st, expected_st) = tup[:3]
        errcode = None
        media = None
        if len(tup) > 3:
            errcode = tup[3]
        if len(tup) > 4:
            media = tup[4]
        expected = expected_st or ''
        source = test_harness.FileInfo(string=source_st, baseUri=uri)
        if media:
            proc = Processor.Processor()
            proc.mediaPref = media
            tester.startTest(title_st)
            isrc = DefaultFactory.fromString(source_st, uri)
            result = proc.run(isrc, ignorePis=0)
            tester.compare(expected_st, result, func=TreeCompare.TreeCompare)
            tester.testDone()
            del proc, isrc, result
        else:
            test_harness.XsltTest(tester, source, [], expected,
                                  exceptionCode=errcode,
                                  title=title_st, ignorePis=0)
    tester.groupDone()
    return
