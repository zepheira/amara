########################################################################
# test/xslt/og_20010503.py
# Oliver Graf <ograf@oli-ver-ena.de> has indentation probs with 
# ft:write-file

import tempfile
from amara.lib import iri
from amara.test.xslt.xslt_support import _run_xml

BASENAME = tempfile.mktemp()
BASENAME_URI = iri.os_path_to_uri(BASENAME)

file_expected = """<?xml version="1.0" encoding="ISO-8859-1"?>
<datatree>
  <name>%s</name>
  <what>test</what>
</datatree>"""


def test_xslt_ft_write_file_og_20010503():
    _run_xml(
        source_xml = """\
<?xml version="1.0" encoding="ISO-8859-1"?>

<test>
  <data>11</data>
  <data>12</data>
  <data>13</data>
  <data>14</data>
  <data>15</data>
</test>
""",
        transform_xml = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:exsl="http://exslt.org/common"
    extension-element-prefixes="exsl">

<xsl:output method="text" encoding="ISO-8859-1"/>

<xsl:template match="/">
  <xsl:apply-templates select="test/data"/>
</xsl:template>

<xsl:template match="data">
  <xsl:variable name="file" select="concat('%s',.,'.xml')"/>
  <exsl:document href="{$file}" method="xml" indent="yes" encoding="ISO-8859-1">
    <datatree>
      <name><xsl:value-of select="."/></name>
      <what>test</what>
    </datatree>
  </exsl:document>
</xsl:template>

</xsl:stylesheet>""" % BASENAME_URI,
        expected = "",
)

if __name__ == '__main__':
    test_main()

