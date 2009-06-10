# -*- encoding: utf-8 -*-
#RFC 4287
#python atomtools.py copiasample.atom

import sys
from itertools import *
from functools import *
from operator import *
from collections import defaultdict

import re, copy
from cStringIO import StringIO
from datetime import datetime

import amara
from amara.namespaces import *
from amara.bindery import html
from amara.bindery.model import *
from amara.lib.util import *
from amara.lib.xmlstring import *
from amara import bindery
from amara.writers.struct import *

from amara.bindery.util import dispatcher, node_handler
from amara.bindery.model import *

from amara.lib.util import *

__all__ = [
  'ENTRY_MODEL', 'FEED_MODEL', 'ENTRY_MODEL_XML', 'FEED_MODEL_XML',
  'ATOM_IMT', 'NSS', 'DEFAULT_SKEL',
  'tidy_content_element', 'feed', 'aggregate_entries',
  'atom2rss1',
]

#From 1.1 of the spec
ENTRY_MODEL_XML = """<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara" ak:resource="atom:id">
   <ak:rel name="'type'" value="'atom:entry'"/>
   <ak:rel name="'alternate_link'" value='atom:link[@rel="alternate"]/@href' />
   <ak:rel name="'self_link'" value='atom:link[not(@rel) or @rel="self"]/@href' />
   <atom:id ak:rel="local-name()" ak:value="."/>
   <atom:title type="xhtml" ak:rel="local-name()" ak:value="."/>
   <atom:updated ak:rel="local-name()" ak:value="."></atom:updated>
   <atom:published ak:rel="local-name()" ak:value="."></atom:published>
   <atom:link eg:occurs="*" ak:rel="local-name()" ak:value="@href" />
   <atom:summary type="xhtml" ak:rel="local-name()" ak:value="."  ak:coercion="'nodeset'"/>
   <atom:category eg:occurs="*" ak:rel="local-name()" ak:value="@term"/>
   <atom:author eg:occurs="*" ak:rel="local-name()" ak:resource="(atom:name|atom:uri|atom:email)[1]">
     <ak:rel name="'type'" value="'atom:author'"/>
     <atom:name ak:rel="local-name()" ak:value="." />
     <atom:uri ak:rel="local-name()" ak:value="." />
     <atom:email ak:rel="local-name()" ak:value="." />
   </atom:author>
   <atom:content type="xhtml" eg:occurs="?" ak:rel="local-name()" ak:value="." ak:coercion="'nodeset'"/> 
 </atom:entry>"""

FEED_MODEL_XML = """<atom:feed xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara" ak:resource="atom:id">
 <ak:rel name="'type'" value="'atom:feed'"/>
 <ak:rel name="'alternate_link'" value='atom:link[@rel="alternate"]/@href' />
 <ak:rel name="'self_link'" value='atom:link[not(@rel) or @rel="self"]/@href' />
 <atom:title ak:rel="local-name()" ak:value="."></atom:title>
 <atom:subtitle ak:rel="local-name()" ak:value="."></atom:subtitle>
 <atom:updated ak:rel="local-name()" ak:value="."></atom:updated>
 <atom:author eg:occurs="*" ak:rel="local-name()" ak:resource="(atom:name|atom:uri|atom:email)[1]">
   <ak:rel name="'type'" value="'atom:author'"/>
   <atom:name ak:rel="local-name()" ak:value="." />
   <atom:uri ak:rel="local-name()" ak:value="." />
   <atom:email ak:rel="local-name()" ak:value="." />
 </atom:author>
 <atom:id ak:rel="local-name()" ak:value="."></atom:id>
 <atom:link eg:occurs="*" ak:rel="local-name()" ak:value="@href"/>
 <atom:rights ak:rel="local-name()" ak:value="."></atom:rights>
%s
</atom:feed>
""" % ENTRY_MODEL_XML

ATOM_IMT = u'application/atom+xml'

NSS = {COMMON_PREFIXES[ATOM_NAMESPACE]: ATOM_NAMESPACE}

FEED_MODEL = examplotron_model(FEED_MODEL_XML)
ENTRY_MODEL = examplotron_model(ENTRY_MODEL_XML)

SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)

TYPE = 'type'
UPDATED = 'updated'
TITLE = 'title'
ID = 'id'

DEFAULT_SKEL = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Sample feed</title>
  <id>http://example.org/CHANGE_ME</id>
  <!--updated>2009-03-03T11:50:21Z</updated-->

</feed>
'''


slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')[:20]

datetime_from_iso = lambda ds: datetime.strptime(ds, "%Y-%m-%dT%H:%M:%SZ")

path_from_datetime = lambda dt: '%i/%i'%dt.utctimetuple()[:2]


def aggregate_entries(envelope, entries):
    '''
    envelope - input source of atom feed document to enclose entries
        if it has any entries, the new ones are appended
    entries - sequence of entry input sources
    '''
    envelope_doc = bindery.parse(envelope, model=FEED_MODEL)
    entrydocs = [ bindery.parse(entry, model=ENTRY_MODEL) for entry in entries ]
    #for entry in sorted(entrydocs, key=lambda x: attrgetter('updated')):
    for entry_doc in sorted(entrydocs, key=lambda x: str(x.entry.updated), reverse=True):
        envelope_doc.feed.xml_append(entry_doc.entry)
    metadata = generate_metadata(envelope_doc)
    return envelope_doc, metadata


def tidy_content_element(root, check=u'//atom:title|//atom:summary|//atom:content', prefixes=NSS):
    """
    Takes all Atom content elements with type=html (i.e. a:title, a:summary or a:content)
    And convert them to be of type=xhtml

    This operation mutates root in place.

    Example:

    import amara; from util import tidy_content_element
    A = '<entry xmlns="http://www.w3.org/2005/Atom"><id>urn:bogus:x</id><title type="html">&lt;div&gt;x&lt;p&gt;y&lt;p&gt;&lt;/div&gt;</title></entry>'
    doc = amara.parse(A)
    tidy_content_element(doc)
    amara.xml_print(doc)
    """
    nodes = root.xml_select(check, prefixes)
    for node in nodes:
        if node.xml_select(u'@type = "html"') and node.xml_select(u'string(.)'):
            #unsouped = html.parse('<html xmlns="http://www.w3.org/1999/xhtml">%s</html>'%node.xml_select(u'string(.)').encode('utf-8'), encoding='utf-8')
            unsouped = html.parse('<html>%s</html>'%node.xml_select(u'string(.)').encode('utf-8'), encoding='utf-8')
            unsouped.html.xml_namespaces[None] = XHTML_NAMESPACE
            subtree = element_subtree_iter(unsouped)
            #Grab body, before changing the namespaces changes how it's bound
            #After NS is changed, you'd need to remember to do unsouped.html_.body_
            body = unsouped.html.body
            for e in subtree:
                if isinstance(e, tree.element):
                    e.xml_namespace = XHTML_NAMESPACE
                    #Temporary fixup until bindery can handle namespace change better
                    e.xml_parent.xml_fixup(e)
            #amara.xml_print(unsouped, stream=sys.stderr, indent=True)
            while node.xml_children: node.xml_remove(node.xml_first_child)
            node.xml_append(amara.parse('<div xmlns="http://www.w3.org/1999/xhtml"/>').xml_first_child)
            #node.xml_append_fragment('<div xmlns="http://www.w3.org/1999/xhtml"/>')
            for child in body.xml_children:
                node.xml_first_child.xml_append(child)
            node.xml_attributes[None, u'type'] = u'xhtml'
    return root

#

class feed(object):
    '''
    Class to facilitate building Atom feeds
    '''
    def __init__(self, skel=None, title=None, updated=None, id=None):
        '''
        skel - an input source with a starting Atom document, generally a skeleton
        '''
        skel = skel or DEFAULT_SKEL
        self.source = bindery.parse(skel, model=FEED_MODEL)
        if title:
            self.source.feed.title = title
        if id:
            self.source.feed.id = id
        #FIXME: Warnings if they don't supply id in skel or id kwarg
        #self.source.feed.xml_append(E((ATOM_NAMESPACE, u'updated'), updated or datetime.now().isoformat()))
        self.source.feed.updated = updated or datetime.now().isoformat()
        return

    def append(self, id_, title, updated=None, summary=None, content=None, authors=None, categories=None, links=None, elements=None):
        '''
        append an entry
        author is list of (u'Uche Ogbuji', u'Uche@Ogbuji.net', u'http://Uche.Ogbuji.net'), any of which can be None
        '''
        authors = authors or []
        links = links or []
        categories = categories or []
        elements = elements or []
        doc = self.source
        updated = updated or datetime.now().isoformat()
        entry = doc.xml_element_factory(ATOM_NAMESPACE, u'entry')
        #entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'id', content=id_))
        entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'id'))
        entry.id.xml_append(U(id_))
        entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'updated'))
        entry.updated.xml_append(U(updated))
        #Only supports text titles, for now
        entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'title'))
        entry.title.xml_append(U(title))
        for link in links:
            (href, rel) = link
            entry.xml_append(E((ATOM_NAMESPACE, u'link'), {u'href': href, u'rel': rel}))
        for category in categories:
            entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'category'))
            try:
                term, scheme = category
            except TypeError:
                term, scheme = category, None
            entry.category[-1].xml_attributes[u'term'] = U(term)
            if scheme: entry.category[-1].xml_attributes[u'scheme'] = U(scheme)
        for author in authors:
            entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'author'))
            (name, email, uri) = author
            entry.author[-1].xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'name'))
            entry.author[-1].name.xml_append(U(name))
            if email:
                entry.author[-1].xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'email'))
                entry.author[-1].name.xml_append(U(email))
            if uri:
                entry.author[-1].xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'uri'))
                entry.author[-1].uri.xml_append(U(uri))
        for elem in elements:
            buf = StringIO()
            w = structwriter(indent=u"yes", stream=buf)
            w.feed(elem)
            entry.xml_append_fragment(buf.getvalue())
        #FIXME: Support other content types
        if summary:
            entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'summary'))
            entry.summary.xml_attributes[u'type'] = u'text'
            entry.summary.xml_append(U(summary))
        if content:
            entry.xml_append(doc.xml_element_factory(ATOM_NAMESPACE, u'content'))
            entry.content.xml_attributes[u'type'] = u'text'
            entry.content.xml_append(U(content))
        doc.feed.xml_append(entry)
        return


def parse(isrc):
    '''
    Convert Atom syntax to Exhibit JSON
    (see: http://www.ibm.com/developerworks/web/library/wa-realweb6/ ; this is based on listing 3)
    '''
    doc = bindery.parse(isrc, model=FEED_MODEL)
    try:
        doc_entries = iter(doc.feed.entry)
        feedinfo = {
            u"label": unicode(doc.feed.id),
            u"type": u"Feed",
            u"title": unicode(doc.feed.title),
            u"link": [ l for l in doc.feed.link if l.rel == u"alternate" ][0].href,
            u"authors": [ unicode(a.name) for a in iter(doc.feed.author or []) ],
            u"updated": unicode(doc.feed.updated),
        }
    except AttributeError:
        try:
            doc_entries = iter(doc.entry)
            feedinfo = None
        except AttributeError:
            return None, []

    def process_entry(e):
        known_elements = [u'id', u'title', u'link', u'author', u'category', u'updated', u'content', u'summary']
        data = {
            u"label": unicode(e.id),
            u"type": u"Entry",
            u"title": unicode(e.title),
            #Nested list comprehension to select the alternate link,
            #then select the first result ([0]) and gets its href attribute
            u"link": [ l for l in e.link if l.rel == u"alternate" ][0].href,
            u"authors": [ unicode(a.name) for a in iter(e.author or []) ],
            #Nested list comprehension to create a list of category values
            u"categories": [ unicode(c.term) for c in iter(e.category or []) ],
            u"updated": unicode(e.updated),
            u"summary": unicode(e.summary),
        }
        if e.summary is not None:
            data[u"summary"] = unicode(e.summary)
        if e.content is not None:
            try:
                data[u"content_src"] = unicode(e.content.src)
            except AttributeError:
                data[u"content_text"] = unicode(e.content)
        for child in e.xml_elements:
            if child.xml_namespace != ATOM_NAMESPACE and child.xml_local not in known_elements:
                data[child.xml_local] = unicode(child)
        return data

    return feedinfo, [ process_entry(e) for e in doc_entries ]


def command_line_prep():
    from optparse import OptionParser
    usage = "%prog [options] wikibase outputdir"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--pattern",
                      action="store", type="string", dest="pattern",
                      help="limit the pages treated as Atom entries to those matching this pattern")
    return parser


def main(argv=None):
    #But with better integration of entry points
    if argv is None:
        argv = sys.argv
    # By default, optparse usage errors are terminated by SystemExit
    try:
        optparser = command_line_prep()
        options, args = optparser.parse_args(argv[1:])
        # Process mandatory arguments with IndexError try...except blocks
        try:
            wikibase = args[0]
            try:
                outputdir = args[1]
            except IndexError:
                optparser.error("Missing output directory")
        except IndexError:
            optparser.error("Missing Wiki base URL")
    except SystemExit, status:
        return status
    rewrite = args[2] if len(args) > 1 else None

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.
    pattern = options.pattern and options.pattern.decode('utf-8')

    moin2atomentries(wikibase, outputdir, rewrite, pattern)
    return


def doctest_example():
    """Return the factorial of n, an exact integer >= 0.

    If the result is small enough to fit in an int, return an int.
    Else return a long.

    >>> [factorial(n) for n in range(6)]
    [1, 1, 2, 6, 24, 120]
    >>> factorial(-1)
    Traceback (most recent call last):
        ...
    ValueError: n must be >= 0

    Factorials of floats are OK, but the float must be an exact integer:
    """
    pass

def test():
    import doctest
    doctest.testmod()
    return


def run(source, normalize):
    doc = bindery.parse(source, model=MODEL)
    #print doc.labels.xml_model.generate_metadata(doc)
    #import pprint
    #pprint.pprint(doc.feed.xml_model.generate_metadata(doc))
    metadata = doc.feed.xml_model.generate_metadata(doc)
    raw_feeddata = {}
    for eid, row in groupby(sorted(metadata, key=itemgetter(0)), itemgetter(0)):
        entity = defaultdict(list)
        for r in row:
            entity[r[1]].append(r[2])
        raw_feeddata[eid] = entity
        #Warning: this is OK since client code would usually not try to mutate raw_feeddata
        #But if it does, it should be mindful of the use of defaultdict
        #If this is a problem, unwrap to regular dicts:
        #for k in raw_feeddata: raw_feeddata[k] = dict(raw_feeddata[k])
    import pprint
    pprint.pprint(raw_feeddata)
    feeddata = {}
    return


RSS_CONTENT_NAMESPACE = u"http://purl.org/rss/1.0/modules/content/"
RSS10_NAMESPACE = u"http://purl.org/rss/1.0/"

def atom2rss1(isrc):
    doc = bindery.parse(isrc, model=FEED_MODEL)
    converter = atom_content_handlers()
    doc.feed.xml_namespaces[u'a'] = ATOM_NAMESPACE
    doc.feed.xml_namespaces[u'html'] = XHTML_NAMESPACE
    buf = StringIO()
    structwriter(indent=u"yes", stream=buf).feed(
        converter.dispatch(doc.feed)
    )
    return buf.getvalue()


#
class atom_content_handlers(dispatcher):
    '''
    A dispatcher for converting Atom to RSS 1.0
    '''
    MAX_ITEM_DESC = 500
    @node_handler(u'a:feed')
    def feed(self, node):
        yield E((RDF_NAMESPACE, u'rdf:RDF'),
            NS(u'dc', DC_NAMESPACE),
            NS(u'content', RSS_CONTENT_NAMESPACE),
            E((RSS10_NAMESPACE, u'channel'), {(u'rdf:about'): node.xml_avt(u"{a:link[@rel='alternate']/@href}")},
                E((RSS10_NAMESPACE, u'title'), self.text_construct(node.title)),
                E((RSS10_NAMESPACE, u'description'), self.text_construct(node.subtitle)),
                E((RSS10_NAMESPACE, u'link'), node.xml_avt(u"{a:link[@rel='alternate']/@href}")),
                E((RSS10_NAMESPACE, u'items'),
                    E((RDF_NAMESPACE, u'rdf:Seq'),
                        chain(*imap(partial(self.dispatch, mode=u'index'), node.entry))
                    )
                )
            ),
            chain(*imap(partial(self.dispatch, mode=u'full'), node.entry))
        )

    @node_handler(u'a:entry', mode=u'index')
    def entry_index(self, node):
        yield E((RDF_NAMESPACE, u'rdf:li'),
            node.xml_avt(u"{a:link[@rel='alternate']/@href}")
        )

    @node_handler(u'a:entry', mode=u'full')
    def entry_full(self, node):
        yield E((RSS10_NAMESPACE, u'item'),  {(u'rdf:about'): node.xml_avt(u"{a:link[@rel='alternate']/@href}")},
        E((RSS10_NAMESPACE, u'title'), self.text_construct(node.title)),
        E((RSS10_NAMESPACE, u'description'), self.description(node)),
        E((RSS_CONTENT_NAMESPACE, u'content:encoded'), self.text_construct(node.summary or node.content)),
        E((DC_NAMESPACE, u'dc:date'), node.updated),
        [ E((DC_NAMESPACE, u'dc:subject'), s.term) for s in iter(node.category or []) ],
        E((RSS10_NAMESPACE, u'link'), node.xml_avt(u"{a:link[@rel='alternate']/@href}")),
        )

    def description(self, node):
        if node.summary:
            d = unicode(node.summary)
        else:
            d = unicode(node.content)
        if len(d) > self.MAX_ITEM_DESC:
            d = d[:self.MAX_ITEM_DESC] + u'\n...[Truncated]'
        return d

    @node_handler(u'html:*')
    def html_elem(self, node):
        yield E(node.xml_local, node.xml_attributes.copy(),
            chain(*imap(self.dispatch, node.xml_children))
        )

    def text_construct(self, node):
        #FIXME: Need to fix a nasty bug in models before using node.type
        type_ = node.xml_avt(u"{@type}")
        #FIXME: will be None, not u'' when said bug is fixed
        if type_ in [u'', u'text']:
            yield unicode(node)
        elif type_ == u'xhtml':
            buf = StringIO()
            w = structwriter(indent=u"yes", stream=buf, encoding='utf-8')
            for child in node.xml_select(u'html:div/node()'):
                w.feed(self.dispatch(child))
            encoded = buf.getvalue().decode('utf-8')
            #print (encoded,)
            yield encoded
