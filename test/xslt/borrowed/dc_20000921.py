########################################################################
# test/xslt/dc_20000921.py
#David Carlisle <davidc@nag.co.uk> demonstrates drawing NS data out of attributes
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_ns_data_in_attributes_dc_20000921(xslt_test):
    source = stringsource("""<x>

<xsd:schema xmlns:xsd="http://www.w3.org/1999/XMLSchema">
	<xsd:element name="swissBankAccountNo" type="xsd:string"/>
</xsd:schema>

<schema xmlns="http://www.w3.org/1999/XMLSchema">
	<element name="luxembourgBankAccountNo" type="string"/>
</schema>

<xsd:schema xmlns:xsd="http://www.w3.org/1999/XMLSchema">
	<xsd:element name="englishBankAccountNo" type="xsd:string2"/>
</xsd:schema>

<schema xmlns="http://www.w3.org/1999/XMLSchema">
	<element name="frenchBankAccountNo" type="string2"/>
</schema>

<xsd:schema xmlns:xsd="file:/notschema">
	<xsd:element name="swissBankAccountNo2" type="xsd:string"/>
</xsd:schema>

<schema xmlns="file:/notschema">
	<element name="luxembourgBankAccountNo2" type="string"/>
</schema>

</x>""")
    transform = stringsource("""\
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xsd="http://www.w3.org/1999/XMLSchema"
>

<xsl:strip-space elements="*"/>

<xsl:output method="text" />

<xsl:template match="xsd:element">
  <xsl:text>&#10;Schema Element</xsl:text>
  <xsl:text>&#10;  name: </xsl:text>
  <xsl:value-of select="@name"/>
  <xsl:text>&#10;  type: </xsl:text>

  <xsl:variable name="p">
    <xsl:if test="contains(@type, ':')">
      <xsl:value-of select="substring-before(@type, ':')"/>
    </xsl:if>
  </xsl:variable>

  <xsl:variable name="n">
    <xsl:choose>
      <xsl:when test="contains(@type, ':')">
        <xsl:value-of  select="substring-after(@type, ':')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of  select="@type"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="ns" select="namespace::*[name()=$p]"/>

  <xsl:text>{</xsl:text>
  <xsl:value-of select="$ns"/>
  <xsl:text>} </xsl:text>
  <xsl:value-of select="$n"/>

  <xsl:text>&#10;  Elements with the same type are:&#10;</xsl:text>

  <xsl:for-each select="//xsd:element">
    <xsl:variable name="p2">
      <xsl:if test="contains(@type, ':')">
        <xsl:value-of select="substring-before(@type, ':')"/>
      </xsl:if>
    </xsl:variable>

    <xsl:variable name="n2">
      <xsl:choose>
        <xsl:when test="contains(@type, ':')">
          <xsl:value-of select="substring-after(@type, ':')"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="@type"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="ns2" select="namespace::*[name()=$p2]"/>

    <xsl:if test="$n=$n2 and $ns=$ns2">
      <xsl:text>    </xsl:text>
      <xsl:value-of select="@name"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
  </xsl:for-each>

</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """
Schema Element
  name: swissBankAccountNo
  type: {http://www.w3.org/1999/XMLSchema} string
  Elements with the same type are:
    swissBankAccountNo
    luxembourgBankAccountNo

Schema Element
  name: luxembourgBankAccountNo
  type: {http://www.w3.org/1999/XMLSchema} string
  Elements with the same type are:
    swissBankAccountNo
    luxembourgBankAccountNo

Schema Element
  name: englishBankAccountNo
  type: {http://www.w3.org/1999/XMLSchema} string2
  Elements with the same type are:
    englishBankAccountNo
    frenchBankAccountNo

Schema Element
  name: frenchBankAccountNo
  type: {http://www.w3.org/1999/XMLSchema} string2
  Elements with the same type are:
    englishBankAccountNo
    frenchBankAccountNo
"""

if __name__ == '__main__':
    test_main()
