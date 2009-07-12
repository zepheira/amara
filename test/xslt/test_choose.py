########################################################################
# test/xslt/test_choose.py

import os
from xslt_support import _run_html
from amara.lib import inputsource

module_name = os.path.dirname(__file__)


def test_choose_1():
    """`xsl:choose"""
    _run_html(
        source_xml = inputsource(os.path.join(module_name, "addr_book1.xml")),
        source_uri = "file:" + module_name + "/addr_book1.xml",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">
  <xsl:output method='html'/>
  <xsl:template match="/">
    <HTML>
    <HEAD><TITLE>Address Book</TITLE>
    </HEAD>
    <BODY>
    <TABLE><xsl:apply-templates/></TABLE>
    </BODY>
    </HTML>
  </xsl:template>

  <xsl:template match="ENTRY">
    <xsl:element name='TR'>
      <xsl:apply-templates select='NAME'/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="NAME">
    <xsl:element name='TD'>
    <xsl:attribute name='ALIGN'>CENTER</xsl:attribute>
      <B><xsl:apply-templates/></B>
      <xsl:choose>
        <xsl:when test="text()='Pieter Aaron'">: Employee 1</xsl:when>
        <xsl:when test="text()='Emeka Ndubuisi'">: Employee 2</xsl:when>
        <xsl:otherwise>: Other Employee</xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
""",
    expected ="""<HTML>
  <HEAD>
    <meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'>
    <TITLE>Address Book</TITLE>
  </HEAD>
  <BODY>
    <TABLE>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Pieter Aaron</B>: Employee 1</TD>
      </TR>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Emeka Ndubuisi</B>: Employee 2</TD>
      </TR>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Vasia Zhugenev</B>: Other Employee</TD>
      </TR>

    </TABLE>
  </BODY>
</HTML>""")

if __name__ == '__main__':
    raise SystemExit("use nosetests")
