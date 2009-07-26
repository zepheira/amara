########################################################################
# test/xslt/mb_20020527.py

from amara.test.xslt.xslt_support import _run_xml
from amara.lib import iri

def test_xslt_nested_imports_with_names_that_clash_across_import_precedence_mb_20020527():
    _run_xml(
        source_xml = "<foo/>",
        transform_uri = iri.os_path_to_uri(__file__),
        transform_xml = """<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="resources/mb_20020527-1.xsl"/>

  <xsl:template name="i">
    <foo>import.xsl</foo>
  </xsl:template>

</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>\n<out><foo>import.xsl</foo></out>""",
        )

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
