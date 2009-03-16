#RFC 4287
#python atomtools.py copiasample.atom

import sys
from itertools import *
from operator import *
from collections import defaultdict

import re, copy
from cStringIO import StringIO
from datetime import datetime

import amara
from amara.namespaces import *
from amara.bindery import html
from amara.bindery.model import *
from amara import bindery


__all__ = ['ENTRY_MODEL', 'FEED_MODEL', '', '']

#__all__ = ['ENTRY_MODEL', 'FEED_MODEL', '', '', '', '', '']

#From 1.1 of the spec
ENTRY_MODEL_XML = """<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara" ak:resource="atom:id">
   <ak:rel name="'alternate_link'" value='atom:link[@rel="alternate"]/@href' />
   <ak:rel name="'type'" value="'atom:entry'"/>
   <atom:id ak:rel="local-name()" ak:value="."/>
   <atom:title type="xhtml" ak:rel="local-name()" ak:value="."/>
   <atom:updated ak:rel="local-name()" ak:value="."></atom:updated>
   <atom:published ak:rel="local-name()" ak:value="."></atom:published>
<!--
   <atom:link eg:occurs="?" ak:rel="concat(local-name(), '_self')" ak:value='descendant-or-self::atom:link[@rel="self"]/@href' />
   <atom:link eg:occurs="?" ak:rel="concat(local-name(), '_alternate')" ak:value='descendant-or-self::atom:link[@rel="alternate"]/@href' />
-->
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

ATOM_MT = u'application/atom+xml'

NSS = {COMMON_PREFIXES[ATOM_NAMESPACE]: ATOM_NAMESPACE}



'''
#From 1.1 of the spec
ENTRY_MODEL_XML = """<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara" ak:resource="atom:id">
   <atom:id ak:rel="local-name()" ak:value="."/>
   <atom:title ak:rel="local-name()" ak:value="."/>
   <atom:updated ak:rel="local-name()" ak:value="."></atom:updated>
   <atom:published ak:rel="local-name()" ak:value="."></atom:published>
   <atom:link eg:occurs="?" ak:rel="concat(local-name(), '_self')" ak:value='descendant-or-self::atom:link[@rel="self"]/@href' />
   <atom:link eg:occurs="?" ak:rel="concat(local-name(), '_alternate')" ak:value='descendant-or-self::atom:link[@rel="alternate"]/@href' />
   <atom:link eg:occurs="*" ak:rel="local-name()" ak:value="@href" />
   <atom:summary ak:rel="local-name()" ak:value="."></atom:summary>
   <atom:category eg:occurs="*" ak:rel="local-name()" ak:value="@term"/>
   <atom:author eg:occurs="*" ak:resource="(atom:name|atom:uri|atom:email)[1]">
     <atom:name ak:rel="local-name()" ak:value="." />
     <atom:uri ak:rel="local-name()" ak:value="." />
     <atom:email ak:rel="local-name()" ak:value="." />
   </atom:author>
   <atom:content eg:occurs="?" ak:rel="local-name()" ak:value="." /> 
 </atom:entry>"""

FEED_MODEL_XML = """<atom:feed xmlns:atom="http://www.w3.org/2005/Atom" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara" ak:resource="atom:id">
 <atom:title ak:rel="local-name()" ak:value="."></atom:title>
 <atom:subtitle ak:rel="local-name()" ak:value="."></atom:subtitle>
 <atom:updated ak:rel="local-name()" ak:value="."></atom:updated>
 <atom:author eg:occurs="*">
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
'''

FEED_MODEL = examplotron_model(FEED_MODEL_XML)
ENTRY_MODEL = examplotron_model(ENTRY_MODEL_XML)

def aggregate_entries(envelope, entries):
    '''
    envelope - input source of atom feed document to enclose entries
        if it has any entries, the new ones are appended
    entries - sequence of entry input sources
    '''
    envelope_doc = bindery.parse(envelope, model=FEED_MODEL)
    for entry in entries:
        entry_doc = bindery.parse(entry, model=ENTRY_MODEL)
        envelope_doc.feed.xml_append(entry_doc.entry)
    metadata = envelope_doc.feed.xml_model.generate_metadata(envelope_doc)
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
            unsouped = html.parse('<html>%s</html>'%node.xml_select(u'string(.)').encode('utf-8'))
            #amara.xml_print(unsouped, stream=sys.stderr)
            while node.xml_children: node.xml_remove(node.xml_first_child)
            newcontent = '<div xmlns="http://www.w3.org/1999/xhtml">'
            for child in unsouped.html.body.xml_children:
                s = StringIO()
                amara.xml_print(child, stream=s)
                newcontent += s.getvalue()
            newcontent += '</div>'
            node.xml_append(amara.parse(newcontent).xml_first_child)
            node.xml_attributes[None, u'type'] = u'xhtml'
            #for child in doc.html.body.xml_children:
            #    div.xml_append(child)
    return root

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



SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)

TYPE = 'type'
UPDATED = 'updated'
TITLE = 'title'
ID = 'id'

slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')[:20]

datetime_from_iso = lambda ds: datetime.strptime(ds, "%Y-%m-%dT%H:%M:%SZ")

path_from_datetime = lambda dt: '%i/%i'%dt.utctimetuple()[:2]

#def create_entry(doc):
#    for entry in doc.entry

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

def atomindex(entry):
    yield TYPE, ATOM_MT
    yield TITLE, unicode(entry.title)
    yield ID, unicode(entry.id)
    yield UPDATED, unicode(entry.updated)
    #yield TITLE, doc.xml_select(u'name(*)')


    

'''
fname = tempfile.mktemp('.xml')
driver.init_db(sqlite3.connect(fname))
drv = driver(sqlite3.connect(fname))
content = MONTY_XML
id = drv.create_resource(StringIO(content), metadata=dict(myindex(content)))
content1, metadata = drv.get_resource(id)
content1 = content1.read()
doc = amara.parse(content)
self.assertEqual(content, content1)
self.assertEqual(metadata[u'root-element-name'], doc.xml_select(u'name(*)'))
self.assertEqual(metadata[u'element-count'], doc.xml_select(u'count(//*)'))
return
'''


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


#Ideas borrowed from
# http://www.artima.com/forums/flat.jsp?forum=106&thread=4829

def command_line_prep():
    from optparse import OptionParser
    usage = "%prog [options] source cmd"
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--normalize",
                      action="store_false", dest="normalize", default=-False,
                      help="send a normalized version of the Atom to the console")
    #parser.add_option("-q", "--quiet",
    #                  action="store_false", dest="verbose", default=1,
    #                  help="don't print status messages to stdout", metavar="<PREFIX=URI>")
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
            source = args[0]
        except IndexError:
            optparser.error("Missing filename/URL to parse")
        #try:
        #    xpattern = args[1]
        #except IndexError:
        #    optparser.error("Missing main xpattern")
    except SystemExit, status:
        return status

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.

    #try:
    #    xpath = args[2].decode('utf-8')
    #except IndexError:
    #    xpath = None
    #xpattern = xpattern.decode('utf-8')
    #sentinel = options.sentinel and options.sentinel.decode('utf-8')
    #display = options.display and options.display.decode('utf-8')
    #prefixes = options.ns
    #limit = options.limit
    #if source == '-':
    #    source = sys.stdin
    print options.normalize
    #run(source, xpattern, xpath, limit, sentinel, display, prefixes)
    if options.test:
        test()
    else:
        run(source, options.normalize)
    return


if __name__ == "__main__":
    sys.exit(main(sys.argv))

