########################################################################
# test/xslt/jk_20050406.py
# See http://bugs.4suite.org/1180509

import tempfile, os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib.Uri import OsPathToUri

fname = tempfile.mktemp()
furi = OsPathToUri(fname)

commonsource = stringsource("<dummy/>")

commontransform = """<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:exsl="http://exslt.org/common"
extension-element-prefixes="exsl"
exclude-result-prefixes="exsl">

<xsl:output method="html" indent="no"/>

<xsl:param name="URL" select="'%s'"/>

<xsl:template match="/">
<exsl:document href="{$URL}"
method ="html"
version ="-//W3C//DTD XHTML 1.1//EN"

doctype-public="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
indent="%s">
<html>
<head>
<title>test</title>
</head>
<body>
<p>hello world</p>
</body>
</html>
</exsl:document>
</xsl:template>

</xsl:stylesheet>"""

class test_xslt_exsl_document_jk_20050406(xslt_test):
    source = commonsource
    transform = ""
    parameters = {}
    expected = ""

    def test_transform(self):
        # Preliminary, populate file with unindented HTML
        from amara.xslt import transform
        io = cStringIO.StringIO()
        self.transform = stringsource(commontransform%(furi, "no"))
        result = transform(self.source, self.transform, output=io)
        self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        open(fname, 'w').write(io.getvalue())

class test_xslt_exsl_document_and_no_indent_2_jk_20050406(xslt_test):
    source = commonsource
    transform = ""
    parameters = {}
    expected = '<!DOCTYPE html PUBLIC "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n<html><head><meta content="text/html; charset=iso-8859-1" http-equiv="Content-Type"><title>test</title></head><body><p>hello world</p></body></html>'

    def test_transform(self):
        # Subsequent, read file and compare
        from amara.xslt import transform
        self.assert_(os.path.exists(fname))
        file = open(fname, 'r')
        fcontent = file.read()
        file.close()
        self.assert_(treecompare.html_compare(self.expected, fcontent))
        os.unlink(fname)
        
        # Re-populate file, with indented HTML
        io = cStringIO.StringIO()
        self.transform = stringsource(commontransform%(furi, "yes"))
        result = transform(self.source, self.transform, output=io)
        open(fname, 'w').write(io.getvalue())
        self.assert_(treecompare.html_compare(self.expected, io.getvalue()))

class test_xslt_exsl_document_with_indent_jk_20050406(xslt_test):
    source = commonsource
    transform = ""
    parameters = {}
    expected = '<!DOCTYPE html PUBLIC "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n<html>\n  <head>\n    <meta content="text/html; charset=iso-8859-1" http-equiv="Content-Type">\n    <title>test</title>\n  </head>\n  <body>\n    <p>hello world</p>\n  </body>\n</html>'

    def test_transform(self):
        # Subsequent, read file and compare
        self.assertEquals(True, os.path.exists(fname))
        file = open(fname, 'r')
        fcontent = file.read()
        file.close()
        self.assert_(treecompare.html_compare(self.expected, fcontent))
        os.unlink(fname)

if __name__ == '__main__':
    test_main()
