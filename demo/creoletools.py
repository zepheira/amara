'''
Requires creole.py ( http://devel.sheep.art.pl/creole/file/tip/creole.py )

Direct download: http://devel.sheep.art.pl/creole/raw-file/tip/creole.py

See also: http://devel.sheep.art.pl/creole/file/tip/creole2html.py

Sample usage:

from amara.tools.creoletools import parse
doc = parse(u'test //test **test// test** test')
doc.xml_write()

from amara.writers import lookup
doc = parse(u'|x|y|z|\n|a|b|c|\n|d|e|f|\ntest') 
doc.xml_write(lookup('xml-indent'))

'''

import creole
from amara.bindery import html
from amara import tree

class text(tree.text):
    @property
    def content(self):
        return self.xml_value

    @content.setter
    def content(self, x):
        self.xml_value = x
    

def DocNode(kind='', parent=None, content=None):
    if kind == 'text':
        e = text(content or u'')
    else:
        e = parent.factory_entity.xml_element_factory(None, unicode(kind))
        if content is not None:
            e.xml_append(content)
    if parent is not None:
        parent.xml_append(e)
    e.kind = kind
    e.content = content
    return e

class Parser(creole.Parser):
    def __init__(self, raw):
        self.raw = raw
        self.root = html.entity()
        self.cur = self.root        # The most recent document node
        self.root.kind = 'document'
        self.text = None            # The node to add inline characters to


#Monkeypatch
creole.DocNode = DocNode

def parse(source):
    #root = 
    doc = Parser(source).parse()
    return doc

if __name__=="__main__":
    import sys

