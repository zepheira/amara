########################################################################
# test/xslt/test_fallback.py
from amara.test import test_main
from amara.test.xslt import xslt_test, xslt_error, filesource, stringsource
from amara.xslt import XsltError

class fallback_test(xslt_test):
    __unittest__ = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")


class test_fallback_1(fallback_test):
    """1.0 stylesheet with non-1.0 top-level element"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting xsl:version="3.0">hello</greeting>
  <xsl:template match="/">
    <result>
      <xsl:value-of select="document('')/*/greeting"/>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result>hello</result>"""


class test_fallback_2(fallback_test):
    """3.0 stylesheet with 3.0 top-level element"""
    # stylesheet version 3.0
    # top-level literal result element w/no version, in no namespace
    # (should be ignored / no error)
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0"?>
<result>hello</result>"""


class test_fallback_3(fallback_test):
    """forwards-compatible example from XSLT 1.0 specification"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    <title>XSLT 1.1 required</title>
  </head>
  <body>
    <p>Sorry, this stylesheet requires XSLT 1.1.</p>
  </body>
</html>"""


class test_fallback_4(fallback_test):
    """1.0 literal result element with fallback"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<result/>"""


class test_fallback_5(fallback_test):
    """uninstantiated non-1.0 literal result element"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>hello world</result>"""


class test_fallback_6(fallback_test):
    """non-1.0 literal result element with fallback"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<result>Sorry, we don't do magic</result>"""



class fallback_error(xslt_error):
    __unittest__ = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")


class test_fallback_error_1(fallback_error):
    """1.0 stylesheet with implicit 1.0 illegal top-level element"""
    error_code = XsltError.ILLEGAL_ELEMENT_CHILD
    # stylesheet version 1.0
    # top-level literal result element with no version info, in no namespace
    # (should raise an exception per XSLT 1.0 sec. 2.2)
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting>hello</greeting>
  <xsl:template match="/">
    <result/>
  </xsl:template>
</xsl:stylesheet>
""")


class test_fallback_error_2(fallback_error):
    """1.0 stylesheet with explicit 1.0 illegal top-level element"""
    error_code = XsltError.ILLEGAL_ELEMENT_CHILD
    # stylesheet version 1.0
    # top-level literal result element version 1.0, in no namespace
    # (same as previous test, but version is explicit;
    #  should still raise an exception per XSLT 1.0 sec. 2.2)
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting xsl:version="1.0">hello</greeting>
  <xsl:template match="/">
    <result/>
  </xsl:template>
</xsl:stylesheet>
""")


class test_fallback_error_3(fallback_error):
    """3.0 stylesheet with explicit 1.0 illegal top-level element"""
    error_code = XsltError.ILLEGAL_ELEMENT_CHILD
    # stylesheet version 3.0
    # top-level literal result element version 1.0, in no namespace
    # (it disables forwards-compatible processing for itself,
    #  so it should still raise an exception per XSLT 1.0 sec. 2.2)
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <greeting xsl:version="1.0">hello</greeting>
  <xsl:template match="/">
    <result/>
  </xsl:template>
</xsl:stylesheet>
""")


class test_fallback_error_4(fallback_error):
    """non-1.0 literal result element without fallback"""
    error_code = XsltError.FWD_COMPAT_WITHOUT_FALLBACK
    transform = stringsource("""<?xml version="1.0"?>
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
""")


if __name__ == '__main__':
    test_main()
