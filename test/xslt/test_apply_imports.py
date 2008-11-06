########################################################################
# test/xslt/test_elem_attr.py
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_apply_imports_1(xslt_test):
    source = stringsource('<example>This is an example</example>')
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet id="main" version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >

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
<xsl:stylesheet id="main" version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >

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


if __name__ == '__main__':
    test_main()
