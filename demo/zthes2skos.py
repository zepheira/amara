"""
Demo XML format translation, specifically one thesaurus information to another.
Specifically, convert Zthes-in-XML [1] file to SKOS [2]

[1] http://zthes.z3950.org/schema/index.html
[2] http://www.w3.org/2004/02/skos/

Sample usage:

zthes2skos.py http://zthes.z3950.org/schema/sample-05.xml
"""

MORE_DOC = """
Zthes relation types explained at http://www.loc.gov/z3950/agency/profiles/zthes-02.html

``NT'' Narrower term: that is, the related term is more specific than the current one. -> skos:narrower
``BT'' Broader term: that is, the related term is more general than the current one. -> skos:broader
``USE'' Use instead: that is, the related term should be used in preference to the current one. -> z:useInstead
``UF'' Use for: that is, the current term should be used in preference to the related one -> z:useFor
``RT'' Related term. -> skos:related

See also:

* http://www.w3.org/2001/sw/Europe/reports/thes/1.0/migrate/
"""

import sys
import amara
from amara.writers.struct import *
from amara.namespaces import *

ZTHES_NAMESPACE = u"http://zthes.z3950.org/model/index.html"

#http://www.loc.gov/z3950/agency/profiles/zthes-02.html
RELATION_LOOKUP = {
  u'RT': (SKOS_NAMESPACE, u'skos:related'),
  u'NT': (SKOS_NAMESPACE, u'skos:narrower'),
  u'BT': (SKOS_NAMESPACE, u'skos:broader'),
  u'USE': (ZTHES_NAMESPACE, u'z:useInstead'),
  u'UF': (ZTHES_NAMESPACE, u'z:useFor'),
}

doc = amara.parse(sys.argv[1])

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

