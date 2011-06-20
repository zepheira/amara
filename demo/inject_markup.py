'''
Demonstration of how you can inject markup into text within XML

Should output:

<?xml version="1.0" encoding="UTF-8"?>
<catalog>
  <book>
     <title>Spam for Supper</title>
     <authors>By <a href="http://example.org">A.X. Ham</a> and <a href="http://example.org">Franco Bacon</a></authors>
  </book>
</catalog>
'''

import re
from itertools import groupby

import amara
from amara.lib import U
from amara.tree import element, text

SOURCE = '''<catalog>
  <book>
     <title>Spam for Supper</title>
     <authors>By A.X. Ham and Franco Bacon</authors>
  </book>
</catalog>'''

EXTRACT_AUTHORS_PAT = r'(\s*By\s*)|(\s*,\s*)|(\s*and\s*)'
EXTRACT_AUTHORS_PAT_GROUPS = 4

doc = amara.parse(SOURCE)
for author_node in doc.xml_select(u'/catalog/book/authors'):
    authors = re.split(EXTRACT_AUTHORS_PAT, U(author_node))
    for n in author_node.xml_children: author_node.xml_remove(n)
    #Collect the regex match into the regex-defined groups
    for i, subenum in groupby(enumerate(authors), lambda i: i[0]//EXTRACT_AUTHORS_PAT_GROUPS):
        matchgroup = [ group for i, group in subenum ]
        if matchgroup[0]:
            link = element(None, u'a')
            link.xml_attributes[None, u'href'] = 'http://example.org'
            link.xml_append(text(matchgroup[0]))
            author_node.xml_append(link)
        for match in matchgroup[1:]:
            if match:
                author_node.xml_append(text(match))

doc.xml_write()
print

#The following variation contributed by Luis Miguel Morillas:

SOURCE = '''<catalog>
 <book>
    <title>Spam for Supper</title>
       By A.X. Ham and Franco Bacon
   <info> Other info</info>
 </book>
</catalog>'''

for author_node in doc.xml_select(u'/catalog/book/authors'):
    authors = re.split(EXTRACT_AUTHORS_PAT, U(author_node))
    #Note: you can use author_node.xml_clear() if you use bindery
    parent = author_node.xml_parent
    pos = parent.xml_index(author_node)
    parent.xml_remove(author_node)
    #Collect the regex match into the regex-defined groups
    for i, subenum in groupby(enumerate(authors), lambda i: i[0]//EXTRACT_AUTHORS_PAT_GROUPS):
        matchgroup = [ group for i, group in subenum ]
        if matchgroup[0]:
            link = element(None, u'a')
            link.xml_attributes[None, u'href'] = 'http://example.org'
            link.xml_append(text(matchgroup[0]))
            parent.xml_insert(pos, link)
            pos += 1
        for match in matchgroup[1:]:
            if match:
                parent.xml_insert(pos, (text(match)))
                pos += 1

doc.xml_write()
