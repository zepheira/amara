########################################################################
# amara/sax.py
"""
Abstraction module for Saxlette usage.

Saxlette is a complete implementation of SAX2 (and SAX2 only), mostly
implemented in C for performance

This file just pulls the SAX bits from amara.reader
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

