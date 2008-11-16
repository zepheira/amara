########################################################################
# test/xslt/mb_20020527.py

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

raise Exception, "Test not yet ported."

from Ft.Lib import Uri
INC_PATH = Uri.OsPathToUri('Xml/Xslt/Borrowed/resources/', attemptAbsolute=1)

class test_xslt_nested_imports_with_names_that_clash_across_import_precedence_mb_20020527(xslt_test):
    source = stringsource("<foo/>")
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="mb_20020527-1.xsl"/>

  <xsl:template name="i">
    <foo>import.xsl</foo>
  </xsl:template>

</xsl:stylesheet>
""")
    parameters = {}
    expected = """<?xml version="1.0" encoding="UTF-8"?>\n<out><foo>import.xsl</foo></out>"""

    def test_transform(self):
        from amara.xslt import transform
        # stylesheetAltUris=[INC_PATH],
        io = cStringIO.StringIO()
        result = transform(self.source, self.transform, output=io)
        self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

if __name__ == '__main__':
    test_main()


