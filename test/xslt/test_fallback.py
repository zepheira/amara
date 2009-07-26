########################################################################
# test/xslt/test_fallback.py

from amara.xslt import XsltError
from xslt_support import _run_xml, _run_html

TRANSFORM_URI = "file:" + __name__

FALLBACK_SOURCE_XML = """<?xml version="1.0"?><dummy/>"""

def test_fallback_1():
    """1.0 stylesheet with non-1.0 top-level element"""
    _run_xml(
        source_xml = FALLBACK_SOURCE_XML,
        transform_uri = TRANSFORM_URI,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting xsl:version="3.0">hello</greeting>
  <xsl:template match="/">
    <result>
      <xsl:value-of select="document('')/*/greeting"/>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>"""
        )

def test_fallback_2():
    """3.0 stylesheet with 3.0 top-level element"""
    # stylesheet version 3.0
    # top-level literal result element w/no version, in no namespace
    # (should be ignored / no error)
    _run_xml(
        source_xml = FALLBACK_SOURCE_XML,
        transform_uri = TRANSFORM_URI,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting>hello</greeting>
  <xsl:template match="/">
    <result>
      <xsl:value-of select="document('')/*/greeting"/>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello</result>""")

def test_fallback_3():
    """forwards-compatible example from XSLT 1.0 specification"""
    _run_html(
        source_xml = FALLBACK_SOURCE_XML,
        transform_uri = TRANSFORM_URI,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.1" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="system-property('xsl:version') >= 1.1">
        <xsl:exciting-new-1.1-feature/>
      </xsl:when>
      <xsl:otherwise>
        <html>
        <head>
          <title>XSLT 1.1 required</title>
        </head>
        <body>
          <p>Sorry, this stylesheet requires XSLT 1.1.</p>
        </body>
        </html>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    <title>XSLT 1.1 required</title>
  </head>
  <body>
    <p>Sorry, this stylesheet requires XSLT 1.1.</p>
  </body>
</html>""")

def test_fallback_4():
    """1.0 literal result element with fallback"""
    _run_xml(
        source_xml = FALLBACK_SOURCE_XML,
        transform_uri = TRANSFORM_URI,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.1" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">
    <!--
      literal result element version = 1.0;
      fallback instruction is noop.
    -->
    <result xsl:version="1.0">
      <xsl:fallback>fallback</xsl:fallback>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result/>""")

def test_fallback_5():
    """uninstantiated non-1.0 literal result element"""
    _run_xml(
        source_xml = FALLBACK_SOURCE_XML,
        source_uri = "file:xslt/test_fallback.py",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.1" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">
    <!--
      literal result element version != 1.0;
      element is not instantiated;
      no error must be signaled.
    -->
    <result xsl:version="3.0">
      <xsl:choose>
        <xsl:when test="false()">
          <xsl:perform-magic>We do magic<xsl:fallback>Sorry, we don't do magic</xsl:fallback></xsl:perform-magic>
        </xsl:when>
        <xsl:otherwise>hello world</xsl:otherwise>
      </xsl:choose>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello world</result>""")

def test_fallback_6():
    """non-1.0 literal result element with fallback"""
    _run_xml(
        source_xml = FALLBACK_SOURCE_XML,
        transform_uri = TRANSFORM_URI,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.1" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">
    <!--
      literal result element version != 1.0;
      fallback must be performed;
    -->
    <result xsl:version="3.0">
      <xsl:perform-magic>We do magic<xsl:fallback>Sorry, we don't do magic</xsl:fallback></xsl:perform-magic>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>Sorry, we don't do magic</result>"""
        )

def test_fallback_error_1():
    """1.0 stylesheet with implicit 1.0 illegal top-level element"""
    # stylesheet version 1.0
    # top-level literal result element with no version info, in no namespace
    # (should raise an exception per XSLT 1.0 sec. 2.2)
    try:
        _run_xml(
            source_xml = FALLBACK_SOURCE_XML,
            transform_uri = TRANSFORM_URI,
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting>hello</greeting>
  <xsl:template match="/">
    <result/>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.ILLEGAL_ELEMENT_CHILD
    else:
        raise AssertionError("should have failed!")

def test_fallback_error_2():
    """1.0 stylesheet with explicit 1.0 illegal top-level element"""
    # stylesheet version 1.0
    # top-level literal result element version 1.0, in no namespace
    # (same as previous test, but version is explicit;
    #  should still raise an exception per XSLT 1.0 sec. 2.2)
    try:
        _run_xml(
            source_xml = FALLBACK_SOURCE_XML,
            transform_uri = TRANSFORM_URI,
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting xsl:version="1.0">hello</greeting>
  <xsl:template match="/">
    <result/>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.ILLEGAL_ELEMENT_CHILD
    else:
        raise AssertionError("should have failed!")

def test_fallback_error_3():
    """3.0 stylesheet with explicit 1.0 illegal top-level element"""
    # stylesheet version 3.0
    # top-level literal result element version 1.0, in no namespace
    # (it disables forwards-compatible processing for itself,
    #  so it should still raise an exception per XSLT 1.0 sec. 2.2)
    try:
        _run_xml(
            source_xml = FALLBACK_SOURCE_XML,
            transform_uri = TRANSFORM_URI,
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting xsl:version="1.0">hello</greeting>
  <xsl:template match="/">
    <result/>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.ILLEGAL_ELEMENT_CHILD
    else:
        raise AssertionError("should have failed!")


def test_fallback_error_4():
    """non-1.0 literal result element without fallback"""
    try:
        _run_xml(
            source_xml = FALLBACK_SOURCE_XML,
            transform_uri = TRANSFORM_URI,
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">
    <!--
      literal result element version != 1.0;
      fallback must be performed;
      since no fallback child, error must be signaled.
    -->
    <result xsl:version="3.0">
      <xsl:perform-magic/>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.FWD_COMPAT_WITHOUT_FALLBACK
    else:
        raise AssertionError("should have failed!")

if __name__ == '__main__':
    raise SystemExit("use nosetests")
