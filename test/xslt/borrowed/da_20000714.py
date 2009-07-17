# -*- encoding: utf-8 -*-
########################################################################
# test/xslt/da_20000714.py
"""
Bug report from David Allouche (david@ansible.xlii.org)
Jul 14 2000

System: RedHat 6.2 and Debian 2.2
Python-1.5.2 4XSLT-0.9.1 4DOM-0.10.1 (from rpm or deb packages)

These are two bugs related to international caracters handling.  They
are related, since applying the "workaround" for the first "bug" cause
incorrect behaviour of the second "bug".

Actually, they may be Python bugs... Since I don't program with
Python, I can't tell.  In this case, please forward it...

Bug 1: Comments with international character can cause parse error
==================================================================

When the bug occurs:
--------------------
Input
^^^^^
cat > bug.xml << --
<?xml version="1.0"?>
<!-- é -->
<toto/>
--
4xslt.py bug.xml

Output
^^^^^^
Error Reading or Parsing XML source: unclosed token at :1:0

When the bug doesn't occur:
---------------------------
Input
^^^^^
cat > bug.xml << --
<?xml version="1.0"?>
<!-- ée -->
<toto/>
--
4xslt.py bug.xml

Output
^^^^^^
No stylesheets to process.

A workaround:
-------------
Input
^^^^^
cat > bug.xml << --
<?xml version="1.0" encoding="iso-8859-1"?>
<!-- é -->
<toto/>
--
4xslt.py bug.xml

Output
^^^^^^
No stylesheets to process.

Bug 2: International characters conversion has problems
=======================================================

When conversion is right:
-------------------------
Note that the accentuated letter must be followed by an ASCII letter
or parsing will fail.  Actually it might be wrong no to throw an error
since the encoding is not specified.

Input
^^^^^
cat > toto.xml << --
<?xml version="1.0"?>
<toto/>
--
cat > toto.xsl << --
<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="toto">
ée
</xsl:template>
</xsl:stylesheet>
--
4xslt.py bug.xml bug.xsl

Output
^^^^^^
&#233;e

When the conversion is wrong:
-----------------------------
Input
^^^^^
cat > toto.xsl << --
<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="toto">
ée
</xsl:template>
</xsl:stylesheet>
--
4xslt.py bug.xml bug.xsl

Output
^^^^^^
&#195;&#169;e
"""

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource


commonsource = stringsource("""<?xml version="1.0"?>
<toto/>
""")

class test_xslt_default_utf8_encoding_da_20000714(xslt_test):
    source = commonsource
    # This is non-well-formed XML.
    #In Python 1.52 plus XML-SIG, expat seems to deal with it by passing the data to us verbatim.
    #In Python 2.0, expat seems to silently ignore the element content with unrecognizable text
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="toto">
ée
</xsl:template>
</xsl:stylesheet>""")
    expected ="""<?xml version="1.0" encoding="UTF-8"?>

\351e
"""
    
class test_xslt_declared_iso_8859_1_encoding_da_20000714(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="toto">
ée
</xsl:template>
</xsl:stylesheet>""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>

\303\251e
"""
    
if __name__ == '__main__':
    test_main()
