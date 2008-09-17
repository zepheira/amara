#!/usr/bin/env python
"""
A command line tool for running reports on XML files.

trimxslt allows you to rapidly extract details from large XML files
on the command line.

Run "trimxslt --help" for details of the command line parameters, but
here are some pointers to get you started.

Let's say you have a simple database dump format with the following
form:

<db>
  <record id="1">
    <name>Alex</name>
    <address>123 Maple St.</address>
  </record>
  <record id="2">
    <name>Bob</name>
    <address>456 Birch Rd.</address>
  </record>
  <record id="3">
    <name>Chris</name>
    <address>789 Pine St.</address>
  </record>
</db>

You can:

Get all the full contents of name elements

$ inspectxml file.xml name
<name>Alex</name>
<name>Bob</name>
<name>Chris</name>

Get the full contents of the record with ID 2

$ inspectxml file.xml record "@id='2'"
<record id="2">
    <name>Bob</name>
    <address>456 Birch Rd.</address>
  </record>

Get the full contents of the first two name elements

$ inspectxml -c 2 file.xml name
<name>Alex</name>
<name>Bob</name>

Get the name of the record with ID 2

$ inspectxml -d "name" file.xml record "@id='2'"
<name>Bob</name>

You could display the id and each correspoding name as follows:

$ inspectxml file.xml "@id|name"
1
<name>Alex</name>
2
<name>Bob</name>
3
<name>Chris</name>

Or a more precise approach might be (demonstrating the use of XPath functions):

$ inspectxml -d "concat(@id, ': ', name)" file.xml record
1: Alex
2: Bob
3: Chris

inspectxml uses namespaces declared on the document element, so you can
conveniently make queries without needing to separately declare prefixes.
So to get the URLs of all a links in an XHTML document you could do:

inspectxml -d "@href" file.xhtml "html:a"

As long as there is a namespace declaration
xmlns:ht="http://www.w3.org/1999/xhtml" in the document.  If not
(many XHTML documents use the default namespace, which courtesy XPath 1.0
restrictions prevents inspectxml from doing any guesswork for you) you have
to declare the prefix.

inspectxml --ns=ht="http://www.w3.org/1999/xhtml" -d "@href" http://www.w3.org/2000/07/8378/xhtml/media-types/test4.xhtml "ht:a"

Notice how this example loads the source XML (XHTML) from a Web URL rather than a local file.  Of course, a shortcut for this is simply:

inspectxml http://www.w3.org/2000/07/8378/xhtml/media-types/test4.xhtml "@href"

"""
#The following won't work because EXSLT is only supported in XsltContext and we use Ft.Xml.XPath.Context
#We can probably revisit when we make bindery nodes subclasses of Domlette
#inspectxml --ns=str="http://exslt.org/strings" -d "str:replace(., 'http://', '')" http://www.w3.org/2000/07/8378/xhtml/media-types/test4.xhtml "@href"

import os
import re
import sys
import codecs
import optparse
#import cStringIO
import amara
#from amara import tree

#from xml.dom import EMPTY_NAMESPACE as NULL_NAMESPACE
#from xml.dom import EMPTY_PREFIX as NULL_PREFIX


#FIXME: Use 4Suite L10N
def _(t): return t


def run(source, xpattern, xpath, limit, sentinel, display, prefixes):
    prefixes = prefixes or {}
    try:
        prefixes = dict([ p.split('=') for p in prefixes ])
    except ValueError:
        raise ValueError("Invalid prefix declaration")
    #if hasattr(source, 'read'):
    #    if hasattr(source, 'rewind'):
    #        nss = saxtools.sniff_namespace(source)
    #        source.rewind()
    #    else:
    #        source = source.read()
    #        nss = saxtools.sniff_namespace(source)
    #else:
    #    nss = saxtools.sniff_namespace(source)
    #nss.update(prefixes)
    nss = prefixes
    doc = amara.parse(source)
    #nodes = amara.pushbind(source, xpattern, prefixes=nss)
    count = 0
    search_space = doc.xml_select(u'//' + xpattern.lstrip(u'//'))
    #FIXME: Until we have something pushbind-like trim all nodes not in the search space 
    for node in search_space:
        if not xpath or node.xml_select(xpath):
            count += 1
            if display:
                #Print specified subset
                result = node.xml_select(display)
                if hasattr(result, 'next'):
                    #print '\n'.join([ n.xml_type == tree.attribute.xml_type and n.xml_value or amara.xml_print(n) for n in result ])
                    print '\n'.join( (n.xml_type == tree.attribute.xml_type and n.xml_value or amara.xml_print(n) for n in result) )
                else:
                    print result
            else:
                #Print the whole thing
                try:
                    amara.xml_print(node)
                except AttributeError:
                    print unicode(node).encode('utf-8')
            if limit != -1 and count >= limit:
                break
        if sentinel and node.xml_select(sentinel):
            break
        print
    return


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def command_line_prep():
    from optparse import OptionParser
    usage = "%prog [options] source xpattern [xpath]"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--limit",
                      action="store", type="int", dest="limit", default=-1,
                      help="limit the number of xpattern matches retrieved; files will not be parsed beyond this number, so it serves as optimization", metavar="NUMBER")
    parser.add_option("-d", "--display",
                      action="store", type="string", dest="display",
                      help="xpath expression indicating what nodes to be displayed from matched and screened patterns", metavar="XPATH")
    parser.add_option("-n", "--ns",
                      action="append", type="string", dest="ns",
                      help="prefix to namespace mapping", metavar="<PREFIX=URI>")
    parser.add_option("--sentinel",
                      action="store", type="string", dest="sentinel",
                      help="xpath expression to be checked for each pattern match.  If true it causes the   reporting to stop, with no further parsing", metavar="XPATH")
    #parser.add_option("-q", "--quiet",
    #                  action="store_false", dest="verbose", default=1,
    #                  help="don't print status messages to stdout")
    return parser


def main(argv=None):
    #Ideas borrowed from
    # http://www.artima.com/forums/flat.jsp?forum=106&thread=4829
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
        try:
            xpattern = args[1]
        except IndexError:
            optparser.error("Missing main xpattern")
    except SystemExit, status:
        return status

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.
    try:
        xpath = args[2].decode('utf-8')
    except IndexError:
        xpath = None
    xpattern = xpattern.decode('utf-8')
    sentinel = options.sentinel and options.sentinel.decode('utf-8')
    display = options.display and options.display.decode('utf-8')
    prefixes = options.ns
    limit = options.limit
    if source == '-':
        source = sys.stdin
    run(source, xpattern, xpath, limit, sentinel, display, prefixes)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

