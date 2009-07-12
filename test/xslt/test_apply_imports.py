########################################################################
# test/xslt/test_apply_imports.py
from amara.xslt import XsltError

from xslt_support import _run_xml

import os
module_name = os.path.dirname(__file__)
module_uri = "file:" + module_name + "/"

def test_apply_imports_1():
    _run_xml(
        source_xml = '<example>This is an example</example>',
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="test-apply-imports-1.xslt"/>

  <xsl:template match="example">
    <div style="border: solid red">
      <xsl:apply-imports/>
    </div>
  </xsl:template>

</xsl:stylesheet>""",
        expected = """<?xml version='1.0' encoding='UTF-8'?>
<div style="border: solid red"><pre>This is an example</pre></div>""",
        transform_uri = module_uri)


def test_apply_imports_2():
    _run_xml(
        source_xml = """<?xml version="1.0"?>
<doc><example>This is an example<inconnu/></example></doc>""",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="test-apply-imports-2.xslt"/>

  <xsl:template match="doc">
    <body>
      <xsl:apply-imports/>
    </body>
  </xsl:template>

  <xsl:template match="*">
    <unknown-element><xsl:value-of select="name()"/></unknown-element>
  </xsl:template>

</xsl:stylesheet>""",
        expected = """<?xml version='1.0' encoding='UTF-8'?>
<body><div style="border: solid red"><unknown-element>example</unknown-element></div></body>""",
        transform_uri = module_uri)


def test_apply_imports_3():
    _run_xml(
        source_xml = '<example>This is an example</example>',
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="test-apply-imports-1.xslt"/>

  <xsl:template match="/">
    <xsl:apply-templates mode="foo"/>
  </xsl:template>

  <xsl:template match="example" mode="foo">
    <span>main</span>
    <xsl:apply-imports/>
  </xsl:template>

</xsl:stylesheet>""",
        expected = """<?xml version='1.0' encoding='UTF-8'?>
<span>main</span><span>imported</span>""",
        transform_uri = module_uri)


def test_apply_imports_error_1():
    """xsl:apply-imports with xsl:param children"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="test-apply-imports-2.xslt"/>

  <xsl:template match="doc">
    <body>
      <xsl:apply-imports>
        <xsl:with-param name="border-style" select="'dotted'"/>
      </xsl:apply-imports>
    </body>
  </xsl:template>

  <xsl:template match="*">
    <unknown-element><xsl:value-of select="name()"/></unknown-element>
  </xsl:template>

</xsl:stylesheet>
""",
            expected = None,
            transform_uri = module_uri)
    except XsltError, err:
        assert err.code == XsltError.ILLEGAL_ELEMENT_CHILD
    else:
        raise AssertionError("should have failed!")


if __name__ == '__main__':
    raise SystemExit("Use nosetests")
