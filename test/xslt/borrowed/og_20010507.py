########################################################################
# test/xslt/og_20010507.py
# Oliver Graf <ograf@oli-ver-ena.de>:
# ft:output cdata-section-elements is not used

import tempfile
from amara.lib import iri
from amara.test.xslt.xslt_support import _run_text

FILESTEM = tempfile.mktemp()
FILESTEM_URI = iri.os_path_to_uri(FILESTEM)

file_expected_1 = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<datatree>
  <content>
    <num><![CDATA[1000]]></num>
    <str><![CDATA[test]]></str>
  </content>
  <what>test</what>
</datatree>"""

def test_xslt_cdata_section_elements_og_20010507():
    _run_text(
        source_xml = """\
<?xml version="1.0" encoding="ISO-8859-1"?>

<test>
  <data>
    <num>1000</num>
    <str>test</str>
  </data>
</test>""",
        transform_xml = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:exsl="http://exslt.org/common"
    extension-element-prefixes="exsl">

<xsl:output method="text" encoding="ISO-8859-1"/>

<xsl:template match="/">
  <xsl:variable name="file" select="'%s'"/>
  <exsl:document href="{$file}" method="xml" indent="yes" encoding="ISO-8859-1"
                 cdata-section-elements="str num">
    <datatree>
      <content><xsl:copy-of select="test/data/*"/></content>
      <what>test</what>
    </datatree>
  </exsl:document>
</xsl:template>

</xsl:stylesheet>"""%(FILESTEM_URI),
        expected = "\n"
        )
if __name__ == '__main__':
    test_main()
