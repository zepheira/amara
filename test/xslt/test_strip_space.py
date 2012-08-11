#!/usr/bin/env python

import sys
from nose import with_setup

from amara.xslt.processor import processor
from amara.lib import inputsource

xslt_proc = None
source = None
trans = None

def setup_blank_text():
    global source
    global trans
    global xslt_proc

    _source1 = '''<?xml version="1.0"?>
<test>
  <item/>
  <item/>
  <item/>
</test>
'''

    _trans1 = '''<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:strip-space  elements="*"/>
  <xsl:template  match="/">
    <test>
      <xsl:apply-templates/>
    </test>
  </xsl:template>
  <xsl:template  match="item">
    <no>
      <xsl:value-of select="position()"/>
    </no>
  </xsl:template>
</xsl:stylesheet>
'''

    xslt_proc = processor()

    source = inputsource(_source1, None)
    trans = inputsource(_trans1, None)


@with_setup(setup_blank_text)
def test_blank_text():
    xslt_proc.append_transform(trans)
    res = xslt_proc.run(source)
    #print >> sys.stderr, res
    assert (res == '<?xml version="1.0" encoding="UTF-8"?><test><no>1</no><no>2</no><no>3</no></test>')


def setup_blank_node():
    global source
    global trans
    global xslt_proc

    _source1 = '''<?xml version="1.0"?>
<document>
<text>   </text>
</document>'''

    _trans1 = '''<?xml version='1.0'?>
<xsl:stylesheet version="1.0"
      xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text"/>
  <xsl:strip-space elements="*"/>

  <xsl:template match="/">
    <xsl:apply-templates select="//text"/>
  </xsl:template>

<xsl:template match="text">
Chars: <xsl:value-of select="string-length(text())"/>
</xsl:template>

</xsl:stylesheet>'''

    xslt_proc = processor()

    source = inputsource(_source1, None)
    trans = inputsource(_trans1, None)


@with_setup(setup_blank_node)
def test_blank_node():
    xslt_proc.append_transform(trans)
    res = xslt_proc.run(source)
    #print >> sys.stderr, res
    assert (res == '\nChars: 0')

