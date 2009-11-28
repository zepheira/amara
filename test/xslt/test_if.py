########################################################################
# test/xslt/test_if.py

#import os
from amara.lib import inputsource
from xslt_support import _run_xml, _run_html
from amara.test import file_finder

FILE = file_finder(__file__)

#module_name = os.path.dirname(__file__)

#def find_file(filename):
#    return os.path.join(module_name, filename)

def test_if_1():
    """`xsl:if`"""
    _run_xml(
        source_xml = inputsource(FILE("addr_book1.xml")),
        transform_uri = "file:xslt/test_if.py",
        transform_xml = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:strip-space elements='*'/>

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
        <xsl:if test='not(position()=last())'><HR/></xsl:if>
  </xsl:template>

  <xsl:template match="NAME">
    <xsl:element name='TD'>
    <xsl:attribute name='ALIGN'>CENTER</xsl:attribute>
      <B><xsl:apply-templates/></B>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
""",
    expected = """<HTML>
  <HEAD>
    <META HTTP-EQUIV='Content-Type' CONTENT='text/html; charset=iso-8859-1'>
    <TITLE>Address Book</TITLE>
  </HEAD>
  <BODY>
    <TABLE>
      <TR>
        <TD ALIGN='CENTER'><B>Pieter Aaron</B></TD>
      </TR>
      <HR>
      <TR>
        <TD ALIGN='CENTER'><B>Emeka Ndubuisi</B></TD>
      </TR>
      <HR>
      <TR>
        <TD ALIGN='CENTER'><B>Vasia Zhugenev</B></TD>
      </TR>
    </TABLE>
  </BODY>
</HTML>""")


def test_if_2():
    """test text and element children of `xsl:if`"""
    _run_xml(
        source_xml = """<?xml version="1.0"?><dummy/>""",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="/">
    <boo>
      <!-- true -->
      <xsl:if test='/'>
        ( <true/> )
      </xsl:if>
      <!-- false -->
      <xsl:if test='/..'>
        ( <false/> )
      </xsl:if>
    </boo>
  </xsl:template>

</xsl:stylesheet>
""",
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<boo>\n        ( <true/> )\n      </boo>"""
        )

if __name__ == '__main__':
    raise SystemExit("use nosetests")
