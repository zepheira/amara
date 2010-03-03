import unittest
from amara.lib import testsupport
from amara import tree
import os
import re, tempfile
from amara.lib import U

from amara import bindery
from amara.bindery.model import generate_metadata
from amara.bindery.model.schematron import schematron_model


MODEL_A = '''<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" xmlns:ak="http://purl.org/xml3k/akara/xmlmodel">
  <title>Mailing labels</title>
  <pattern name="A label">
    <rule context="label">
      <ak:resource select="@id"/>
      <report test="@added">
        <ak:rel name="'date added'" value="."/>
      </report>
      <report test="name">
        <ak:rel name="" value="."/>
      </report>
      <report test="address">
        <ak:rel name="'place'" value="concat(city, ',', province)"/>
      </report>
      <report test="opus">
        <ak:rel name="" resource="."/>
      </report>
    </rule>
    <rule context="opus">
      <report test="@year">
        <ak:rel name="" value="."/>
      </report>
      <report test="title">
        <ak:rel name="" value="."/>
      </report>
    </rule>
  </pattern>
  <pattern name="Element paths">
    <rule context="/labels/label"/>
    <rule context="/labels/label/@id"/>
    <rule context="/labels/label/@added"/>
    <rule context="/labels/label/name"/>
    <rule context="/labels/label/address"/>
    <rule context="/labels/label/address/street"/>
    <rule context="/labels/label/address/city"/>
    <rule context="/labels/label/opus"/>
    <rule context="/labels/label/opus/@year"/>
    <rule context="/labels/label/quote"/>
  </pattern>
</schema>
'''

INSTANCE_A_1 = '''<?xml version="1.0" encoding="iso-8859-1"?>
<labels>
  <label id='ep' added="2003-06-10">
    <name>Ezra Pound</name>
    <address>
      <street>45 Usura Place</street>
      <city>Hailey</city>
      <province>ID</province>
    </address>
  </label>
  <label id='tse' added="2003-06-20">
    <name>Thomas Eliot</name>
    <address>
      <street>3 Prufrock Lane</street>
      <city>Stamford</city>
      <province>CT</province>
    </address>
    <opus>
      <title>The Wasteland</title>
    </opus>
    <tag>old possum</tag>
    <tag>poet</tag>
  </label>
  <label id="lh" added="2004-11-01">
    <name>Langston Hughes</name>
    <address>
      <street>10 Bridge Tunnel</street>
      <city>Harlem</city>
      <province>NY</province>
    </address>
    <tag>poet</tag>
  </label>
  <label id="co" added="2004-11-15">
    <name>Christopher Okigbo</name>
    <address>
      <street>7 Heaven's Gate</street>
      <city>Idoto</city>
      <province>Anambra</province>
    </address>
    <opus>
      <title>Heaven's Gate</title>
    </opus>
    <tag>biafra</tag>
    <tag>poet</tag>
  </label>
</labels>
'''

def normalize_generated_ids(meta_list):
    pat = re.compile('r(\d+)e')

    # Takes an ID such as 'r1234e0e4' and returns 'r*e0e4'.
    def normalize_id(id):
        m = pat.match(id)
        if m:
            id = 'r*e' + id[m.end():]
        return id

    for i, (s, p, o) in enumerate(meta_list):
        s = normalize_id(s)
        o = normalize_id(U(o))
        meta_list[i] = (s, p, o)
    return meta_list


class Test_parse_model_a(unittest.TestCase):
    """Testing nasty tag soup 1"""
    def test_metadata_extraction(self):
        """Test metadata extraction"""
        model = schematron_model(MODEL_A)
        doc = bindery.parse(INSTANCE_A_1, model=model)
        metadata = generate_metadata(doc)
        EXPECTED_MD = [(u'ep', u'place', u'Hailey,ID'),
         (u'tse', u'place', u'Stamford,CT'),
         (u'tse', u'opus', u'r2e0e3e5'),
         (u'r2e0e3e5', u'title', u'The Wasteland'),
         (u'tse', u'tag', u'old possum'),
         (u'tse', u'tag', u'poet'),
         (u'lh', u'place', u'Harlem,NY'),
         (u'lh', u'tag', u'poet'),
         (u'co', u'place', u'Idoto,Anambra'),
         (u'co', u'opus', u'r2e0e7e5'),
         (u'r2e0e7e5', u'title', u"Heaven's Gate"),
         (u'co', u'tag', u'biafra'),
         (u'co', u'tag', u'poet')]

        #print list(metadata)
        meta_list = normalize_generated_ids(list(metadata))
        self.assertEqual(meta_list, normalize_generated_ids(EXPECTED_MD))

if __name__ == '__main__':
    from amara.test import test_main
    testsupport.test_main()

