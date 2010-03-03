# -*- encoding: utf-8 -*-
#Tools for working with atom Syntax (RFC 4287)

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
from amara.lib import inputsource
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
  'ATOM_IMT', 'PREFIXES', 'DEFAULT_SKEL',
  'tidy_content_element', 'feed', 'aggregate_entries',
  'ejsonize', 'entry_metadata',
  'author', 'link', 'category',
]

#
#Basic schematic models
#

#From 1.1 of the spec
ENTRY_MODEL_XML = """<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/xml3k/akara/xmlmodel" ak:resource="atom:id">
   <ak:rel name="'type'" value="'atom:entry'"/>
   <ak:rel name="'alternate_link'" value='atom:link[@rel="alternate"]/@href' />
   <ak:rel name="'self_link'" value='atom:link[not(@rel) or @rel="self"]/@href' />
   <atom:id ak:rel="local-name()"/>
   <atom:title type="xhtml" ak:rel="local-name()"/>
   <atom:updated ak:rel="local-name()"></atom:updated>
   <atom:published ak:rel="local-name()"></atom:published>
   <atom:link rel="self" eg:occurs="*" ak:rel="concat(local-name(), '_', @rel)" ak:value="@href" />
   <atom:summary type="xhtml" ak:rel="local-name()"/>
   <atom:category eg:occurs="*" ak:rel="local-name()"/>
   <!--
   <atom:author eg:occurs="*" ak:rel="local-name()" ak:resource="(atom:name|atom:uri|atom:email)[1]">
   -->
   <atom:author eg:occurs="*" ak:rel="local-name()">
     <ak:rel name="'type'" value="'atom:author'"/>
     <atom:name ak:rel="local-name()" ak:value="." />
     <atom:uri ak:rel="local-name()" ak:value="." />
     <atom:email ak:rel="local-name()" ak:value="." />
   </atom:author>
   <atom:content type="xhtml" eg:occurs="?" ak:rel="local-name()" ak:value="."/> 
 </atom:entry>"""

FEED_MODEL_XML = """<atom:feed xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/xml3k/akara/xmlmodel" ak:resource="atom:id">
  <ak:rel name="'type'" value="'atom:feed'"/>
  <ak:rel name="'alternate_link'" value='atom:link[@rel="alternate"]/@href' />
  <ak:rel name="'self_link'" value='atom:link[not(@rel) or @rel="self"]/@href' />
  <atom:title ak:rel="local-name()"></atom:title>
  <atom:subtitle ak:rel="local-name()"></atom:subtitle>
  <atom:updated ak:rel="local-name()"></atom:updated>
 <!--
 <atom:author eg:occurs="*" ak:rel="local-name()" ak:resource="(atom:name|atom:uri|atom:email)[1]">
 -->
  <atom:author eg:occurs="*" ak:rel="local-name()">
    <ak:rel name="'type'" value="'atom:author'"/>
    <atom:name ak:rel="local-name()"/>
    <atom:uri ak:rel="local-name()"/>
    <atom:email ak:rel="local-name()"/>
  </atom:author>
  <atom:id ak:rel="local-name()"></atom:id>
  <atom:link rel="self" eg:occurs="*" ak:rel="concat(local-name(), '_', @rel)" ak:value="@href" />
  <atom:rights ak:rel="local-name()"></atom:rights>
%s
</atom:feed>
""" % ENTRY_MODEL_XML

FEED_MODEL = examplotron_model(FEED_MODEL_XML)
ENTRY_MODEL = examplotron_model(ENTRY_MODEL_XML)

ATOM_IMT = u'application/atom+xml'

PREFIXES = {COMMON_NAMESPACES[ATOM_NAMESPACE]: ATOM_NAMESPACE, COMMON_NAMESPACES[ATOMTHR_EXT_NAMESPACE]: ATOMTHR_EXT_NAMESPACE}

SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)

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

#
#Utility functions
#

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


def tidy_content_element(root, check=u'//atom:title|//atom:summary|//atom:content', prefixes=PREFIXES):
    """
    Takes all Atom content elements with type=html (i.e. a:title, a:summary or a:content)
    And convert them to be of type=xhtml

    This operation mutates root in place.

    Example:

    import amara; from util import tidy_content_element
    A = '<entry xmlns="http://www.w3.org/2005/Atom"><id>urn:bogus:x</id><title type="html">&lt;div&gt;x&lt;p&gt;y&lt;p&gt;&lt;/div&gt;</title></entry>'
    doc = amara.parse(A)
    tidy_content_element(doc)
    doc.xml_write()
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
class author(object):
    def __init__(self, node):
        self.name = node.name
        self.uri = node.uri
        self.email = node.email
        self.node = node
    
class category(object):
    def __init__(self, node):
        self.scheme = node.scheme
        self.term = node.term
        self.node = node
    

class link(object):
    def __init__(self, node):
        self.rel = node.rel
        self.href = node.href
        self.node = node

#
RSS_CONTENT_NAMESPACE = u"http://purl.org/rss/1.0/modules/content/"
RSS10_NAMESPACE = u"http://purl.org/rss/1.0/"

#
#An atom feed as a proper specialized version of bindery
#

class feed(bindery.nodes.entity_base):
    '''
    Class to facilitate building Atom feeds
    '''
    #If you override __init__ and change the signature, you must also override __new__
    def __new__(cls, document_uri=None, feedxml=None, skel=None, title=None, updated=None, id=None):
        return bindery.nodes.entity_base.__new__(cls, document_uri)

    def __init__(self, feedxml=None, skel=None, title=None, updated=None, id=None):
        '''
        skel - an input source with a starting Atom document, generally a skeleton
        '''
        #WARNING: id global masked herein
        bindery.nodes.entity_base.__init__(self, document_uri)
        source = feedxml or skel or DEFAULT_SKEL
        source = bindery.parse(source, model=FEED_MODEL)
        #FIXME: need copy.deepcopy implemented to ease this
        for child in source.xml_children:
            self.xml_append(child)
        if title:
            self.feed.title = title
        if id:
            self.feed.id = id
        if not self.feed.id:
            raise ValueError("Must supply id in skel or id kwarg")
        #if not(hasattr)
        #self.feed.xml_append(E((ATOM_NAMESPACE, u'updated'), updated or datetime.now().isoformat()))
        self.feed.updated = updated or datetime.now().isoformat()
        return

    @staticmethod
    def from_rss2(feedxml):
        '''
        feedxml - an input source with an RSS 2.0 document
        '''
        source = bindery.parse(feedxml)#, model=FEED_MODEL)
        title = html.markup_fragment(str(source.rss.channel.title)).body.xml_encode()
        updated = unicode(source.rss.channel.pubDate)
        link = unicode(source.rss.channel.link)
        f = feed(title=title, updated=updated, id=link)
        #FIXME: Add description
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
        updated = updated or datetime.now().isoformat()
        entry = self.xml_element_factory(ATOM_NAMESPACE, u'entry')
        #entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'id', content=id_))
        entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'id'))
        entry.id.xml_append(U(id_))
        entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'updated'))
        entry.updated.xml_append(U(updated))
        #Only supports text titles, for now
        entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'title'))
        entry.title.xml_append(U(title))
        for link in links:
            (href, rel) = link
            entry.xml_append(E((ATOM_NAMESPACE, u'link'), {u'href': href, u'rel': rel}))
        for category in categories:
            entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'category'))
            try:
                term, scheme = category
            except TypeError:
                term, scheme = category, None
            entry.category[-1].xml_attributes[u'term'] = U(term)
            if scheme: entry.category[-1].xml_attributes[u'scheme'] = U(scheme)
        for author in authors:
            entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'author'))
            (name, email, uri) = author
            entry.author[-1].xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'name'))
            entry.author[-1].name.xml_append(U(name))
            if email:
                entry.author[-1].xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'email'))
                entry.author[-1].name.xml_append(U(email))
            if uri:
                entry.author[-1].xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'uri'))
                entry.author[-1].uri.xml_append(U(uri))
        for elem in elements:
            buf = StringIO()
            w = structwriter(indent=u"yes", stream=buf)
            w.feed(elem)
            entry.xml_append_fragment(buf.getvalue())
        #FIXME: Support other content types
        if summary:
            entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'summary'))
            entry.summary.xml_attributes[u'type'] = u'text'
            entry.summary.xml_append(U(summary))
        if content:
            entry.xml_append(self.xml_element_factory(ATOM_NAMESPACE, u'content'))
            entry.content.xml_attributes[u'type'] = u'text'
            entry.content.xml_append(U(content))
        self.feed.xml_append(entry)
        return

    #
    def rss1format(self):
        '''
        Return export as string in RSS 1.0 format
        '''
        #doc = bindery.parse(isrc, model=FEED_MODEL, prefixes={u'a', ATOM_NAMESPACE})
        converter = self.atom_2rss1()
        self.feed.xml_namespaces[u'a'] = ATOM_NAMESPACE
        self.feed.xml_namespaces[u'html'] = XHTML_NAMESPACE
        buf = StringIO()
        structwriter(indent=u"yes", stream=buf).feed(
            converter.dispatch(self.feed)
        )
        return buf.getvalue()

    #
    class atom_2rss1(dispatcher):
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

#
def entry_metadata(isrc):
    '''
    Organize the metadata of an atom document according to its entries
    '''
    #metadata = doc.xml_model.generate_metadata(doc)
    #delimited = groupby(metadata, lambda row: (row[1:] == (u'type', u'atom:entry') ))
    #first, rows = delimited.next()
    def handle_row(resource, rel, val):
        #if rel in [u"id", u"title"]:
        if rel == u"author":
            yield rel, (unicode(val[0].name), unicode(val[0].email), unicode(val[0].uri))
        if rel == u"link":
            yield rel, (val[0].rel, unicode(val[0]))
        if rel in [u"title", u"updated"]:
            yield rel, unicode(val[0])
        if rel in [u"id"]:
            yield rel, unicode(val[0])
            yield u"label", unicode(val[0])
        #u"link": [ l for l in doc.feed.link if l.rel == u"alternate" ][0].href,
        #u"authors": [ unicode(a.name) for a in iter(doc.feed.author or []) ],
        #u"updated": unicode(doc.feed.updated),

    if not first:
        #Must be a full feed, so consume the first entry's delimiter
        first, rows = delimited.next()
    entries = []
    for isboundary, rows in delimited:
        entryinfo = {u"type": u"atom:entry"}
        if isboundary:
            #consume/skip the entry's delimiter
            continue
        for k, v in (kvpair for row in rows for kvpair in handle_row(*row)):
            print k, v
        #print isboundary, list(rows)
        entries.append(entryinfo)

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
    return


def deserialize_text_construct(node):
    #FIXME: Need to fix a nasty bug in models before using node.type
    type_ = node.type
    if type_ in [None, u'text', u'html']:
        return unicode(node)
    elif type_ == u'xhtml':
        encoded = node.div.xml_encode()
        return encoded


def ejsonize(isrc):
    '''
    Convert Atom syntax to a dictionary
    Note: the conventions used are designed to simplify conversion to Exhibit JSON
    (see: http://www.ibm.com/developerworks/web/library/wa-realweb6/ ; listing 3)
    '''
    doc = bindery.parse(isrc, model=FEED_MODEL)
    def process_entry(e):
        known_elements = [u'id', u'title', u'link', u'author', u'category', u'updated', u'content', u'summary']
        data = {
            u"id": unicode(e.id),
            #XXX Shall we use title for label?
            u"label": unicode(e.id),
            u"type": u"Entry",
            u"title": unicode(e.title),
            u"link": first_item([ l.href for l in e.link if l.rel in [None, u"alternate"] ], []),
            #Nested list comprehension to select the alternate link,
            #then select the first result ([0]) and gets its href attribute
            u"authors": [ unicode(a.name) for a in iter(e.author or []) ],
            #Nested list comprehension to create a list of category values
            u"categories": [ unicode(c.term) for c in iter(e.category or []) ],
            u"updated": unicode(e.updated),
            u"summary": unicode(e.summary),
        }
        if not data[u"categories"]: del data[u"categories"]
        if e.summary is not None:
            data[u"summary"] = unicode(e.summary)
        if e.content is not None:
            try:
                data[u"content_src"] = unicode(e.content.src)
            except AttributeError:
                data[u"content_text"] = deserialize_text_construct(e.content)
        for child in e.xml_elements:
            if child.xml_namespace != ATOM_NAMESPACE and child.xml_local not in known_elements:
                data[child.xml_local] = unicode(child)
        return data

    try:
        doc_entries = iter(doc.feed.entry)
        feedinfo = {
            u"id": unicode(doc.feed.id),
            #XXX Shall we use title for label?
            u"label": unicode(doc.feed.id),
            u"type": u"Feed",
            u"title": unicode(doc.feed.title),
            u"link": first_item([ l.href for l in doc.feed.link if l.rel in [None, u"alternate"] ], []),
            u"authors": [ unicode(a.name) for a in iter(doc.feed.author or []) ],
            u"updated": unicode(doc.feed.updated),
        }
    except AttributeError:
        try:
            doc_entries = iter(doc.entry)
            feedinfo = None
        except AttributeError:
            #FIXME L10N
            raise ValueError("Does not appear to be a valid Atom file")

    return [ process_entry(e) for e in doc_entries ]

