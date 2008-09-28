import sys, datetime
from amara.writers.struct import *
from amara.namespaces import *

tags = [u"xml", u"python", u"atom"]

w = structwriter(indent=u"yes")
w.feed(
ROOT(
    E((ATOM_NAMESPACE, u'feed'), {(XML_NAMESPACE, u'xml:lang'): u'en'},
        E(u'id', u'urn:bogus:myfeed'),
        E(u'title', u'MyFeed'),
        E(u'updated', datetime.datetime.now().isoformat()),
        E(u'name',
            E(u'title', u'Uche Ogbuji'),
            E(u'uri', u'http://uche.ogbuji.net'),
            E(u'email', u'uche@ogbuji.net'),
        ),
        E(u'link', {u'href': u'/blog'}),
        E(u'link', {u'href': u'/blog/atom1.0', u'rel': u'self'}),
        E(u'entry',
            E(u'id', u'urn:bogus:myfeed:entry1'),
            E(u'title', u'Hello world'),
            E(u'updated', datetime.datetime.now().isoformat()),
            ( E(u'category', {u'term': t}) for t in tags ),
        ),
        E(u'content', {u'type': u'xhtml'},
            E((XHTML_NAMESPACE, u'div'),
                E(u'p', u'Happy to be here')
            )
        )
))
)
