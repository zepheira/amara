#!/usr/bin/env python
import unittest
import cStringIO
from amara.lib import testsupport, inputsource
from amara.xupdate import reader, XUpdateError, apply_xupdate

class test_xupdate(unittest.TestCase):
    class __metaclass__(type):
        def __init__(cls, name, bases, members):
            if '__metaclass__' not in members:
                test_method = cls.new_test_method()
                setattr(cls, 'runTest', test_method)
            return

        def new_test_method(cls):
            def test_method(self):
                source = inputsource(self.source, 'source')
                xupdate = inputsource(self.xupdate, 'xupdate-source')
                document = apply_xupdate(source, xupdate)
                return
            return test_method

# this first test is from the spec
# (http://www.xmldb.org/xupdate/xupdate-wd.html)
# "Example of Usage" section
class test_spec_1(test_xupdate):
    source = """<?xml version="1.0"?>
<addresses version="1.0">

  <address id="1">
    <fullname>Andreas Laux</fullname>
    <born day='1' month='12' year='1978'/>
    <town>Leipzig</town>
    <country>Germany</country>
  </address>

</addresses>
"""
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:insert-after select="/addresses/address[1]" >

    <xupdate:element name="address">
      <xupdate:attribute name="id">2</xupdate:attribute>
      <fullname>Lars Martin</fullname>
      <born day='2' month='12' year='1974'/>
      <town>Leizig</town>
      <country>Germany</country>
    </xupdate:element>
  </xupdate:insert-after>

</xupdate:modifications>
"""
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<addresses version='1.0'>

  <address id='1'>
    <fullname>Andreas Laux</fullname>
    <born day='1' month='12' year='1978'/>
    <town>Leipzig</town>
    <country>Germany</country>
  </address><address id='2'><fullname>Lars Martin</fullname><born day='2' month='12' year='1974'/><town>Leizig</town><country>Germany</country></address>

</addresses>"""


class test_append(test_xupdate):
    source = """<?xml version="1.0"?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
</addresses>
"""
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:append select="/addresses" child="last()">
    <xupdate:element name="address">
      <town>San Francisco</town>
    </xupdate:element>
  </xupdate:append>

</xupdate:modifications>
"""
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
<address><town>San Francisco</town></address></addresses>"""


class test_update(test_xupdate):
    source = """<?xml version="1.0"?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
  <address>
    <town>San Francisco</town>
  </address>
</addresses>
"""
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:update select="/addresses/address[2]/town">
    New York
  </xupdate:update>

</xupdate:modifications>
"""
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
  <address>
    <town>
    New York
  </town>
  </address>
</addresses>"""


class test_remove(test_xupdate):
    source = """<?xml version="1.0"?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
  <address>
    <town>San Francisco</town>
  </address>
</addresses>
"""
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:remove select="/addresses/address[1]"/>

</xupdate:modifications>
"""
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<addresses>
__
  <address>
    <town>San Francisco</town>
  </address>
</addresses>""".replace('_', ' ')


class test_attribute_append(test_xupdate):
    source = """<ftss:Container xmlns:ftss="http://xmlns.4suite.org/reserved">
  <ftss:Children/>
</ftss:Container>"""
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
  xmlns:ftss="http://xmlns.4suite.org/reserved"
  xmlns:xlink="http://www.w3.org/1999/xlink"
>
<xupdate:variable name='child-name'>FOO</xupdate:variable>
<xupdate:append select="(ftss:Repository | ftss:Container)/ftss:Children"
                child="last()">
    <ftss:ChildReference xlink:type="simple" xlink:actuate="onLoad" xlink:show="embed">
      <xupdate:attribute name='xlink:href'>
        <xupdate:value-of select='concat($child-name,";metadata")'/>
      </xupdate:attribute>
    </ftss:ChildReference>
  </xupdate:append>
</xupdate:modifications>
"""
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<ftss:Container xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:ftss='http://xmlns.4suite.org/reserved'>\n  <ftss:Children><ftss:ChildReference xlink:href='FOO;metadata' xlink:type='simple' xlink:actuate='onLoad' xlink:show='embed'/></ftss:Children>\n</ftss:Container>"""


class test_spec_2(test_xupdate):
    source = """<?xml version="1.0" encoding="utf-8"?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
</addresses>
"""
    xupdate = """<?xml version="1.0" encoding="utf-8"?>
<xupdate:modifications version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>
 <xupdate:append select="/addresses" child="last()">
   <xupdate:element name="address">
     <town>San Francisco</town>
   </xupdate:element>
 </xupdate:append>
</xupdate:modifications>
"""
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
<address><town>San Francisco</town></address></addresses>
"""

# The following was posted on SourceForge as bug #704627
# (attributes were not being appended properly)
class test_attribute_append_2(test_xupdate):
    source = """<?xml version='1.0'?>
<test><t id='t1'>one</t><t id='t2'>two</t></test>
"""
    xupdate = """<?xml version="1.0"?>
<xu:modifications version="1.0" xmlns:xu="http://www.xmldb.org/xupdate">
    <xu:append select="/test"><xu:attribute name="a1">a1v</xu:attribute></xu:append>
</xu:modifications>
"""
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<test a1="a1v"><t id="t1">one</t><t id="t2">two</t></test>"""


class test_usecase(test_xupdate):
    source = """<?xml version="1.0" encoding="UTF-8"?>
<addresses>

   <address id="1">
      <!--This is the users name-->
      <name>
         <first>John</first>
         <last>Smith</last>
      </name>
      <city>Houston</city>
      <state>Texas</state>
      <country>United States</country>
      <phone type="home">333-300-0300</phone>
      <phone type="work">333-500-9080</phone>
      <note><![CDATA[This is a new user]]></note>
   </address>

</addresses>"""
    xupdate = """<?xml version="1.0" encoding="UTF-8"?>
<xupdate:modifications version="1.0" xmlns:xupdate="http://www.xmldb.org/xupdate">
   <xupdate:append select="/addresses/address[@id = 1]/phone[@type='work']">
      <xupdate:attribute name="extension">223</xupdate:attribute>
   </xupdate:append>
</xupdate:modifications>"""
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<addresses>

   <address id="1">
      <!--This is the users name-->
      <name>
         <first>John</first>
         <last>Smith</last>
      </name>
      <city>Houston</city>
      <state>Texas</state>
      <country>United States</country>
      <phone type="home">333-300-0300</phone>
      <phone type="work" extension="223">333-500-9080</phone>
      <note><![CDATA[This is a new user]]></note>
   </address>

</addresses>"""

# rename tests based partly on SF bug #704627 and
# http://lists.fourthought.com/pipermail/4suite/2002-November/004602.html
#
class test_rename(test_xupdate):
    source = """<?xml version="1.0" encoding="utf-8"?>
<addresses version="1.0">

  <address id="1">
    <fullname>Andreas Laux</fullname>
    <born day="1" month="12" year="1978"/>
    <town>Leipzig</town>
    <country>Germany</country>
  </address>

  <address id="2">
    <fullname>Heiko Smit</fullname>
    <born day="4" month="8" year="1970"/>
    <town>Berlin</town>
    <country>Germany</country>
  </address>

  <address id="3">
    <fullname>Vincent Q. Lu</fullname>
    <born day="9" month="9" year="1990"/>
    <town>Hong Kong</town>
    <country>China</country>
  </address>

  <address id="4">
    <fullname>Michelle Lambert</fullname>
    <born day="10" month="10" year="1958"/>
    <town>Toronto</town>
    <country>Canada</country>
  </address>

</addresses>"""
    xupdate = """<?xml version="1.0" encoding="UTF-8"?>
<xupdate:modifications version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
  xmlns:my="urn:bogus:myns">

  <!-- rename of an element -->
  <xupdate:rename select="/addresses/address[@id='1']/town">city</xupdate:rename>

  <!-- rename of an attribute -->
  <xupdate:rename select="/addresses/address[@id='1']/born/@year">annum</xupdate:rename>

  <!-- rename of document element -->
  <xupdate:rename select="/addresses">info</xupdate:rename>

  <!-- rename of multiple elements -->
  <xupdate:rename select="/*/address">data</xupdate:rename>

  <!-- rename of multiple attributes (1 per element) -->
  <xupdate:rename select="/*/*/@id[. > 1 and . &lt; 4]">num</xupdate:rename>

  <!-- rename of multiple attributes (all in same element) -->
  <xupdate:rename select="/*/*[@id='4']/born/@*[name()='day' or name()='month']">zzz</xupdate:rename>

  <!-- rename of renamed element -->
  <xupdate:rename select="/info">my:info</xupdate:rename>

  <!-- insert/append and rename of multiple elements -->
  <xupdate:insert-before select="/*/*[1]/born"><xupdate:element name="new-elem"/></xupdate:insert-before>
  <xupdate:insert-before select="/*/*[2]/born"><xupdate:element name="new-elem"/></xupdate:insert-before>
  <xupdate:insert-before select="/*/*[3]/born"><xupdate:element name="new-elem"/></xupdate:insert-before>
  <xupdate:insert-before select="/*/*[4]/born"><xupdate:element name="new-elem"/></xupdate:insert-before>
  <xupdate:rename select="/*/*/new-elem">my:new-elem</xupdate:rename>
  <xupdate:append select="/*/*" child="last()"><my:another-elem/></xupdate:append>
  <xupdate:rename select="/*/*/my:another-elem">my:other-elem</xupdate:rename>
  <xupdate:insert-after select="/*/*/my:other-elem"><xupdate:element name="my:foo"/></xupdate:insert-after>
</xupdate:modifications>
"""
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<my:info xmlns:my="urn:bogus:myns" version="1.0">

  <data id="1">
    <fullname>Andreas Laux</fullname>
    <my:new-elem/><born day="1" month="12" annum="1978"/>
    <city>Leipzig</city>
    <country>Germany</country>
  <my:other-elem/><my:foo/></data>

  <data num="2">
    <fullname>Heiko Smit</fullname>
    <my:new-elem/><born day="4" month="8" year="1970"/>
    <town>Berlin</town>
    <country>Germany</country>
  <my:other-elem/><my:foo/></data>

  <data num="3">
    <fullname>Vincent Q. Lu</fullname>
    <my:new-elem/><born day="9" month="9" year="1990"/>
    <town>Hong Kong</town>
    <country>China</country>
  <my:other-elem/><my:foo/></data>

  <data id="4">
    <fullname>Michelle Lambert</fullname>
    <my:new-elem/><born zzz="10" year="1958"/>
    <town>Toronto</town>
    <country>Canada</country>
  <my:other-elem/><my:foo/></data>

</my:info>
"""

#-----------------------------------------------------------------------

class test_xupdate_error(test_xupdate):
    # trick __metaclass__ into not treating this as a test-case
    __metaclass__ = test_xupdate.__metaclass__
    source = """<?xml version="1.0"?>
<addresses>
  <address>
    <town>Los Angeles</town>
  </address>
</addresses>
"""
    @classmethod
    def new_test_method(cls):
        def format_error(error_code):
            for name, value in XUpdateError.__dict__.iteritems():
                if value == error_code:
                    error_code = 'XUpdateError.' + name
                    break
            return 'XUpdateError(%s)' % error_code
        expected = format_error(cls.error_code)
        def test_method(self):
            source = inputsource(self.source, 'source')
            xupdate = inputsource(self.xupdate, 'xupdate-error-source')
            try:
                document = apply_xupdate(source, xupdate)
            except XUpdateError, error:
                compared = format_error(error.code)
                self.assertEquals(expected, compared)
            else:
                self.fail('%s not raised' % expected)
            return
        return test_method


class test_version_missing(test_xupdate_error):
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:append select="/addresses" child="last()">
    <xupdate:element name="address">
      <town>San Francisco</town>
    </xupdate:element>
  </xupdate:append>

</xupdate:modifications>
"""
    error_code = XUpdateError.MISSING_REQUIRED_ATTRIBUTE


class test_select_missing(test_xupdate_error):
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:append child="last()">
    <xupdate:element name="address">
      <town>San Francisco</town>
    </xupdate:element>
  </xupdate:append>

</xupdate:modifications>
"""
    error_code = XUpdateError.MISSING_REQUIRED_ATTRIBUTE


class test_select_invalid(test_xupdate_error):
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:append select="/.." child="last()">
    <xupdate:element name="address">
      <town>San Francisco</town>
    </xupdate:element>
  </xupdate:append>

</xupdate:modifications>
"""
    error_code = XUpdateError.INVALID_SELECT


class test_syntax_error(test_xupdate_error):
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:append select="!/addresses" child="last()">
    <xupdate:element name="address">
      <town>San Francisco</town>
    </xupdate:element>
  </xupdate:append>

</xupdate:modifications>
"""
    error_code = XUpdateError.SYNTAX_ERROR


class test_test_missing(test_xupdate_error):
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:if>
    <xupdate:append select="/addresses" child="last()">
      <xupdate:element name="address">
        <town>San Francisco</town>
      </xupdate:element>
    </xupdate:append>
  </xupdate:if>

</xupdate:modifications>
"""
    error_code = XUpdateError.MISSING_REQUIRED_ATTRIBUTE


class test_illegal_element(test_xupdate_error):
    xupdate = """<?xml version="1.0"?>
<xupdate:modifications
  version="1.0"
  xmlns:xupdate="http://www.xmldb.org/xupdate"
>

  <xupdate:prepend select="/addresses" child="last()">
    <xupdate:element name="address">
      <town>San Francisco</town>
    </xupdate:element>
  </xupdate:prepend>

</xupdate:modifications>
"""
    error_code = XUpdateError.ILLEGAL_ELEMENT


if __name__ == '__main__':
    testsupport.test_main()
