import cStringIO
import unittest
from amara.lib import testsupport
from amara.lib import MarkupWriter  ### where is now MarkupWriter ?


s = "100\xc2\xb0"

EXPECTED_1 = """<?xml version="1.0" encoding="UTF-8"?>
<xsa>
  <vendor>
    <name>Centigrade systems</name>
    <email>info@centigrade.bogus</email>
  </vendor>
  <product id="%s">
    <name>%s Server</name><version>1.0</version><last-release>20030401</last-release>
    <changes/>
  </product>
</xsa>""" % (s, s)


class Test_markup_writer(unittest.TestCase):
    """Basic document creation with different elements and attributes
    """
    def test_basic_markup_writer(self):
        """Basic MarkupWriter test"""
        s = cStringIO.StringIO()
        writer = MarkupWriter(stream=s, indent=u"yes")
        writer.startDocument()
        writer.startElement(u'xsa')
        writer.startElement(u'vendor')
        #Element with simple text (#PCDATA) content
        writer.simpleElement(u'name', content=u'Centigrade systems')
        #Note writer.text(content) still works
        writer.simpleElement(u'email', content=u"info@centigrade.bogus")
        writer.endElement(u'vendor')
        #Element with an attribute
        writer.startElement(u'product', attributes={u'id': u"100\u00B0"})
        #Note writer.attribute(name, value, namespace=None) still works
        writer.simpleElement(u'name', content=u"100\u00B0 Server")
        #XML fragment
        writer.xmlFragment('<version>1.0</version><last-release>20030401</last-release>')
        #Empty element
        writer.simpleElement(u'changes')
        writer.endElement(u'product')
        writer.endElement(u'xsa')
        writer.endDocument()
        self.assertEqual(EXPECTED_1, s.getvalue())
        return

if __name__ == '__main__':
    testsupport.test_main()