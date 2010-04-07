'''
Requires creole.py ( http://devel.sheep.art.pl/creole/file/tip/creole.py )

Recommended installation process:

pip install -e hg+http://devel.sheep.art.pl/creole/#egg=Creole

Or if you prefer, direct download: http://devel.sheep.art.pl/creole/raw-file/tip/creole.py

See also: http://devel.sheep.art.pl/creole/file/tip/creole2html.py

Sample usage:

>>> from amara.tools.creoletools import parse
>>> doc = parse(u'test //test **test// test** test')
>>> doc.xml_write()
<?xml version="1.0" encoding="UTF-8"?>
<paragraph>test <emphasis>test <strong>test<emphasis> test<strong> test</strong></emphasis></strong></emphasis></paragraph>

>>> from amara.writers import lookup
>>> doc = parse(unichr(10).join([u'|x|y|z|', u'|a|b|c|', u'|d|e|f|', u'test']))
>>> doc.xml_write(lookup('xml-indent'))
<?xml version="1.0" encoding="UTF-8"?>
<table>
  <table_row>
    <table_cell>x</table_cell>
    <table_cell>y</table_cell>
    <table_cell>z</table_cell>
  </table_row>
  <table_row>
    <table_cell>a</table_cell>
    <table_cell>b</table_cell>
    <table_cell>c</table_cell>
  </table_row>
  <table_row>
    <table_cell>d</table_cell>
    <table_cell>e</table_cell>
    <table_cell>f</table_cell>
  </table_row>
</table>
<paragraph>test</paragraph>

'''

#FIXME: I don' think the base creole.py is Unicode aware at all

#parse(unichr(10).join([u'|x|y|z|', u'|a|b|c|', u'|d|e|f|', u'test']))
#A roundabout way, for purposes of doctest, to write: parse(u'|x|y|z|\n|a|b|c|\n|d|e|f|\ntest')

import re
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
    #import sys; print >> sys.stderr, (kind, parent, content)
    if parent is not None:
        if kind == 'text':
            e = text(content or u'')
        else:
            e = parent.factory_entity.xml_element_factory(None, unicode(kind))
            if content is not None:
                e.xml_append(content)
        parent.xml_append(e)
        e.kind = kind
        e.content = content
        return e

class Parser(creole.Parser):
    def __init__(self, raw, rules=None):
        '''
        '''
        rules = rules or Rules()
        creole.Parser.__init__(self, raw, rules)
        self.raw = raw
        self.root = html.entity()
        self.cur = self.root        # The most recent document node
        self.root.kind = 'document'
        self.text = None            # The node to add inline characters to

    def _defitem_repl(self, groups):
        term = groups.get('defterm', u'')
        defn = groups.get('defdef', u'')
        kind = 'definition_list'
        lst = self.cur
        # Find a list of the same kind up the tree
        #FIXME: check/test how this works for defn lists in Moin
        #print groups, repr(lst)
        while (lst and
                   not lst.kind == kind and
                   not lst.kind in ('document', 'section', 'blockquote')):
            lst = lst.parent
        if lst and lst.kind == kind:
            self.cur = lst
        else:
            # Create a new level of list
            self.cur = self._upto(self.cur,
                ('item', 'document', 'section', 'blockquote'))
            self.cur = DocNode(kind, self.cur)
        item = DocNode('item', self.cur)
        self.cur = item
        self.cur = DocNode('term', self.cur)
        self.text = None
        self.parse_inline(term)
        self.cur = item
        self.cur = DocNode('defn', self.cur)
        self.text = None
        self.parse_inline(defn)
        self.text = None
    _defterm_repl = _defitem_repl
    _defdef_repl = _defitem_repl

    def _deflist_repl(self, groups):
        text = groups.get('deflist', u'')
        self.rules.defitem_re.sub(self._replace, text)


class Rules(creole.Rules):
    deflist = r'''(?P<deflist>
            ^ [ \t]*[\w-].*?::[ \t].* $
            ( \n[ \t]*[\w-].*?::[ \t].* $ )*
        )'''

    defitem = r'''(?P<defitem>
            ^ \s*
            (?P<defterm> [\w-]+.*?)::[ \t](?P<defdef> .*?)
            $
        )'''

    def __init__(self, bloglike_lines=False, url_protocols=None, wiki_words=False):
        creole.Rules.__init__(self, bloglike_lines, url_protocols, wiki_words)
        self.defitem_re = re.compile(self.defitem, re.X | re.U | re.M)
        self.block_re = re.compile('|'.join([self.line, self.head, self.separator,
                          self.pre, self.list, self.deflist, self.table,
                          self.text]), re.X | re.U | re.M)


from amara.lib import inputsource
def parse(source):
    if isinstance(source, str):
        doc = Parser(source).parse()
    elif isinstance(source, unicode):
        doc = Parser(source.encode('utf-8')).parse()
    else:
        doc = Parser(inputsource.text(source).stream.read()).parse()
    return doc

#Monkeypatching
creole.DocNode = DocNode

#--------------
#Unit test

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

