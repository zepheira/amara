########################################################################
# test/xslt/test_elem_attr.py

import os
from amara.lib import inputsource
from xslt_support import _run_html, _run_xml

module_dirname = os.path.dirname(__file__)

def test_elem_attr_1():
    """`xsl:element` and `xsl:attribute` instantiation"""
    _run_html(
        source_xml = inputsource(os.path.join(module_dirname, 'addr_book1.xml')),
        source_uri = "file:" + module_dirname + "/addr_book1.xml",
        transform_xml = """<?xml version="1.0"?>
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">

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
    </xsl:element>
  </xsl:template>

</xsl:transform>""",
        expected = """<HTML>
  <HEAD>
    <META HTTP-EQUIV='Content-Type' CONTENT='text/html; charset=iso-8859-1'>
    <TITLE>Address Book</TITLE>
  </HEAD>
  <BODY>
    <TABLE>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Pieter Aaron</B></TD>
      </TR>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Emeka Ndubuisi</B></TD>
      </TR>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Vasia Zhugenev</B></TD>
      </TR>

    </TABLE>
  </BODY>
</HTML>""")


def test_elem_attr_2():
    """`xsl:element` with namespaces"""
    _run_xml(
        source_xml = '<?xml version="1.0"?><dummy/>',
        transform_xml = """<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="no"/>

  <xsl:template match="/">
    <result>
      <!-- should be in explicitly specified namespace --> 
      <xsl:element name="xse-ns" namespace="http://foo/bar"/>
      <xsl:element name="xse-empty-ns" namespace=""/>
      <!-- should be in default namespace (empty) -->
      <xsl:element name="xse"/>
      <lre-ns xmlns="http://stuff">
        <!-- should be in explicitly specified namespace -->   
        <xsl:element name="xse-ns" namespace="http://foo/bar"/>
        <xsl:element name="xse-empty-ns" namespace=""/>
        <!-- should be in http://stuff namespace -->
        <xsl:element name="xse"/>
      </lre-ns>
    </result>
  </xsl:template>

</xsl:transform>""",
        expected = """<?xml version='1.0' encoding='UTF-8'?>
<result><xse-ns xmlns='http://foo/bar'/><xse-empty-ns/><xse/><lre-ns xmlns='http://stuff'><xse-ns xmlns='http://foo/bar'/><xse-empty-ns xmlns=''/><xse/></lre-ns></result>"""
        )

def test_elem_attr_3():
    """`xsl:attribute` with namespaces"""
    _run_xml(
        source_xml = '<?xml version="1.0"?><dummy/>',
        transform_xml = """<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="no"/>   

  <xsl:template match="/">
    <result>
      <lre>
        <xsl:attribute name="att">foo</xsl:attribute>
        <!-- should be in explicitly specified namespace -->
        <xsl:attribute name="att-ns" namespace="http://crud">foo</xsl:attribute>
        <xsl:attribute name="att-empty-ns" namespace="">foo</xsl:attribute>
      </lre>
      <lre xmlns="http://stuff">
        <!-- ns should be none/empty; should *not* inherit http://stuff -->
        <xsl:attribute name="att">foo</xsl:attribute>
        <!-- should be in explicitly specified namespace -->
        <xsl:attribute name="att-ns" namespace="http://crud">foo</xsl:attribute>
        <xsl:attribute name="att-empty-ns" namespace="">foo</xsl:attribute>
      </lre>
      <lre xmlns:pre="http://prefix">
        <!-- ns should the one bound to pre: -->
        <xsl:attribute name="pre:att">foo</xsl:attribute>
        <!-- explicit namespace should override the one bound to pre: -->
        <xsl:attribute name="pre:att-ns" namespace="http://crud">foo</xsl:attribute>
        <xsl:attribute name="pre:att-empty-ns" namespace="">foo</xsl:attribute>
      </lre>
    </result>
  </xsl:template>

</xsl:transform>""",
        expected = """<?xml version='1.0' encoding='UTF-8'?>
<result><lre xmlns:org.4suite.4xslt.ns0='http://crud' att-empty-ns='foo' att='foo' org.4suite.4xslt.ns0:att-ns='foo'/><lre xmlns='http://stuff' xmlns:org.4suite.4xslt.ns0='http://crud' att-empty-ns='foo' att='foo' org.4suite.4xslt.ns0:att-ns='foo'/><lre xmlns:org.4suite.4xslt.ns0='http://crud' xmlns:pre='http://prefix' pre:att='foo' att-empty-ns='foo' org.4suite.4xslt.ns0:att-ns='foo'/></result>"""
        )

if __name__ == '__main__':
    raise SystemExit("use nosetests")
