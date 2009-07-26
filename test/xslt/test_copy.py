########################################################################
# test/xslt/test_copy.py

import os
from amara.lib import inputsource
from xslt_support import _run_xml

module_dirname = os.path.dirname(__file__)

def test_copy_1():
    """`xsl:copy`"""
    _run_xml(
        source_xml = """<?xml version="1.0"?>
<foo a="1" b="2">
  <?foobar baz?>
  <bar/>
</foo>
""",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="foo">
  <xsl:copy/>
</xsl:template>

</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<foo/>""")

def test_copy_2():
    """identity transform"""
    _run_xml(
        source_xml = inputsource(os.path.join(module_dirname, 'addr_book1.xml')),
        source_uri = "file:" + module_dirname + "/addr_book1.xml",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet>
""",
        expected ="""<?xml version='1.0' encoding='UTF-8'?>
<?xml-stylesheet href="addr_book1.xsl" type="text/xml"?><ADDRBOOK>
    <ENTRY ID='pa'>
        <NAME>Pieter Aaron</NAME>
        <ADDRESS>404 Error Way</ADDRESS>
        <PHONENUM DESC='Work'>404-555-1234</PHONENUM>
        <PHONENUM DESC='Fax'>404-555-4321</PHONENUM>
        <PHONENUM DESC='Pager'>404-555-5555</PHONENUM>
        <EMAIL>pieter.aaron@inter.net</EMAIL>
    </ENTRY>
    <ENTRY ID='en'>
        <NAME>Emeka Ndubuisi</NAME>
        <ADDRESS>42 Spam Blvd</ADDRESS>
        <PHONENUM DESC='Work'>767-555-7676</PHONENUM>
        <PHONENUM DESC='Fax'>767-555-7642</PHONENUM>
        <PHONENUM DESC='Pager'>800-SKY-PAGEx767676</PHONENUM>
        <EMAIL>endubuisi@spamtron.com</EMAIL>
    </ENTRY>
    <ENTRY ID='vz'>
        <NAME>Vasia Zhugenev</NAME>
        <ADDRESS>2000 Disaster Plaza</ADDRESS>
        <PHONENUM DESC='Work'>000-987-6543</PHONENUM>
        <PHONENUM DESC='Cell'>000-000-0000</PHONENUM>
        <EMAIL>vxz@magog.ru</EMAIL>
    </ENTRY>
</ADDRBOOK>""")

if __name__ == '__main__':
    raise SystemExit("use nosetests")
