# -*- encoding: utf-8 -*-
########################################################################
# test/xslt/borrowed/uo_20010503.py

# From original 4Suite cvs:
#This source doc used to bomb cDomlette just on parse, as Uche found out

import os

from amara.lib import treecompare, iri
from amara.test import test_main
from amara.test.xslt import xslt_test, stringsource

BASE_URI = iri.os_path_to_uri(os.path.abspath(__file__), attemptAbsolute=True)

common_transform = stringsource("""
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
""")

class test_xslt_uo_20010503_1(xslt_test):
  transform = common_transform

  source = stringsource("""<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include1.xi"/>
</x>
""")

  expected = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s"/>
</x>""" % iri.absolutize("include1.xi", BASE_URI)


class test_xslt_uo_20010503_2(xslt_test):
  transform = common_transform

  source = stringsource("""<?xml version='1.0'?>
  <x xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include href="include2.xi"/>
  </x>
  """)

  expected = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s">
  <foo xml:base="%s"/>
</foo>
</x>""" % (iri.absolutize("include2.xi", BASE_URI),
           iri.absolutize("include1.xi", BASE_URI))


# Determine platform line seperator for textual inclusions
f = open(os.path.join(os.path.dirname(__file__), 'include1.xi'), 'rb')
line = f.readline()
f.close()
if line.endswith(os.linesep):
    LINESEP = os.linesep.replace('\r', '&#13;')
else:
    # Assume UNIX line-ending
    LINESEP = '\n'

class test_xslt_uo_20010503_3(xslt_test):
  transform = common_transform

  source = stringsource("""<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include2.xi" parse='text'/>
</x>
""")

  expected = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
&lt;?xml version='1.0' encoding='utf-8'?&gt;%(linesep)s&lt;foo xmlns:xi="http://www.w3.org/2001/XInclude"&gt;%(linesep)s  &lt;xi:include href="include1.xml"/&gt;%(linesep)s&lt;/foo&gt;
</x>""" % {'linesep' : LINESEP}


if __name__ == '__main__':
    test_main()
