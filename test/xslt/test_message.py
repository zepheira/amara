########################################################################
# test/xslt/test_message.py

import os

from xslt_support import _run_xml, _run_html, _compare_text

module_name = os.path.dirname(__file__)
filename = os.path.join(module_name, "addr_book1.xml")
SOURCE_XML = open(filename).read()
SOURCE_URI = "file:" + filename
TRANSFORM_URI = "file:xslt/test_message.py"

from cStringIO import StringIO

def _run(run_func, transform_xml, expected, expected_messages):
    message_stream = StringIO()
    run_func(
        processor_kwargs = dict(message_stream = message_stream),
        source_xml = SOURCE_XML,
        source_uri = SOURCE_URI,
        transform_uri = TRANSFORM_URI,
        transform_xml = transform_xml,
        expected = expected)
    messages = message_stream.getvalue()
    diff = _compare_text(messages, expected_messages)

    if diff:
        print diff
        print "GOT MESSAGES"
        print messages
        print "EXPECTED MESSAGES"
        print expected_messages
        raise AssertionError("transform was correct but the messages were unexpected")

def test_message_1():
    """<xsl:message> in top-level variable"""
    _run(
        run_func = _run_xml,
        transform_xml = """<?xml version="1.0"?>
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
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>""",
        expected_messages = """STYLESHEET MESSAGE:
Legal xsl:message in top-level variable template
END STYLESHEET MESSAGE
""")


def test_message_2():
    """<xsl:message> in template body"""
    _run(
        run_func = _run_xml,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml"/>

  <xsl:template match="/">
    <result>hello</result>
    <xsl:message terminate="no">Legal xsl:message in regular template body</xsl:message>
  </xsl:template>

</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>""",
        expected_messages = """STYLESHEET MESSAGE:
Legal xsl:message in regular template body
END STYLESHEET MESSAGE
""")


def test_message_3():
    """xsl:message deep in stylesheet processing"""
    _run(
        run_func = _run_html,
        transform_xml = """<?xml version="1.0"?>
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
""",
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
</HTML>""",
    expected_messages = """STYLESHEET MESSAGE:
We're in the thick of processing NAME elements
END STYLESHEET MESSAGE
STYLESHEET MESSAGE:
We're in the thick of processing NAME elements
END STYLESHEET MESSAGE
STYLESHEET MESSAGE:
We're in the thick of processing NAME elements
END STYLESHEET MESSAGE
""")

def test_message_4():
    """<xsl:message> in XML form"""
    _run(
        run_func = _run_xml,
        transform_xml = """<?xml version="1.0"?>
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
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>""",
        expected_messages = """STYLESHEET MESSAGE:
<msg>XML <code>xsl:message</code> in top-level variable template</msg>
END STYLESHEET MESSAGE
"""
        )

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
