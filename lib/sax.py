########################################################################
# amara/sax.py
"""
Abstraction module for Saxlette usage.

Saxlette is a complete implementation of SAX2 (and SAX2 only), mostly
implemented in C for performance

This file just pulls the SAX bits from amara.reader

Sample usage:

from xml import sax
from amara.lib import inputsource

class element_counter(sax.ContentHandler):
    def startDocument(self):
        self.ecount = 0

    def startElementNS(self, name, qname, attribs):
        self.ecount += 1

parser = sax.make_parser(['amara.reader'])
handler = element_counter()
parser.setContentHandler(handler)
#'ot.xml' or 'file:ot.xml' or file('ot.xml') or file('ot.xml').read() would work just as well, of course
parser.parse(inputsource('http://www.w3schools.com/xmL/cd_catalog.xml'))
print "Elements counted:", handler.ecount
"""

import sys
from amara._expat import SaxReader as reader

# Support xml.sax.make_parser()
# To create a parser using this method, use the following:
#   parser = xml.sax.make_parser(['amara.reader'])
create_parser = reader

# Amara-specific SAX features
from amara._expat import FEATURE_PROCESS_XINCLUDES
from amara._expat import FEATURE_GENERATOR

# Amara-specific SAX properties
from amara._expat import PROPERTY_WHITESPACE_RULES
from amara._expat import PROPERTY_YIELD_RESULT

from amara import XMLNS_NAMESPACE

from amara.reader import ContentHandler, Locator, Attributes, SaxPrinter

