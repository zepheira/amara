########################################################################
# amara/xpath/locationpaths/__init__.py
"""
XPath location path expressions.
"""

from amara.xpath import XPathError
from amara.xpath.expressions import nodesets
from amara.xpath.locationpaths import axisspecifiers, nodetests, _paths

class location_path(nodesets.nodeset_expression):
    """
    An object representing a location path
    (XPath 1.0 grammar production 1: LocationPath)
    """
    _steps = ()

    def compile_iterable(self, compiler):
        emit = compiler.emit
        if self.absolute:
            emit(
                # discard existing context node on stack
                'POP_TOP',
                # make the root node the context node
                'LOAD_FAST', 'context',
                'LOAD_ATTR', 'node',
                'LOAD_ATTR', 'xml_root',
                'BUILD_TUPLE', 1,
                )
        for step in self._steps:
            # spare an attribute lookup
            axis, node_test = step.axis, step.node_test
            # get the node filter to use for the node iterator
            node_filter = node_test.get_filter(compiler, axis.principal_type)
            if node_filter:
                node_filter = node_filter.select
            predicates = step.predicates
            if predicates:
                predicates = [ predicate.select for predicate in predicates ]
            # create the node iterator for this step
            step = _paths.stepiter(axis.select, axis.reverse, node_filter,
                                   predicates)
            # add the opcodes for calling `step.select(context, nodes)`
            emit('LOAD_CONST', step.select,
                 'LOAD_FAST', 'context',
                 # stack is now [context, step.select, nodes]
                 'ROT_THREE',
                 # stack is now [step.select, nodes, context]
                 'ROT_THREE',
                 # stack is now [nodes, context, step.select]
                 'CALL_FUNCTION', 2,
                 )
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        for step in self._steps:
            step.pprint(indent + '  ', stream)

    def __str__(self):
        path = '/'.join(map(unicode, self._steps))
        if self.absolute:
            path = '/' + path
        return path


class absolute_location_path(location_path):
    """
    An object representing an absolute location path
    (XPath 1.0 grammar production 2: AbsoluteLocationPath)
    """
    absolute = True
    def __init__(self, path=None):
        if path is None:
            self._steps = ()
        else:
            assert isinstance(path, relative_location_path)
            self._steps = path._steps


class relative_location_path(location_path):
    """
    An object representing a relative location path
    (XPath 1.0 grammar production 3: RelativeLocationPath)
    """
    absolute = False
    def __init__(self, path, step=None):
        if step is None:
            assert isinstance(path, location_step), repr(path)
            self._steps = [path]
        else:
            assert isinstance(path, relative_location_path), path
            assert isinstance(step, location_step), step
            self._steps = path._steps
            self._steps.append(step)


class abbreviated_absolute_location_path(absolute_location_path):
    """
    An object representing an abbreviated absolute location path
    (XPath 1.0 grammar production 10: AbbreviatedAbsoluteLocationPath)
    """
    def __init__(self, path):
        assert isinstance(path, relative_location_path)
        self._steps = path._steps
        # `a//b` is the same as `a/descendant::b` if `b` uses the `child`
        # axis and has no (positional) predicates
        step = path._steps[0]
        if not step.predicates and isinstance(step.axis, 
                                              axisspecifiers.child_axis):
            axis = axisspecifiers.axis_specifier('descendant')
            path._steps[0] = location_step(axis, step.node_test)
        else:
            axis = axisspecifiers.axis_specifier('descendant-or-self')
            node_test = nodetests.node_type('node')
            abbrev = location_step(axis, node_test)
            self._steps.insert(0, abbrev)


class abbreviated_relative_location_path(relative_location_path):
    """
    An object representing an abbreviated relative location path
    (XPath 1.0 grammar production 11: AbbreviatedRelativeLocationPath)
    """
    def __init__(self, path, step):
        assert isinstance(path, relative_location_path)
        assert isinstance(step, location_step)
        self._steps = path._steps
        # `a//b` is the same as `a/descendant::b` if `b` uses the `child`
        # axis and has no (positional) predicates
        if not step.predicates and isinstance(step.axis, 
                                              axisspecifiers.child_axis):
            axis = axisspecifiers.axis_specifier('descendant')
            step = location_step(axis, step.node_test)
        else:
            axis = axisspecifiers.axis_specifier('descendant-or-self')
            node_test = nodetests.node_type('node')
            abbrev = location_step(axis, node_test)
            self._steps.append(abbrev)
        self._steps.append(step)


class location_step(object):
    """
    An object representing a location step
    (XPath 1.0 grammar production 4: Step)
    """
    __slots__ = ('axis', 'node_test', 'predicates')

    def __init__(self, axis, node_test, predicates=None):
        self.axis = axis
        self.node_test = node_test
        self.predicates = predicates

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self.axis.pprint(indent + '  ', stream)
        self.node_test.pprint(indent + '  ', stream)
        if self.predicates:
            self.predicates.pprint(indent + '  ', stream)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<%s at 0x%x: %s>' % (self.__class__.__name__, ptr, self)

    def __str__(self):
        # allows display abbreviated syntax, if possible
        if isinstance(self.node_test, nodetests.any_node_test):
            if isinstance(self.axis, axisspecifiers.self_axis):
                return '.'
            if isinstance(self.axis, axisspecifiers.parent_axis):
                return '..'
            if isinstance(self.axis, axisspecifiers.descendant_or_self_axis):
                return ''
        return '%s::%s%s' % (self.axis, self.node_test, self.predicates or '')


class abbreviated_step(location_step):
    """
    An object representing an abbreviated location step
    (XPath 1.0 grammar production 12: AbbreviatedStep)
    """
    node_test = nodetests.node_type('node')
    predicates = None

    def __init__(self, abbrev):
        if abbrev == '.':
            axis = 'self'
        else:
            assert abbrev == '..'
            axis = 'parent'
        self.axis = axisspecifiers.axis_specifier(axis)
