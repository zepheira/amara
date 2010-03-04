import sys
import unittest
from cStringIO import StringIO

from amara import xml_print, tree
from amara.lib.treecompare import xml_compare
from amara.writers import lookup, register, XML_W, HTML_W, XHTML_W

from amara.test import KnownFailure

class Test_xml_write(unittest.TestCase):
    "Test the new xml_write and xml_encode methods"

    def test_lookup(self):
        "Test the lookup of the standard printers"
        # Check the constants are supported
        self.assertTrue(lookup(XML_W) is not None)
        self.assertTrue(lookup(HTML_W) is not None)
        self.assertTrue(lookup(XHTML_W) is not None)

        # Check unknown values raise ValueError
        self.assertRaises(ValueError, lookup, 'bogus')

    def test_register(self):
        "Check that register() works"
        self.assertRaises(ValueError, lookup, "new-printer")
        register('new-printer', object)
        self.assertTrue(lookup('new-printer') is not None)

    def test_encode(self):
        xml_w = lookup('xml')
        t = tree.parse("<root>entr&#233;e</root>")

        # Default is UTF-8.
        self.assert_(xml_compare(t.xml_encode(),
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<root>entr\xc3\xa9e</root>'))
        self.assert_(xml_compare(t.xml_encode(XML_W),
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<root>entr\xc3\xa9e</root>'))
        self.assert_(xml_compare(t.xml_encode(xml_w),
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<root>entr\xc3\xa9e</root>'))

        # Try latin-1 output.
        self.assert_(xml_compare(t.xml_encode(encoding='iso-8859-1'),
                    '<?xml version="1.0" encoding="iso-8859-1"?>\n'
                    '<root>entr\xe9e</root>'))

    def test_html(self):
        "Simple check of HTML output"
        t = tree.parse("""<?xml version='1.0'?>
<disclaimer>
  <p>The opinions represented herein represent those of the individual
  and should not be interpreted as official policy endorsed by this
  organization.</p>
</disclaimer>
""")

        
        self.assertEqual(t.xml_encode(HTML_W), """<disclaimer>
  <p>The opinions represented herein represent those of the individual
  and should not be interpreted as official policy endorsed by this
  organization.</p>
</disclaimer>""")
        html_w = lookup(HTML_W)
        self.assertEqual(t.xml_encode(html_w), """<disclaimer>
  <p>The opinions represented herein represent those of the individual
  and should not be interpreted as official policy endorsed by this
  organization.</p>
</disclaimer>""")

    def test_write_to_stdout(self):
        "Check that the default output is to stdout"
        xml_w = lookup('xml')
        t = tree.parse("<root>entr&#233;e</root>")
        stream = StringIO()
        try:
            sys.stdout = stream
            t.xml_write()
            self.assertEqual(stream.getvalue(),
                             '<?xml version="1.0" encoding="UTF-8"?>\n'
                             '<root>entr\xc3\xa9e</root>')
        finally:
            sys.stdout = sys.__stdout__

    def test_canonical(self):
        "Tests output of canonical XML (see also test_c14n)"
        raise KnownFailure("See http://trac.xml3k.org/ticket/23")
        t = tree.parse("<root><empty/>"
                       "</root>")
        self.assertEqual(t.xml_encode('xml-canonical'),
                         '<?xml version="1.0" encoding="UTF-8"?>\n'
                         '<root><empty></empty>'
                         '</root>')
        

if __name__ == '__main__':
    raise SystemExit("use nosetests")
