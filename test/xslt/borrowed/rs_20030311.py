#From Robert Sanderson AKA azaroth42
from Xml.Xslt import test_harness

EXPECTED_1 = """<?xml version="1.0" encoding="UTF-8"?>\n"""


from Ft.Xml.Xslt.Processor import Processor
from Ft.Xml.InputSource import DefaultFactory

processor = Processor()
TRANSFORM_2 = """<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">
  <xsl:output method="html"/>
  <xsl:template match="/">
  <xsl:text>Starting...</xsl:text>
  <xsl:apply-templates/>
  <xsl:text>Finished.</xsl:text>
  </xsl:template>
  <xsl:template match="aaa">
  <xsl:variable name="atxt">
  <xsl:value-of select="."/>
  </xsl:variable>
  <xsl:if test="atxt='now'">
  Now!
  </xsl:if>
  </xsl:template>
</xsl:stylesheet>
"""

EXPECTED = 'Starting...Finished.'
  
def Test(tester):
    # We don't use test_harness.XsltTest and friends because they hide
    # away the API details we're testing in this module.
    # See http://bugs.4suite.org/641693
    tester.startGroup("Test multiple stylesheet invokation")
    transform = DefaultFactory.fromString(TRANSFORM_2, "http://foo.com/")
    processor.appendStylesheet(transform)

    results = ["<xml><aaa>nope</aaa></xml>",
               "<xml><aaa>now</aaa></xml>",
               "<xml><aaa>now</aaa></xml>"]

    for x in range(0,2):
        SOURCE = results[x]
        source = DefaultFactory.fromString(SOURCE, "file:bogus.xml")
        result = processor.run(source)
        tester.compare(result, EXPECTED)

    tester.groupDone()
    return

