########################################################################
# test/xslt/ss_20010301.py
#Stefan Seefeld <seefeld@sympatico.ca> has trouble with the docbook stylesheets

import os, re
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib.Uri import OsPathToUri

# The name of the environment variable that will indicate
# the location of DocBook XSL docbook-xsl-#.#.# directory
KEYNAME = 'DOCBOOK_HOME'

MIN_VERSION = '1.64.0'
# NOTE: there is a '%s' for the actual version of docbook used
#
# docbook-xsl-1.68.0 and up
expected_1_1680 = """\
<html><head><meta content="text/html; charset=ISO-8859-1" http-equiv="Content-Type"><title></title><meta content="DocBook XSL Stylesheets V%s" name="generator"></head><body alink="#0000FF" bgcolor="white" vlink="#840084" link="#0000FF" text="black"><div lang="en" class="book"><div class="titlepage"><hr></div><div class="toc"><p><b>Table of Contents</b></p><dl><dt><span class="chapter"><a href="#id3">1. Chapter</a></span></dt><dd><dl><dt><span class="sect1"><a href="#id2">Sect1</a></span></dt><dd><dl><dt><span class="sect2"><a href="#id1">Sect2</a></span></dt></dl></dd></dl></dd></dl></div><div lang="en" class="chapter"><div class="titlepage"><div><div><h2 class="title"><a name="id3"></a>Chapter&nbsp;1.&nbsp;Chapter</h2></div></div></div><div class="toc"><p><b>Table of Contents</b></p><dl><dt><span class="sect1"><a href="#id2">Sect1</a></span></dt><dd><dl><dt><span class="sect2"><a href="#id1">Sect2</a></span></dt></dl></dd></dl></div><div lang="en" class="sect1"><div class="titlepage"><div><div><h2 style="clear: both" class="title"><a name="id2"></a>Sect1</h2></div></div></div><div lang="en" class="sect2"><div class="titlepage"><div><div><h3 class="title"><a name="id1"></a>Sect2</h3></div></div></div></div></div></div></div></body></html>"""

# docbook-xsl-1.64.0(?) and up;
expected_1_640 = """\
<html><head><meta content="text/html; charset=ISO-8859-1" http-equiv="Content-Type"><title></title><meta content="DocBook XSL Stylesheets V%s" name="generator"></head><body alink="#0000FF" bgcolor="white" vlink="#840084" link="#0000FF" text="black"><div lang="en" class="book"><div class="titlepage"><div></div><div></div><hr></div><div class="toc"><p><b>Table of Contents</b></p><dl><dt><span class="chapter"><a href="#id3">1. Chapter</a></span></dt><dd><dl><dt><span class="sect1"><a href="#id2">Sect1</a></span></dt><dd><dl><dt><span class="sect2"><a href="#id1">Sect2</a></span></dt></dl></dd></dl></dd></dl></div><div lang="en" class="chapter"><div class="titlepage"><div><div><h2 class="title"><a name="id3"></a>Chapter&nbsp;1.&nbsp;Chapter</h2></div></div><div></div></div><div class="toc"><p><b>Table of Contents</b></p><dl><dt><span class="sect1"><a href="#id2">Sect1</a></span></dt><dd><dl><dt><span class="sect2"><a href="#id1">Sect2</a></span></dt></dl></dd></dl></div><div lang="en" class="sect1"><div class="titlepage"><div><div><h2 style="clear: both" class="title"><a name="id2"></a>Sect1</h2></div></div><div></div></div><div lang="en" class="sect2"><div class="titlepage"><div><div><h3 class="title"><a name="id1"></a>Sect2</h3></div></div><div></div></div></div></div></div></div></body></html>"""


class test_xslt_docbook_ss_20010301(xslt_test):
    source = stringsource("""\
<book>
  <chapter>
    <title>Chapter</title>
    <sect1>
      <title>Sect1</title>
      <sect2>
        <title>Sect2</title>
      </sect2>
    </sect1>
  </chapter>
</book>
""")
    transform = ""
    parameters = {}
    expected = ""

    # def test_transform(self):
    #     import sys
    #     from amara.xslt import transform
    # 
    #     dirs = ["/usr/share/sgml/docbook/xsl-stylesheets", #default for docbook-style-xsl RPM
    #             "/usr/local/share/xsl/docbook", #default for FreeBSD textproc/docbook-xsl port
    #            ]
    # 
    #     DOCBOOK_DIR = None
    #     for dir in dirs:
    #         if os.path.isdir(dir):
    #             DOCBOOK_DIR = dir
    #             break
    # 
    #     DOCBOOK_DIR = os.environ.get(KEYNAME, DOCBOOK_DIR)
    #     if not DOCBOOK_DIR:
    #         tester.warning(
    #             "You need Norm Walsh's DocBook XSL stylesheet package for this test.\n"
    #             "You can either ignore this, or you can install the DocBook XSL\n"
    #             "stylesheets and re-run this test. Get the docbook-xsl package from\n"
    #             "http://sourceforge.net/project/showfiles.php?group_id=21935\n"
    #             "Install it in anywhere, and then before running this test, set\n"
    #             "the environment variable %r to the absolute path\n"
    #             "of the docbook-xsl-#.#.# directory on your filesystem.\n"
    #             % KEYNAME)
    #         tester.testDone()
    #         return
    # 
    #     if not os.path.isdir(DOCBOOK_DIR):
    #         tester.warning("Unable to find DocBook stylesheet directory %r" % DOCBOOK_DIR)
    #         tester.testDone()
    #         return
    # 
    #     VERSION_FILE = os.path.join(DOCBOOK_DIR, 'VERSION')
    #     if os.path.isfile(VERSION_FILE):
    #         VERSION = open(VERSION_FILE).read()
    #         match = re.search(r'>\s*(\d[.0-9]+)\s*<', VERSION)
    #         if not match:
    #             tester.warning("Unable to determine version of DocBook stylesheets\n"
    #                            "Format of %r unrecognized." % VERSION_FILE)
    #             tester.testDone()
    #             return
    #         version = match.group(1)
    #         if version <= MIN_VERSION:
    #             tester.warning("DocBook XSL version %s or higher needed;"
    #                            " version %s found." % (MIN_VERSION, version))
    #             tester.testDone()
    #             return
    #     else:
    #         tester.warning("Unable to determine version of DocBook stylesheets\n"
    #                        "Was looking for file %r." % VERSION_FILE)
    #         tester.testDone()
    #         return
    # 
    #     STYLESHEET = os.path.join(DOCBOOK_DIR, 'html', 'docbook.xsl')
    #     if not os.path.isfile(STYLESHEET):
    #         tester.warning("Unable to find DocBook stylesheet %r" % STYLESHEET)
    #         tester.testDone()
    #         return
    # 
    #     STYLESHEET_URI = OsPathToUri(STYLESHEET)
    #     tester.testDone()
    # 
    #     source = test_harness.FileInfo(string=source_1)
    #     if version >= '1.68':
    #         expected = expected_1_1680 % version
    #     else:
    #         expected = expected_1 % version
    #     sheet = test_harness.FileInfo(uri=STYLESHEET_URI)
    #     test_harness.XsltTest(tester, source, [sheet], expected,
    #         title="Basic DocBook XSL processing")
    # 
    # 
    #     result = transform(self.source, self.transform, output=io)
    #     self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
    #     return

if __name__ == '__main__':
    test_main()
