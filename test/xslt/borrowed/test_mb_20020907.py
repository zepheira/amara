########################################################################
# test/xslt/mb_20020907.py
# See 
# http://lists.fourthought.com/pipermail/4suite-dev/2002-September/000732.html

from amara.test import test_main
from amara.test.xslt.xslt_support import _run_xml

commonsource = '<?xml version="1.0" encoding="UTF-8"?>\n<dummy/>' # stringsource()
commonexpected = '<?xml version="1.0" encoding="UTF-8"?>\n'

def test_xslt_vars_1_mb_20020907():
    transform = """<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="resources/mb_20020907.xsl"/>

  <xsl:variable name="var1" select="'foo'"/>
  <xsl:variable name="var2" select="'bar'"/>
  <xsl:variable name="culprit" select="concat($var1,$var2)"/>

  <xsl:template match="/"/>

</xsl:transform>
"""
    _run_xml(
        source_xml = commonsource,
        transform_uri = __file__,
        transform_xml = transform,
        expected = commonexpected)

def test_xslt_vars_2_mb_20020907():
    transform = """<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:variable name="var1" select="'foo'"/>
  <xsl:variable name="var2" select="'bar'"/>
  <xsl:variable name="culprit" select="concat($var1,$var2)"/>

  <xsl:template match="/"/>

</xsl:transform>
"""
    _run_xml(
        source_xml = commonsource,
        transform_uri = __file__,
        transform_xml = transform,
        expected = commonexpected)

if __name__ == '__main__':
    raise SystemExit("Use nosetests")

