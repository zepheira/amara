# -*- encoding: utf-8 -*-
########################################################################
# test/xslt/borrowed/cs_20070210.py

# From original 4Suite cvs:
# Dan (hitt@charybdis.zembu.com) reports non-conformance with XSLT w.r.t. variable shadowing
from amara.lib import iri

from amara.test.xslt.xslt_support import _run_xml

def test_apply_import1():
    _run_xml(
        source_xml = "<example><spam/></example>",
        transform_uri = iri.os_path_to_uri(__file__),
        transform_xml = """\
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

<xsl:import href="cs_20070210-1.xslt"/>

<xsl:template match="/">
  <xsl:apply-templates mode="foo"/>
</xsl:template>

<xsl:template match="example" mode="foo">
  <div>
    <span>b</span>
    <xsl:apply-imports/>
  </div>
</xsl:template>

</xsl:transform>""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<div><span>b</span><span>a</span></div>""",
        )

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
