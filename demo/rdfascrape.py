"""
Scrape RDFa [1] [2] from an XHTML Web page
Works on any HTML, though people who put what they call RDFa into tag soup are naughty and need their ears boxed

[1] http://en.wikipedia.org/wiki/RDFa
[2] 

Sample usage:

python rdfascrape.py data/xhtmlrdfa.html
python rdfascrape.py http://www.ivan-herman.net/foaf.html

For other examples see: http://esw.w3.org/topic/RDFa/Examples
"""

import sys
import amara
from amara.bindery import html
from amara.writers.struct import *
from amara.namespaces import *
from amara.lib.xmlstring import *
from amara.lib.iri import DEFAULT_RESOLVER
from amara.bindery.model import *

#Give Amara an example so it knows what structure to expect
#label_model = examplotron_model('data/xhtmlrdfa.html')

DOCURI = sys.argv[1]
#doc = html.parse(DOCURI, model=label_model)
doc = html.parse(DOCURI)

try:
    DOCURI = BASEURI = doc.html.head.base.href
except:
    BASEURI = None

def absolutize(uriref):
    try:
        return DEFAULT_RESOLVER.normalize(uriref, DOCURI)
    except:
        return uriref

def expand(data, context=None):
    if context:
        nss = context.xml_namespaces.copy()
        prefix, qname = splitqname(unicode(data))
        if prefix and prefix in nss:
            return nss[prefix] + qname
    return unicode(data)

def handle_statement(elem):
    subject = elem.xml_select(u'ancestor::*/@about')
    subject = absolutize(subject[0].xml_value) if subject else DOCURI
    if elem.xml_select(u'@property') and elem.xml_select(u'@content'):
        return ( subject , expand(elem.property, elem), elem.content )
    elif elem.xml_select(u'@property'):
        return ( subject, expand(elem.property, elem), expand(elem) )
    elif elem.xml_select(u'@rel') and elem.xml_select(u'@resource'):
        return ( subject, expand(elem.rel, elem), elem.resource )
    elif elem.xml_select(u'@rel') and elem.xml_select(u'@href'):
        return ( subject, expand(elem.rel, elem), elem.href )
    else:
        return ()

statement_elems = doc.xml_select(u'//*[@property|@resource|@rel]')
triples = ( handle_statement(elem) for elem in statement_elems )

for triple in triples:
    print triple

sys.exit(0)
