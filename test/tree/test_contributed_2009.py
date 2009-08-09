# -*- encoding: utf-8 -*-
#Tests based on bug reports and other contributions from the community

import unittest
from amara.lib import testsupport
from amara.bindery import parse
import amara

class Test_many_attribs(unittest.TestCase):
    """http://trac.xml3k.org/ticket/8"""
    MANY_ATTRS_XML = """<row a="" b="" c="" d="" e="" f=""/>"""
    def test_many_att(self):
        doc = amara.parse(self.MANY_ATTRS_XML)
        row = doc.xml_select("row")[0]

        attrs = row.xml_attributes
        missing = [ k for k in attrs.keys() if k not in attrs ]
        #[(None, u'b'), (None, u'c'), (None, u'd'), (None, u'e')]
        listcomp_keys = [ k for k in attrs.keys() ]
        genexpr_keys = list( k for k in attrs.keys() )
        items = attrs.items()
        self.assertEqual(missing, [])
        self.assertEqual(listcomp_keys, [(None, u'b'), (None, u'c'), (None, u'd'), (None, u'e')])
        self.assertEqual(genexpr_keys, [(None, u'b'), (None, u'c'), (None, u'd'), (None, u'e')])
        self.assertEqual(items, [(None, u'b'), (None, u'c'), (None, u'd'), (None, u'e')])
        return


if __name__ == '__main__':
    testsupport.test_main()

