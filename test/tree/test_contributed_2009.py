# -*- encoding: utf-8 -*-
#Tests based on bug reports and other contributions from the community

import unittest
from amara.lib import testsupport
from amara.bindery import parse
import amara

class Test_many_attribs(unittest.TestCase):
    """http://trac.xml3k.org/ticket/8"""
    MANY_ATTRS_XML = """<row a="1" b="2" c="3" d="4" e="5" f="6"/>"""
    def test_many_att(self):
        doc = amara.parse(self.MANY_ATTRS_XML)
        row = doc.xml_select("row")[0]

        attrs = row.xml_attributes
        missing = [ k for k in attrs.keys() if k not in attrs ]
        #[(None, u'b'), (None, u'c'), (None, u'd'), (None, u'e')]
        listcomp_keys = sorted([ k for k in attrs.keys() ])
        genexpr_keys = sorted(list( k for k in attrs.keys() ))
        items = sorted(attrs.items())
        self.assertEqual(missing, [])
        self.assertEqual(listcomp_keys, [(None, u'a'), (None, u'b'), (None, u'c'), (None, u'd'), (None, u'e'), (None, u'f')])
        self.assertEqual(genexpr_keys, [(None, u'a'), (None, u'b'), (None, u'c'), (None, u'd'), (None, u'e'), (None, u'f')])
        self.assertEqual(items, [((None, u'a'), u'1'), ((None, u'b'), u'2'), ((None, u'c'), u'3'), ((None, u'd'), u'4'), ((None, u'e'), u'5'), ((None, u'f'), u'6')])
        return


if __name__ == '__main__':
    testsupport.test_main()

