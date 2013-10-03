# -*- encoding: utf-8 -*-
# 
# amara.lib.util
# © 2008, 2009 by Uche Ogbuji and Zepheira LLC
#

"""
Some utilities for general use in Amara
"""

import re
from itertools import *

from amara import tree


def element_subtree_iter(node, include_root=False):
    '''
    An iterator over the subtree, in document order, elements in the given subtree

    Basically equivalent to the descendant-or-self axis of XPath
    '''
    if isinstance(node, tree.element) or (include_root and isinstance(node, tree.entity)):
        process_stack = [(node,)]
    else:
        process_stack = [(ch for ch in node.xml_children if isinstance(ch, tree.element))]
    while process_stack:
        curr_iter = process_stack.pop()
        for e in curr_iter:
            yield e
            process_stack.append(( ch for ch in e.xml_children if isinstance(ch, tree.element) ))
    return


def top_namespaces(doc):
    '''
    Return a namespace mapping for an entity node derived from its children

    It is not safe to pass this function anything besides an entity node
    '''
    elems = [ dict([(prefix, ns) for (prefix, ns) in e.xml_namespaces.iteritems()])
                                 for e in doc.xml_children if hasattr(e, 'xml_namespaces') ]
    elems.reverse()
    return reduce(lambda a, b: a.update(b) or a, elems, {})


#
def set_namespaces(node, prefixes):
    """
    Sets namespace mapping on an entity node by updating its children, or
    on element by just updating its own mappings.  As such it can be used as
    a batch namespace update on an element

    node - the root of the tree on which namespaces are to be declared
    prefixes -  the any additional/overriding namespace mappings
                in the form of a dictionary of prefix: namespace
                the base namespace mappings are taken from in-scope
                declarations on the given node.  These new declarations are
                superimposed on existing ones
    """
    to_update = chain(node.xml_elements, (node,)) if isinstance(node, tree.entity) else (node,)
    for target in to_update:
        for k, v in prefixes.items():
            target.xml_namespaces[k] = v
    return


def replace_namespace(node, oldns, newns):
    '''
    Checks the subtree at node for elements in oldns, and changes their xml_namespace to newns.
    If newprefix is provided, update the xml_qname as well.
    Update namespace declarations on node accordingly

    You should probably ensure the appropriate namespace declaration is ready first:
    node.xmlns_attributes[newprefix] = newns
    '''
    for elem in node.xml_select(u'.//*'):
        if elem.xml_namespace == oldns:
            elem.xml_namespace = newns
    return


def unwrap(e):
    '''
    Remove a wrapping tag and graft its children onto its parents
    Returns the parent (e.xml_parent)

    >>> import amara
    >>> from amara.lib.util import unwrap
    >>> doc = amara.parse('<a><b><c/><d/></b></a>')
    >>> swapped = doc.xml_first_child.xml_first_child #b element
    >>> swapped = unwrap(swapped)
    >>> swapped.xml_encode()
    <a><c/><d/></a>
    '''
    children = e.xml_children
    #e.xml_parent.xml_replace(e, children[0])
    pos = e.xml_parent.xml_index(e)
    parent = e.xml_parent
    parent.xml_remove(e)
    for c in children:
        parent.xml_insert(pos, c)
        pos += 1
    #Returning the parent facilitates typical logic
    return parent


def first_item(seq, default=None):
    '''
    Return the first item in a sequence, or the default result (None by default),
    or if it can reasonably determine it's not a sequence, just return the identity
    
    This is a useful, blind unpacker tool, e.g. when dealing with XML models that
    sometimes provide scalars and sometimes sequences, which are sometimes empty.
    
    This is somewhat analogous to the Python get() method on dictionaries, and
    is an idiom which in functional chains is less clumsy than its equivalent:

    try:
        return seq.next()
    except StopIteration:
        return default
    '''
    from amara import tree
    if isinstance(seq, basestring) or isinstance(seq, tree.node): return seq
    return chain(seq or (), (default,)).next()


def parse_pi_pseudo_attrs(pinode):
    '''
    Parse the given processing instruction node in terms of conventional pseudo-attribute
    structure. Returns a key/value pair dictionary.

    >>> import amara
    >>> from amara.lib.util import parse_pi_pseudo_attrs
    >>> X = '<?xml-stylesheet type="text/xml" href="Xml/Xslt/Core/addr_book1.xsl"?><doc/>'
    >>> doc = amara.parse(X)
    >>> pi = doc.xml_children[0]
    >>> parse_pi_pseudo_attrs(pi)
    {u'href': u'Xml/Xslt/Core/addr_book1.xsl', u'type': u'text/xml'}
    '''
    PI_PA_PAT = re.compile('(\w+)\s*=\s*"(.*?)"', re.DOTALL)
    return dict(PI_PA_PAT.findall(pinode.xml_data))


identity = lambda x: x

def omit_blanks():
    return "..."

def make_date():
    return "..."


#See: http://docs.python.org/dev/howto/functional.html
#from functional import *
#Will work as of 2.7
#mcompose = partial(reduce, compose)

def mcompose(*funcs):
    def f(val):
        result = val
        for func in funcs:
            result = pipeline_stage(func, result)
        return result
    return f
#    return result
#        result = tuple(pipeline_stage(func, result))
#    for item in result:
#        yield item


def pipeline_stage(obj, arg):
    if callable(obj):
        fresult = obj(arg)
    else:
        fresult = arg
#        try:
#            it = (fresult,)
#            if not isinstance(fresult, basestring): it = iter(fresult)
#        except TypeError:
#            pass
#    else:
#        it = (arg,)
#    return iter(it)
    return fresult


from copy import *
def trim_word_count(node, maxcount):
    '''
    import amara
    from amara.lib.util import trim_word_count
    x = amara.parse('<a>one two <b>three four </b><c>five <d>six seven</d> eight</c> nine</a>')
    trim_word_count(x, 1).xml_write()
    trim_word_count(x, 2).xml_write()
    trim_word_count(x, 3).xml_write()
    trim_word_count(x, 4).xml_write()
    trim_word_count(x, 5).xml_write()
    trim_word_count(x, 6).xml_write()
    trim_word_count(x, 7).xml_write()
    trim_word_count(x, 8).xml_write()
    trim_word_count(x, 9).xml_write()
    trim_word_count(x, 10).xml_write()
    '''
    def trim(node, count):
        newnode = copy(node)
        for child in node.xml_children:
            if count >= maxcount:
                break
            words = len(child.xml_select(u'string(.)').split())
            if count + words < maxcount:
                newnode.xml_append(deepcopy(child))
                count += words
            else:
                if isinstance(child, tree.text):
                    words_required = maxcount - count
                    chunk = child.xml_value.rsplit(None, 
                                                   words-words_required)[0]
                    newnode.xml_append(tree.text(chunk))
                else:
                    newnode.xml_append(trim(child, count))
                count = maxcount
        return newnode
    return trim(node, 0)


def coroutine(func):
    '''
    A simple tool to eliminate the need to call next() to kick-start a co-routine
    From David Beazley: http://www.dabeaz.com/generators/index.html
    '''
    def start(*args,**kwargs):
        coro = func(*args,**kwargs)
        coro.next()
        return coro
    return start


def strip_namespaces(node, strip_decls=False):
    #from amara.lib.util import element_subtree_iter
    for e in element_subtree_iter(node):
        e.xml_namespace = None
        if strip_decls and e.xml_namespaces:
            for prefix in e.xml_namespaces:
                del e.xml_namespaces[prefix] #FIXME: Does not work (NotImplementedError: NamespaceMap_DelNode)
    return


#class UTemplate(Template):
#    '''
#    Unicode-safe version of string.Template
#    '''
#    pattern = unicode(Template.pattern)
#    delimiter = u'$'
#    idpattern = ur'[_a-z][_a-z0-9]*'


#Loosely based on methods in unittest.py

def assert_(test, obj, msg=None):
    """
    Raise an error if the test expression is not true.  The test can be a function that takes the context object.
    """
    if (callable(test) and not test(obj)) or not test:
        raise AssertionError(msg)
    return obj


def assert_false(test, obj, msg=None):
    """
    Raise an error if the test expression is true.  The test can be a function that takes the context object.
    """
    if (callable(test) and test(obj)) or test:
        raise AssertionError(msg)
    return obj


def assert_equal(other, obj, msg=None):
    """
    Fail if the two objects are unequal as determined by the '==' operator.
    
    from functools import *
    from amara.lib.util import *
    f = partial(assert_equal, u'', msg="POW!")
    print (f(''),) # -> ''
    """
    if not obj == other:
        raise AssertionError(msg or '%r != %r' % (obj, other))
    return obj


def assert_not_equal(other, obj, msg=None):
    """Fail if the two objects are equal as determined by the '=='
       operator.
    """
    if obj == other:
        raise AssertionError(msg or '%r == %r' % (obj, other))
    return obj


DEF_BUFFERSIZE = 1000

# read by specified separator, not newlines
def readbysep(f, sep, buffersize=DEF_BUFFERSIZE):
    '''
from amara.lib.util import readbysep
import cStringIO
f = cStringIO.StringIO('a\fb\fc')
[ x for x in readbysep(f, '\f') ]
['a', 'b', 'c']

#OK next 2 go in test suite, not docstrings
f = cStringIO.StringIO('a\fb\fc\f')
[ x for x in readbysep(f, '\f') ]
['a', 'b', 'c']

f = cStringIO.StringIO('\fa\fb\fc')
[ x for x in readbysep(f, '\f') ]
['a', 'b', 'c']

from amara import parse
from amara.lib.util import readbysep
import cStringIO
f = cStringIO.StringIO('<a/>\f<b/>\f<c/>')
[ parse(x).xml_select(u'name(*)') for x in readbysep(f, '\f') ]
    '''
    leftover = ''
    while 1:
        next = f.read(buffersize)
        if not next: #empty string at EOF
            yield leftover
            break
        chunks = (leftover + next).split(sep)
        leftover = chunks[-1]
        for chunk in chunks[:-1]: yield chunk
    return



#Though I've found this very hard to reproduce simply, the plain string.Template seems susceptible to Unicode error

#Rest of this file is an adaptation from Python 2.6.1 string.py
#It creates a drop-in replacement for string.Template to address the Unicode problem

import re as _re

class _multimap:
    """Helper class for combining multiple mappings.

    Used by .{safe_,}substitute() to combine the mapping and keyword
    arguments.
    """
    def __init__(self, primary, secondary):
        self._primary = primary
        self._secondary = secondary

    def __getitem__(self, key):
        try:
            return self._primary[key]
        except KeyError:
            return self._secondary[key]


class _TemplateMetaclass(type):
    pattern = r"""
    %(delim)s(?:
      (?P<escaped>%(delim)s) |   # Escape sequence of two delimiters
      (?P<named>%(id)s)      |   # delimiter and a Python identifier
      {(?P<braced>%(id)s)}   |   # delimiter and a braced identifier
      (?P<invalid>)              # Other ill-formed delimiter exprs
    )
    """

    def __init__(cls, name, bases, dct):
        super(_TemplateMetaclass, cls).__init__(name, bases, dct)
        if 'pattern' in dct:
            pattern = cls.pattern
        else:
            pattern = _TemplateMetaclass.pattern % {
                'delim' : _re.escape(cls.delimiter),
                'id'    : cls.idpattern,
                }
        cls.pattern = _re.compile(unicode(pattern), _re.IGNORECASE | _re.VERBOSE | _re.UNICODE)


class Template:
    """A string class for supporting $-substitutions."""
    __metaclass__ = _TemplateMetaclass

    delimiter = '$'
    idpattern = r'[_a-z][_a-z0-9]*'

    def __init__(self, template):
        self.template = template

    # Search for $$, $identifier, ${identifier}, and any bare $'s

    def _invalid(self, mo):
        i = mo.start('invalid')
        lines = self.template[:i].splitlines(True)
        if not lines:
            colno = 1
            lineno = 1
        else:
            colno = i - len(''.join(lines[:-1]))
            lineno = len(lines)
        raise ValueError('Invalid placeholder in string: line %d, col %d' %
                         (lineno, colno))

    def substitute(self, *args, **kws):
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = _multimap(kws, args[0])
        else:
            mapping = args[0]
        # Helper function for .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                val = mapping[named]
                val = val if isinstance(val, unicode) else unicode(val, 'utf-8')
                # We use this idiom instead of str() because the latter will
                # fail if val is a Unicode containing non-ASCII characters.
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

    def safe_substitute(self, *args, **kws):
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = _multimap(kws, args[0])
        else:
            mapping = args[0]
        # Helper function for .sub()
        def convert(mo):
            named = mo.group('named')
            if named is not None:
                try:
                    # We use this idiom instead of str() because the latter
                    # will fail if val is a Unicode containing non-ASCII
                    return '%s' % (mapping[named],)
                except KeyError:
                    return self.delimiter + named
            braced = mo.group('braced')
            if braced is not None:
                try:
                    return '%s' % (mapping[braced],)
                except KeyError:
                    return self.delimiter + '{' + braced + '}'
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return self.delimiter
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

