########################################################################
# test/xslt/test_message.py
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_message_1(xslt_test):
    """<xsl:message> in top-level variable"""
    source = filesource("""addr_book1.xml""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml"/>

  <xsl:variable name="foo">
    <bar>world</bar>
    <xsl:message terminate="no">Legal xsl:message in top-level variable template</xsl:message>
  </xsl:variable>

  <xsl:template match="/">
    <result>hello</result>
  </xsl:template>

</xsl:stylesheet>
""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>"""
    messages = """STYLESHEET MESSAGE:
Legal xsl:message in top-level variable template
END STYLESHEET MESSAGE
"""

class test_message_2(xslt_test):
    """<xsl:message> in template body"""
    source = filesource("""addr_book1.xml""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml"/>

  <xsl:template match="/">
    <result>hello</result>
    <xsl:message terminate="no">Legal xsl:message in regular template body</xsl:message>
  </xsl:template>

</xsl:stylesheet>
""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>"""
    messages = """STYLESHEET MESSAGE:
Legal xsl:message in regular template body
END STYLESHEET MESSAGE
"""

class test_message_3(xslt_test):
    """xsl:message deep in stylesheet processing"""
    source = filesource("""addr_book1.xml""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="/">
    <HTML>
    <HEAD><TITLE>Address Book</TITLE>
    </HEAD>
    <BODY>
    <TABLE><xsl:apply-templates/></TABLE>
    </BODY>
    </HTML>
  </xsl:template>

  <xsl:template match="ENTRY">
    <xsl:element name='TR'>
      <xsl:apply-templates select='NAME'/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="NAME">
    <xsl:element name='TD'>
      <xsl:attribute name='ALIGN'>CENTER</xsl:attribute>
      <xsl:message>We're in the thick of processing NAME elements</xsl:message>
      <B><xsl:apply-templates/></B>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
""")
    expected = """<HTML>
  <HEAD>
    <META HTTP-EQUIV='Content-Type' CONTENT='text/html; charset=iso-8859-1'>
    <TITLE>Address Book</TITLE>
  </HEAD>
  <BODY>
    <TABLE>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Pieter Aaron</B></TD>
      </TR>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Emeka Ndubuisi</B></TD>
      </TR>
\x20\x20\x20\x20
      <TR>
        <TD ALIGN='CENTER'><B>Vasia Zhugenev</B></TD>
      </TR>

    </TABLE>
  </BODY>
</HTML>"""
    messages = """STYLESHEET MESSAGE:
We're in the thick of processing NAME elements
END STYLESHEET MESSAGE
STYLESHEET MESSAGE:
We're in the thick of processing NAME elements
END STYLESHEET MESSAGE
STYLESHEET MESSAGE:
We're in the thick of processing NAME elements
END STYLESHEET MESSAGE
"""

class test_message_4(xslt_test):
    """<xsl:message> in XML form"""
    source = filesource("""addr_book1.xml""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml"/>

  <xsl:variable name="foo">
    <bar>world</bar>
    <xsl:message terminate="no"><msg>XML <code>xsl:message</code> in top-level variable template</msg></xsl:message>
  </xsl:variable>

  <xsl:template match="/">
    <result>hello</result>
  </xsl:template>

</xsl:stylesheet>
""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>"""
    messages = """STYLESHEET MESSAGE:
<msg>XML <code>xsl:message</code> in top-level variable template</msg>
END STYLESHEET MESSAGE
"""


if __name__ == '__main__':
    test_main()
