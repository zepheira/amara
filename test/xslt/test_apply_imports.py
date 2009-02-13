########################################################################
# test/xslt/test_apply_imports.py
from amara.test import test_main
from amara.test.xslt import xslt_test, xslt_error, filesource, stringsource
from amara.xslt import XsltError

class test_apply_imports_1(xslt_test):
    source = stringsource('<example>This is an example</example>')
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="test-apply-imports-1.xslt"/>

  <xsl:template match="example">
    <div style="border: solid red">
      <xsl:apply-imports/>
    </div>
  </xsl:template>

</xsl:stylesheet>""")
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<div style="border: solid red"><pre>This is an example</pre></div>"""


class test_apply_imports_2(xslt_test):
    source = stringsource("""<?xml version="1.0"?>
<doc><example>This is an example<inconnu/></example></doc>""")
    transform = stringsource("""<?xml version="1.0"?>
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

</xsl:stylesheet>""")
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<body><div style="border: solid red"><unknown-element>example</unknown-element></div></body>"""


class test_apply_imports_3(xslt_test):
    source = stringsource('<example>This is an example</example>')
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="test-apply-imports-1.xslt"/>

  <xsl:template match="/">
    <xsl:apply-templates mode="foo"/>
  </xsl:template>

  <xsl:template match="example" mode="foo">
    <span>main</span>
    <xsl:apply-imports/>
  </xsl:template>

</xsl:stylesheet>""")
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<span>main</span><span>imported</span>"""


class test_apply_imports_error_1(xslt_error):
    """xsl:apply-imports with xsl:param children"""
    error_code = XsltError.ILLEGAL_ELEMENT_CHILD
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
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
""")


if __name__ == '__main__':
    test_main()
