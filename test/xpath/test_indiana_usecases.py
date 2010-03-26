XML = '''<listitem>
  <para>
    <ulink url="http://wiki.semiolabs.org/test/test/MacDonald#">MacDonald</ulink> TM. A European's perspective of COX-2 drug safety. J Cardiovasc Pharmacol. 2006;47 Suppl 1:S92-7. (<ulink url="http://wiki.semiolabs.org/test/test/PubMed#">PubMed</ulink>: <ulink url="http://www.ncbi.nlm.nih.gov/pubmed/16785838">16785838</ulink>)
  </para>
</listitem>
'''

import amara
from amara.xpath.datatypes import nodeset

def test_last_function_low_level():
    '''
    '''
    doc = amara.parse(XML)
    last_url = doc.xml_select(u'/listitem/para/ulink[position() = last()]/@url')
    EXPECTED = nodeset([u'http://www.ncbi.nlm.nih.gov/pubmed/16785838'])
    assert last_url == EXPECTED, (EXPECTED, last_url)

