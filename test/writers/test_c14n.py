#Derived from: http://cvs.4suite.org/viewcvs/4Suite/test/Xml/Core/test_c14n.py?view=markup

import sys
import unittest
#from cStringIO import StringIO
import amara
from amara.writers import lookup

C14N_3_2 = '''\
<doc>
   <clean>   </clean>
   <dirty>   A   B   </dirty>
   <mixed>
      A
      <clean>   </clean>
      B
      <dirty>   A   B   </dirty>
      C
   </mixed>
</doc>'''

C14N_3_2_RESULT = '''\
<doc>
   <clean>   </clean>
   <dirty>   A   B   </dirty>
   <mixed>
      A
      <clean>   </clean>
      B
      <dirty>   A   B   </dirty>
      C
   </mixed>
</doc>'''

C14N_3_3 = '''\
<doc>
   <e1   />
   <e2   ></e2>
   <e3   name = "elem3"   id="elem3"   />
   <e4   name="elem4"   id="elem4"   ></e4>
   <e5 a:attr="out" b:attr="sorted" attr2="all" attr="I'm"
      xmlns:b="http://www.ietf.org"
      xmlns:a="http://www.w3.org"
      xmlns="http://example.org"/>
   <e6 xmlns="" xmlns:a="http://www.w3.org">
      <e7 xmlns="http://www.ietf.org">
         <e8 xmlns="" xmlns:a="http://www.w3.org">
            <e9 xmlns="" xmlns:a="http://www.ietf.org"/>
         </e8>
      </e7>
   </e6>
</doc>
'''
#Note: the official spec example has <!DOCTYPE doc [<!ATTLIST e9 attr CDATA "default">]>

C14N_3_3_RESULT = '''\
<doc>
   <e1></e1>
   <e2></e2>
   <e3 id="elem3" name="elem3"></e3>
   <e4 id="elem4" name="elem4"></e4>
   <e5 xmlns="http://example.org" xmlns:a="http://www.w3.org" xmlns:b="http://www.ietf.org" attr="I'm" attr2="all" b:attr="sorted" a:attr="out"></e5>
   <e6 xmlns:a="http://www.w3.org">
      <e7 xmlns="http://www.ietf.org">
         <e8 xmlns="">
            <e9 xmlns:a="http://www.ietf.org"></e9>
         </e8>
      </e7>
   </e6>
</doc>'''
#Note: the official spec example has <e9 xmlns:a="http://www.ietf.org" attr="default"></e9>


#DTD with attribute decls omitted
C14N_3_4 = '''\
<doc>
   <text>First line&#x0d;&#10;Second line</text>
   <value>&#x32;</value>
   <compute><![CDATA[value>"0" && value<"10" ?"valid":"error"]]></compute>
   <compute expr='value>"0" &amp;&amp; value&lt;"10" ?"valid":"error"'>valid</compute>
   <norm attr=' &apos;   &#x20;&#13;&#xa;&#9;   &apos; '/>
</doc>'''


#Result modified to reflect omitted DTD
C14N_3_4_RESULT = '''\
<doc>
   <text>First line&#xD;
Second line</text>
   <value>2</value>
   <compute>value&gt;"0" &amp;&amp; value&lt;"10" ?"valid":"error"</compute>
   <compute expr="value>&quot;0&quot; &amp;&amp; value&lt;&quot;10&quot; ?&quot;valid&quot;:&quot;error&quot;">valid</compute>
   <norm attr=" '    &#xD;&#xA;&#x9;   ' "></norm>
</doc>'''


EXCL_C14N_2_2_1 = '''\
<n0:local xmlns:n0="foo:bar"
    xmlns:n3="ftp://example.org">
    <n1:elem2 xmlns:n1="http://example.net"
        xml:lang="en">
        <n3:stuff xmlns:n3="ftp://example.org"/>
    </n1:elem2>
</n0:local>'''

EXCL_C14N_2_2_2 = '''\
<n2:pdu xmlns:n1="http://example.com"
        xmlns:n2="http://foo.example"
        xml:lang="fr"
        xml:space="retain">
    <n1:elem2 xmlns:n1="http://example.net"
              xml:lang="en">
        <n3:stuff xmlns:n3="ftp://example.org"/>
    </n1:elem2>
</n2:pdu>'''

EXCL_C14N_2_2_RESULT = '''\
<n1:elem2 xmlns:n1="http://example.net" xml:lang="en">\n        <n3:stuff xmlns:n3="ftp://example.org"></n3:stuff>\n    </n1:elem2>'''

EXSPEC_2_2_1_C14N_RESULT = '''\
<n1:elem2 xmlns:n0="foo:bar" xmlns:n1="http://example.net" xmlns:n3="ftp://example.org" xml:lang="en">
        <n3:stuff></n3:stuff>
    </n1:elem2>'''

EXSPEC_2_2_2_C14N_RESULT = '''\
<n1:elem2 xmlns:n1="http://example.net" xmlns:n2="http://foo.example" xml:lang="en" xml:space="retain">
        <n3:stuff xmlns:n3="ftp://example.org"></n3:stuff>
    </n1:elem2>'''


class Test_c14n_spec(unittest.TestCase):
    #Note: c14n spec is at: http://www.w3.org/TR/xml-c14n
    #exclusive c14n spec is at: http://www.w3.org/TR/xml-exc-c14n/
    "Test canonicalization spec"

    def test_c14n_3_2(self):
        'c14n spec 3.2'
        doc = amara.parse(C14N_3_2)
        self.assertEqual(doc.xml_encode('xml-canonical'), C14N_3_2_RESULT)
        
    def test_c14n_3_3(self):
        'c14n spec 3.3'
        doc = amara.parse(C14N_3_3)
        self.assertEqual(doc.xml_encode('xml-canonical'), C14N_3_3_RESULT)
        
    def test_c14n_3_4(self):
        'c14n spec 3.4'
        doc = amara.parse(C14N_3_4)
        self.assertEqual(doc.xml_encode('xml-canonical'), C14N_3_4_RESULT)
        
    #
    def test_exc_c14n_2_2_1(self):
        '1st regular c14n example from exclusive spec sect 2.2'
        doc = amara.parse(EXCL_C14N_2_2_1)
        elem2 = doc.xml_select(u'//*[local-name() = "elem2"]')[0]
        self.assertEqual(elem2.xml_encode('xml-canonical', exclusive=True), EXSPEC_2_2_1_C14N_RESULT)
    
    def test_exc_c14n_2_2_2(self):
        '2nd regular c14n example from exclusive spec sect 2.2'
        doc = amara.parse(EXCL_C14N_2_2_2)
        elem2 = doc.xml_select(u'//*[local-name() = "elem2"]')[0]
        self.assertEqual(elem2.xml_encode('xml-canonical', exclusive=True), EXSPEC_2_2_2_C14N_RESULT)
    

if __name__ == '__main__':
    raise SystemExit("use nosetests")
