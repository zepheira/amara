"""
Scrape RDFa [1] [2] from an XHTML Web page
Works on any HTML, though people who put what they call RDFa into tag soup are naughty and need their ears boxed

[1] http://en.wikipedia.org/wiki/RDFa
[2] 

Sample usage:

rdfascrape.py http://www.ivan-herman.net/foaf.html

For other examples see: http://esw.w3.org/topic/RDFa/Examples
"""

import sys
import amara
from amara.writers.struct import *
from amara.namespaces import *

doc = amara.parse(sys.argv[1])
statement_elements = doc.xml_select(u'//@property|//@resource')
print statement_elements

sys.exit(0)

w = structwriter(indent=u"yes").feed(
ROOT(
  E((RDF_NAMESPACE, u'rdf:RDF'),
    NS(u'skos', SKOS_NAMESPACE),
    NS(u'z', ZTHES_NAMESPACE),
    (
      E(
        (SKOS_NAMESPACE, u'skos:Concept'),
        {(RDF_NAMESPACE, u'rdf:ID'): term.xml_select(u'string(termId)')},
        E((SKOS_NAMESPACE, u'skos:prefLabel'), term.xml_select(u'string(termName)')),
        (E((SKOS_NAMESPACE, u'skos:note'),
          E((SKOS_NAMESPACE, u'skos:Note'),
            E((RDF_NAMESPACE, u'rdf:label'), note.xml_select(u'string(@label)')),
            E((RDF_NAMESPACE, u'rdf:value'), note.xml_select(u'string(.)'))
          )
        ) for note in term.xml_select(u'termNote') ),
        (E(RELATION_LOOKUP.get(rel.xml_select(u'string(relationType)'), (ZTHES_NAMESPACE, u'z:'+rel.xml_local)),
          {(RDF_NAMESPACE, u'rdf:resource'): rel.xml_select(u'concat("#", termId)')}
        ) for rel in term.xml_select(u'relation') )
      )
      #E((SKOS_NAMESPACE, u'skos:note'), term.xml_select(u'string(termName)')),
    for term in doc.xml_select(u'/Zthes/term'))
  )
))

print

