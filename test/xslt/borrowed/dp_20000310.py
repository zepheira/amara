########################################################################
# test/xslt/dp_20000310.py
#Namespace tracer from Pawson, David <DPawson@rnib.org.uk> on 10 March 
# 2000, with a version using the namespace axis from David Carlisle.

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

commonsource = stringsource("""<?xml version='1.0'?>

<!DOCTYPE ns1:ns-test [
<!ELEMENT ns1:ns-test (block)+>
<!ATTLIST ns-test  xmlns:ns1 CDATA #FIXED "http://ns1.com"
          
>
<!ELEMENT ns2:block (para)+>
<!ATTLIST block  xmlns:ns2 CDATA #FIXED "http://ns2.com"
>
<!ELEMENT para (#PCDATA)>
<!ATTLIST para id ID #IMPLIED
               another CDATA #IMPLIED>]>

<ns1:ns-test xmlns:ns1= "http://ns1.com">

  <block>
    <para>Para in block 1, main document namespace </para>
  </block>

  <ns2:block xmlns:ns2="http://ns2.com">
    <para>Para in block 2</para>
  </ns2:block>

    <ns3:block xmlns:ns3="http://ns3.com">
      <long:para xmlns:long="A long namespace uri">Para in block
3</long:para>
    </ns3:block>


</ns1:ns-test>""")

class test_xslt_ns_tracer_1_dp_20000310(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version='1.0'?>

<xsl:stylesheet 
   version="1.0"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:ns-test="http://ns1.com"
   xmlns:ns1="http://ns1.com"
   xmlns:ns2="http://ns2.com"
   xmlns:long-namespace="http://ns3.com"
   exclude-result-prefixes="ns1 ns2 long-namespace"
>

<xsl:output method="xml" indent="yes"/>

<xsl:template match="*">
  <!--<xsl:message><xsl:value-of select="name(.)"/></xsl:message>-->
  <tag>Namespace:<xsl:choose><xsl:when test="namespace-uri(.)"><xsl:value-of select="namespace-uri(.)"/>
      </xsl:when>
      <xsl:otherwise> Null namespace</xsl:otherwise>
    </xsl:choose>
  </tag>
  <tag>name: <xsl:value-of select="name(.)"/></tag>
  <tag>local-name: <xsl:value-of select="local-name(.)"/></tag>
  <tag>Content: <xsl:value-of select="text()"/></tag>
  <xsl:if test="./*"><xsl:apply-templates/></xsl:if>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<tag>Namespace:http://ns1.com</tag>
<tag>name: ns1:ns-test</tag>
<tag>local-name: ns-test</tag>
<tag>Content: 

  </tag>

  <tag>Namespace: Null namespace</tag>
<tag>name: block</tag>
<tag>local-name: block</tag>
<tag>Content: 
    </tag>
    <tag>Namespace: Null namespace</tag>
<tag>name: para</tag>
<tag>local-name: para</tag>
<tag>Content: Para in block 1, main document namespace </tag>
  

  <tag>Namespace:http://ns2.com</tag>
<tag>name: ns2:block</tag>
<tag>local-name: block</tag>
<tag>Content: 
    </tag>
    <tag>Namespace: Null namespace</tag>
<tag>name: para</tag>
<tag>local-name: para</tag>
<tag>Content: Para in block 2</tag>
  

    <tag>Namespace:http://ns3.com</tag>
<tag>name: ns3:block</tag>
<tag>local-name: block</tag>
<tag>Content: 
      </tag>
      <tag>Namespace:A long namespace uri</tag>
<tag>name: long:para</tag>
<tag>local-name: para</tag>
<tag>Content: Para in block
3</tag>
    


"""

class test_xslt_ns_tracer_2_dp_20000310(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version='1.0'?>

<xsl:stylesheet 
   version="1.0" 
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:ns-test="http://ns1.com"
   xmlns:ns1="http://ns1.com"
   xmlns:ns2="http://ns2.com"
   xmlns:long-namespace="http://ns3.com"
   exclude-result-prefixes="ns1 ns2 long-namespace"
>

<xsl:output method="xml" indent="yes"/>

<xsl:template match="*">
  <tag>Namespace:<xsl:choose><xsl:when test="namespace-uri(.)"><xsl:value-of select="namespace-uri(.)"/>
    </xsl:when>
    <xsl:otherwise> Null namespace</xsl:otherwise>
  </xsl:choose>

  <!-- namespaces are unordered, sort is needed for comparision only -->
    <xsl:for-each select="namespace::*">
      <xsl:sort select="name()"/>
      NS name: <xsl:value-of select="name(.)"/>
      NS value : <xsl:value-of select="."/>
    </xsl:for-each>

  </tag>
  <xsl:if test="./*"><xsl:apply-templates/></xsl:if>
</xsl:template>

</xsl:stylesheet>
""")
    parameters = {}
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<tag>Namespace:http://ns1.com
      NS name: ns1
      NS value : http://ns1.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>

  <tag>Namespace: Null namespace
      NS name: ns1
      NS value : http://ns1.com
      NS name: ns2
      NS value : http://ns2.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>
    <tag>Namespace: Null namespace
      NS name: ns1
      NS value : http://ns1.com
      NS name: ns2
      NS value : http://ns2.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>
  

  <tag>Namespace:http://ns2.com
      NS name: ns1
      NS value : http://ns1.com
      NS name: ns2
      NS value : http://ns2.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>
    <tag>Namespace: Null namespace
      NS name: ns1
      NS value : http://ns1.com
      NS name: ns2
      NS value : http://ns2.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>
  

    <tag>Namespace:http://ns3.com
      NS name: ns1
      NS value : http://ns1.com
      NS name: ns3
      NS value : http://ns3.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>
      <tag>Namespace:A long namespace uri
      NS name: long
      NS value : A long namespace uri
      NS name: ns1
      NS value : http://ns1.com
      NS name: ns3
      NS value : http://ns3.com
      NS name: xml
      NS value : http://www.w3.org/XML/1998/namespace</tag>
    


"""
    
if __name__ == '__main__':
    test_main()
