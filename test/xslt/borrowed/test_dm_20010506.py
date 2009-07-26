########################################################################
# test/xslt/dm_20010506.py
# Dieter Maurer <dieter@handshake.de> reports problems with xsl:import 
# and variables

from amara.xslt import XsltError
from amara.lib import iri
from amara.test.xslt.xslt_support import _run_xml, _run_html

commonsource = "<ignored/>"

def test_xslt_import_with_variables_dm_20010506():
    _run_html(
        source_xml = commonsource,
        transform_uri = iri.os_path_to_uri(__file__),
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:import href="dm_20010506-1.xslt"/>

  <xsl:variable name="section.autolabel" select="1" />
  <xsl:variable name="html.stylesheet">book.xsl</xsl:variable>
  <xsl:variable name="html.stylesheet.type">text/css</xsl:variable>
    
</xsl:stylesheet>""",
        expected = """\
<html>
    START
    <link type='text/css' rel='stylesheet' href='book.xsl'>
    END
    </html>""",
        )

def test_xslt_import_with_params_dm_20010506():
    _run_html(
        source_xml = commonsource,
        transform_uri = iri.os_path_to_uri(__file__),
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:import href="dm_20010506-1.xslt"/>

  <xsl:param name="section.autolabel" select="1" />
  <xsl:param name="html.stylesheet">book.xsl</xsl:param>
  <xsl:param name="html.stylesheet.type">text/css</xsl:param>

</xsl:stylesheet>""",
        expected = """\
<html>
    START
    <link type='text/css' rel='stylesheet' href='book.xsl'>
    END
    </html>""",
        )

def test_xslt_include_with_variables_dm_20010506():
    try:
        _run_html(
            source_xml = commonsource,
            transform_uri = iri.os_path_to_uri(__file__),
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:include href="dm_20010506-1.xslt"/>

  <xsl:variable name="section.autolabel" select="1" />
  <xsl:variable name="html.stylesheet">book.xsl</xsl:variable>
  <xsl:variable name="html.stylesheet.type">text/css</xsl:variable>

</xsl:stylesheet>""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.DUPLICATE_TOP_LEVEL_VAR, err
    else:
        raise AssertionError("Should have raised an exception")

def test_xslt_include_with_params_dm_20010506():
    try:
        _run_html(
            source_xml = commonsource,
            transform_uri = iri.os_path_to_uri(__file__),
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:include href="dm_20010506-1.xslt"/>

  <xsl:param name="section.autolabel" select="1" />
  <xsl:param name="html.stylesheet">book.xsl</xsl:param>
  <xsl:param name="html.stylesheet.type">text/css</xsl:param>

</xsl:stylesheet>""",
            expected = None,
            )
    except XsltError, err:
        assert err.code == XsltError.DUPLICATE_TOP_LEVEL_VAR, err
    else:
        raise AssertionError("Should have raised an exception")


if __name__ == '__main__':
    raise SystemExit("use nosetests")
