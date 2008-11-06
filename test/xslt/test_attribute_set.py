########################################################################
# test/xslt/test_attribute_set.py
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_attribute_set_1(xslt_test):
    source = stringsource('<dummy/>')
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

  <xsl:output method="xml" indent="yes"/>

  <!-- simple1 -->
  <xsl:attribute-set name="ab">
    <xsl:attribute name="a">1</xsl:attribute>
    <xsl:attribute name="b">2</xsl:attribute>
  </xsl:attribute-set>

  <!-- simple2 -->
  <xsl:attribute-set name="cd">
    <xsl:attribute name="c">3</xsl:attribute>
    <xsl:attribute name="d">4</xsl:attribute>
  </xsl:attribute-set>

  <!-- combined1 -->
  <xsl:attribute-set name="abcd" use-attribute-sets="ab cd"/>

  <!-- combined2 -->
  <xsl:attribute-set name="abcdef" use-attribute-sets="abcd">
    <xsl:attribute name="e">5</xsl:attribute>
    <xsl:attribute name="f">6</xsl:attribute>
  </xsl:attribute-set>

  <!-- combined3 (uses dups) -->
  <xsl:attribute-set name="abcdefabcdef" use-attribute-sets="ab cd abcd abcdef"/>

  <!-- combined4 (uses, overrides dups) -->
  <xsl:attribute-set name="abcdefabcdefbc" use-attribute-sets="ab cd abcd abcdef">
    <xsl:attribute name="b">B</xsl:attribute>
    <xsl:attribute name="c">C</xsl:attribute>
  </xsl:attribute-set>

  <!-- combined5 (uses, overrides dups) -->
  <xsl:attribute-set name="BC">
    <xsl:attribute name="b">B</xsl:attribute>
    <xsl:attribute name="c">C</xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="abcdefabcdefBC" use-attribute-sets="ab cd abcd abcdef BC"/>

  <!-- circular (allowed to be defined, but not used) -->
  <xsl:attribute-set name="x" use-attribute-sets="y">
    <xsl:attribute name="x">X</xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="y" use-attribute-sets="x">
    <xsl:attribute name="y">Y</xsl:attribute>
  </xsl:attribute-set>

  <xsl:template match="/">
    <results>
      <xsl:element name="simple1" use-attribute-sets="ab"/>
      <xsl:element name="simple2" use-attribute-sets="cd"/>
      <xsl:element name="combined1" use-attribute-sets="abcd"/>
      <xsl:element name="combined2" use-attribute-sets="abcdef"/>
      <xsl:element name="combined3" use-attribute-sets="abcdefabcdef"/>
      <xsl:element name="combined4" use-attribute-sets="abcdefabcdefbc"/>
      <xsl:element name="combined5" use-attribute-sets="abcdefabcdefBC"/>
    </results>
  </xsl:template>

  <xsl:template match="nevermatches">
    <xsl:element name="circular" use-attribute-sets="x"/>
  </xsl:template>

</xsl:stylesheet>
""")

    expected = """<?xml version="1.0"?>
<results>
  <simple1 a="1" b="2"/>
  <simple2 c="3" d="4"/>
  <combined1 a="1" c="3" b="2" d="4"/>
  <combined2 a="1" c="3" b="2" e="5" d="4" f="6"/>
  <combined3 a="1" c="3" b="2" e="5" d="4" f="6"/>
  <combined4 a="1" c="C" b="B" e="5" d="4" f="6"/>
  <combined5 a="1" c="C" b="B" e="5" d="4" f="6"/>
</results>
"""


if __name__ == '__main__':
    test_main()
