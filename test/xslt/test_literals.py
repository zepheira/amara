########################################################################
# test/xslt/test_literals.py
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_literals_1(xslt_test):
    source = stringsource("""<customer id="uo">Uche Ogbuji</customer>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="customer">
    <wrapper>
    <customer id="{@id}" xmlns="http://spam.com">
      <xsl:element name="{substring-before(., ' ')}" namespace="http://eggs.com">Eggs</xsl:element>
      <name><xsl:value-of select="."/></name>
    </customer>
    </wrapper>
  </xsl:template>

</xsl:stylesheet>
""")
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<wrapper><customer id='uo' xmlns='http://spam.com'><Uche xmlns='http://eggs.com'>Eggs</Uche><name>Uche Ogbuji</name></customer></wrapper>"""


class test_literals_2(xslt_test):
    source = stringsource("""<?xml version="1.0"?><foo/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

     <xsl:output indent="no" encoding="us-ascii"/>

     <xsl:template match="/">
       <result>
         <text>
           <xsl:text/>
         </text>
         <value>
           <xsl:value-of select="''"/>
         </value>
       </result>
     </xsl:template>

</xsl:stylesheet>
""")
    expected = """<?xml version='1.0' encoding='us-ascii'?>
<result><text/><value/></result>"""


if __name__ == '__main__':
    test_main()
