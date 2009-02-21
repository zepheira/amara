import unittest
from amara.lib import testsupport
from amara import tree
import os
import tempfile

from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from amara import bindery
from amara.bindery.model import *

MODEL_A = '''<?xml version="1.0" encoding="utf-8"?>
<labels xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara">
  <label id="tse" added="2003-06-10" eg:occurs="*" ak:resource="@id"> <!-- use ak:resource="" for an anon resource -->
    <quote eg:occurs="?">
      <emph>Midwinter</emph> Spring is its own <strong>season</strong>...
    </quote>
    <name>Thomas Eliot</name>
    <address ak:rel="'place'" ak:value="concat(city, ',', province)">
      <street>3 Prufrock Lane</street>
      <city>Stamford</city>
      <province>CT</province>
    </address>
    <opus year="1932" ak:rel="name()" ak:resource="">
      <title ak:rel="name()">The Wasteland</title>
    </opus>
    <tag eg:occurs="*" ak:rel="name()">old possum</tag>
  </label>
</labels>
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

class Test_parse_model_a(unittest.TestCase):
    """Testing nasty tag soup 1"""
    def test_metadata_extraction(self):
        """Test metadata extraction"""
        model = examplotron_model(MODEL_A)
        doc = bindery.parse(INSTANCE_A_1, model=model)
        metadata = doc.xml_model.generate_metadata(doc)
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
        
        self.assertEqual(metadata, EXPECTED_MD)
        #import pprint; pprint.pprint(metadata)

        #f = filesource('nastytagsoup1.html')
        #doc = html.parse(f.source)
        #self.assertEqual(len(doc.xml_children), 1)
        return

if __name__ == '__main__':
    testsupport.test_main()

