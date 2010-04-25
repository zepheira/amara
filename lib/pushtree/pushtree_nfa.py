import itertools

from amara.xpath import parser as xpath_parser
from amara.xpath import locationpaths
from amara.xpath.locationpaths import axisspecifiers
from amara.xpath.locationpaths import nodetests
from amara.xpath.functions import nodesets
from amara.xpath.expressions import booleans
import amara.xpath.expressions.nodesets # another nodesets!
from amara.xpath.expressions import basics

counter = itertools.count(1)

# [@x]
class AttributeExistsPred(object):
    def __init__(self, name):
        self.name = name

# [@x="a"]
class AttributeBinOpPred(object):
    def __init__(self, name, op, value):
        self.name = name
        self.op = op
        self.value = value

class AttributeFunctionCallPred(object):
    def __init__(self, func):
        self.func = func

#####

# This would yield nodes, attribute, PIs, and comments
#class AnyTest(object):
#    pass

class BaseNodeTest(object):
    match_type = "node"

# What about *[@spam] ?
class AnyNodeTest(BaseNodeTest):
    def __str__(self):
        return "AnyNode (*)"

class NodeTest(BaseNodeTest):
    def __init__(self, name, predicates):
        # (ns, name)
        self.name = name
        self.predicates = predicates

    def __str__(self):
        return "Node ns=%r localname=%r predicates=%r" % (self.name[0], self.name[1],
                                                          self.predicates)

# predicates make no sense here because we only support downward axes
# and these have no downward axes. (XXX I think.)
class AttributeTest(object):
    match_type = "attr"
    def __init__(self, name, predicates):
        self.name = name
        assert not predicates
        self.predicates = predicates
    def __str__(self):
        return "Attr name=%r" % (self.name,)


class ProcessingInstructionTest(object):
    match_type = "processing-instruction"
    def __init__(self, target):
        self.target = target
    def __str__(self):
        return "processing-instruction(%r)" % (self.target,)

class CommentTest(object):
    match_type = "comment"


class NFA(object):
    def __init__(self):
        self.start_edges = []
        self.edges = {}  # from_node_id -> [(to_node_id, test), ...]
        self.terminal_nodes = set()
        # The start node has no type
        self.match_types = {}  # node_id -> match_type
        self.labeled_handlers = {} # node_id -> (label, PushtreeHandler)

    def copy(self):
        nfa = NFA()
        nfa.start_edges[:] = self.start_edges
        nfa.edges.update(self.edges)
        nfa.terminal_nodes.update(self.terminal_nodes)
        nfa.match_types.update(self.match_types)
        nfa.labeled_handlers.update(self.labeled_handlers)
        return nfa

    def get_edges(self, node_id):
        if node_id is None:
            return self.start_edges
        return self.edges[node_id]

    def add_handler(self, labeled_handler):
        for node_id in self.terminal_nodes:
            self.labeled_handlers[node_id].append(labeled_handler)


    def new_node(self, from_node_id, test):
        edges = self.get_edges(from_node_id)
        to_node_id = next(counter)
        self.edges[to_node_id] = []
        self.match_types[to_node_id] = test.match_type
        self.labeled_handlers[to_node_id] = []
        edges.append( (to_node_id, test) )
        return to_node_id

    def connect(self, from_node_id, to_node_id, test):
        self.get_edges(from_node_id).append( (to_node_id, test) )

    def extend(self, other):
        assert not set(self.edges) & set(other.edges), "non-empty intersection"
        if not self.start_edges:
            self.start_edges[:] = other.start_edges
        self.edges.update(other.edges)
        self.match_types.update(other.match_types)
        for node_id in self.terminal_nodes:
            self.edges[node_id].extend(other.start_edges)
        self.terminal_nodes.clear()
        self.terminal_nodes.update(other.terminal_nodes)
        self.labeled_handlers.update(other.labeled_handlers)

    def union(self, other):
        assert not set(self.edges) & set(other.edges), "non-empty intersection"
        self.start_edges.extend(other.start_edges)
        self.edges.update(other.edges)
        self.match_types.update(other.match_types)
        self.terminal_nodes.update(other.terminal_nodes)
        self.labeled_handlers.update(other.labeled_handlers)

    def dump(self):
        for node_id, edges in [(None, self.start_edges)] + sorted(self.edges.items()):
            if node_id is None:
                node_name = "(start)"
                labels = ""
            else:
                node_name = str(node_id)
                action = str(self.match_types[node_id])
                labels += " " + str([x[0] for x in self.labeled_handlers[node_id]])
            is_terminal = "(terminal)" if (node_id in self.terminal_nodes) else ""
            print node_name, is_terminal, labels
            self._dump_edges(edges)
        print "======"

    def _dump_edges(self, edges):
        for (to_node_id, test) in edges:
            print "", test, "->", to_node_id
        

def _add_initial_loop(nfa):
    start_edges = nfa.start_edges[:]
    any_node = nfa.new_node(None, AnyNodeTest())
    for (to_node_id, test) in start_edges:
        nfa.connect(any_node, to_node_id, test)
    nfa.connect(any_node, any_node, AnyNodeTest()) # loop

def to_nfa(expr, namespaces):
    #print "Eval", expr.__class__
    if (expr.__class__ is locationpaths.relative_location_path):
        # This is a set of path specifiers like
        #  "a" "a/b", "a/b/c[0]/d[@x]"   (relative location path)
        #  "@a", "a/@b", and even "@a/@b", which gives nothing
        nfa = NFA()
        for step in expr._steps:
            nfa.extend(to_nfa(step, namespaces))
        _add_initial_loop(nfa)
        return nfa

    if (expr.__class__ is locationpaths.absolute_location_path):
        # This is an absolute path like
        #   "/a", "/a[0]/b[@x]"
        nfa = NFA()
        for step in expr._steps:
            axis = step.axis
            axis_name = axis.name
            assert axis_name in ("child", "descendant"), axis_name
            subnfa = to_nfa(step, namespaces)
            if axis_name == "descendant":
                _add_initial_loop(subnfa)
            nfa.extend(subnfa)
        return nfa
        
    if (expr.__class__ is locationpaths.abbreviated_absolute_location_path):
        # This is an abbreviated_absolute_location_path
        #  "//a", "a//b"
        nfa = NFA()
        for step in expr._steps:
            nfa.extend(to_nfa(step, namespaces))
        _add_initial_loop(nfa)
        return nfa

    if expr.__class__ is locationpaths.location_step:
        # This is a step along some axis, such as:
        #  "a" - step along the child axis
        #  "a[@x][@y='1']" - step along the child axis, with two predicates
        #  "@a" - step along the attribute axis
        axis = expr.axis
        axis_name = axis.name
        assert axis_name in ("child", "descendant", "attribute"), axis_name
        if axis_name == "attribute":
            klass = AttributeTest
        else:
            klass = NodeTest

        nfa = NFA()
        node_test = expr.node_test
        if node_test.__class__ is nodetests.local_name_test:
            # Something without a namespace, like "a"
            node_id = nfa.new_node(None,
                                   klass(node_test.name_key, expr.predicates))
        elif node_test.__class__ is nodetests.namespace_test:
            # Namespace but no name, like "a:*"
            namespace = namespaces[node_test._prefix]
            node_id = nfa.new_node(None,
                                   klass((namespace, None), expr.predicates))
        elif node_test.__class__ is nodetests.qualified_name_test:
            prefix, localname = node_test.name_key
            namespace = namespaces[prefix]
            node_id = nfa.new_node(None,
                                   klass((namespace, localname), expr.predicates))
        elif node_test.__class__ is nodetests.processing_instruction_test:
            node_id = nfa.new_node(None,
                                   ProcessingInstructionTest(node_test._target))
        elif node_test.__class__ is locationpaths.nodetests.principal_type_test:
            node_id = nfa.new_node(None,
                                   klass((None, None), None))
        else:
            die(node_test)

        nfa.terminal_nodes.add(node_id)

        #if axis_name == "descendant":
        #    _add_initial_loop(nfa)
            
        #print "QWERQWER"
        #nfa.dump()
        return nfa

    if expr.__class__ is amara.xpath.expressions.nodesets.union_expr:
        # "a|b"
        nfa = to_nfa(expr._paths[0], namespaces)
        for path in expr._paths[1:]:
            nfa.union(to_nfa(path, namespaces))
        return nfa

    die(expr)

def node_intersect(parent_test, child_test):
    if parent_test is not None:
        assert isinstance(parent_test, BaseNodeTest), parent_test
        assert getattr(parent_test, "predicates", None) is None
    assert isinstance(child_test, BaseNodeTest), child_test
    assert getattr(child_test, "predicates", None) is None

    if parent_test is None:
        if isinstance(child_test, AnyNodeTest):
            return True, False
        if isinstance(child_test, NodeTest):
            return child_test, False
    
    if isinstance(parent_test, AnyNodeTest):
        if isinstance(child_test, AnyNodeTest):
            return True, False
        if isinstance(child_test, NodeTest):
            return child_test, False
    elif isinstance(parent_test, NodeTest):
        if isinstance(child_test, AnyNodeTest):
            return True, True
        if isinstance(child_test, NodeTest):
            # XXX This is wrong. Resolved namespaces can be the same even
            # if the namespace fields are different.
            # XXX check for predicates!
            if parent_test.name == child_test.name:
                return True, False
            return False, child_test

def attr_intersect(parent_test, child_test):
    if parent_test is not None:
        assert isinstance(parent_test, AttributeTest), parent_test
    assert isinstance(child_test, AttributeTest), child_test

    if parent_test is None:
        return child_test, False
    if parent_test.name == child_test.name:
        return True, False
    return False, child_test

def pi_intersect(parent_test, child_test):
    if parent_test is not None:
        assert isinstance(parent_test, ProcessingInstructionTest), parent_test
    assert isinstance(child_test, ProcessingInstructionTest), child_test

    if parent_test is None:
        return child_test, False
    # Is there any way to match *any* PI?
    # Looks like Amara support XPath 1.0, where this is a string
    if parent_test.target == child_test.target:
        return True, False
    return False, child_test

def comment_intersect(parent_test, child_test):
    if parent_test is not None:
        assert isinstance(parent_test, CommentTest), parent_test
    assert isinstance(child_test, CommentTest), child_test
    return True, False


# Used to make a decision tree. Either the test passes or it fails.
# TODO: something more sophisticated? For example, if there are a
# large number of element tag tests then sort the tags and start
# in the middle. Should give O(log(number of tags)) performance
# instead of O(n). However, for now, n is no more than 10 or so.


class Branch(object):
    def __init__(self, test, if_true, if_false):
        self.test = test
        self.if_true = if_true
        self.if_false = if_false


class StateTable(object):
    def __init__(self, match_type, nfa, nfa_node_ids):
        self.match_type = match_type # 'None' for the start node
        self.nfa = nfa
        self.nfa_node_ids = nfa_node_ids
        self.node_tree = Branch(None, set(), set())
        self.attr_tree = Branch(None, set(), set())
        self.pi_tree = Branch(None, set(), set())
        self.comment_tree = Branch(None, set(), set())

    def add(self, test, to_node_id):
        if isinstance(test, BaseNodeTest):
            self._add(self.node_tree, test, to_node_id, node_intersect)
        elif isinstance(test, AttributeTest):
            self._add(self.attr_tree, test, to_node_id, attr_intersect)
        elif isinstance(test, ProcessingInstructionTest):
            self._add(self.pi_tree, test, to_node_id, pi_intersect)
        elif isinstance(test, CommentTest):
            self._add(self.comment_tree, test, to_node_id, comment_intersect)
        else:
            raise AssertionError(test)
                
    def _add(self, tree, test, to_node_id, intersect):
        new_true_test, new_false_test = intersect(tree.test, test)
        if new_true_test == True:
            self._add_to_leaves(tree.if_true, to_node_id)

        elif new_true_test:
            if isinstance(tree.if_true, set):
                new_branch = Branch(new_true_test,
                                    tree.if_true | set([to_node_id]),
                                    tree.if_true)
                tree.if_true = new_branch
            else:
                self._add(tree.if_true, new_true_test, to_node_id, intersect)

        if new_false_test == True:
            self._add_to_leaves(tree.if_false, to_node_id)
        elif new_false_test:
            if isinstance(tree.if_false, set):
                new_branch = Branch(new_false_test,
                                    tree.if_false | set([to_node_id]),
                                    tree.if_false)
                tree.if_false = new_branch
            else:
                self._add(tree.if_false, new_false_test, to_node_id, intersect)

    def _add_to_leaves(self, tree, to_node_id):
        if isinstance(tree, set):
            tree.add(to_node_id)
        else:
            self._add_to_leaves(tree.if_true, to_node_id)
            self._add_to_leaves(tree.if_false, to_node_id)

    def get_final_nodes(self):
        result = {}
        for match_type, tree in ( (BaseNodeTest.match_type, self.node_tree),
                                  (AttributeTest.match_type, self.attr_tree),
                                  (ProcessingInstructionTest.match_type, self.pi_tree),
                                  (CommentTest.match_type, self.comment_tree) ):
            visit = [tree]
            while visit:
                node = visit.pop()
                if isinstance(node, set):
                    if node:
                        result[frozenset(node)] = match_type
                elif node is not None:
                    visit.append(node.if_true)
                    visit.append(node.if_false)
        return result.items()

    def dump(self, numbering):
        # Do I report anything for having reached here?
        if list(self.nfa_node_ids) != [None]:
            for nfa_node in self.nfa_node_ids:
                labels = [x[0] for x in self.nfa.labeled_handlers[nfa_node]]
                if labels:
                    print "Report", self.nfa.match_types[nfa_node], labels
        for (name, tree) in ( ("NODE", self.node_tree),
                              ("ATTR", self.attr_tree),
                              ("PROCESSING-INSTRUCTION", self.pi_tree),
                              ("COMMENT", self.comment_tree) ):
            if tree is None:
                print " No", name, "tree"
            else:
                print name, "tree:"
                # The first branch is always true
                self._dump(tree.if_true, 0, numbering)
    def _dump(self, tree, depth, numbering):
        s = "-"*depth
        if isinstance(tree, set):
            if tree:
                k = sorted(tree)
                print s, "<>", numbering[frozenset(tree)], k
            else:
                print s, "<> (empty)"
        else:
            print s, tree.test, "?"
            self._dump(tree.if_true, depth+1, numbering)
            self._dump(tree.if_false, depth+1, numbering)

def all_transitions(nfa, current_dfa):
    transitions = []
    for node_id in current_dfa:
        if node_id is None:
            new_transitions = nfa.start_edges
        else:
            # XXX I can't transition from something
            # which wasn't a node or a record
            match_type = nfa.match_types[node_id]
            if match_type not in ("node", "record"):
                continue
            new_transitions = nfa.edges[node_id]

        transitions.extend(new_transitions)

    return transitions


def transition(nfa_state, event):
    for (to_node_id, test) in edge in nfa_state.edges:
        if edge[0] == event:
            yield edge[1]


# Raymond's code

def nfa_to_dfa(nfa):
    numbering = {} # from frozenset -> 0, 1, 2, ...
    dfa_start = frozenset([None]) # nfa start node
    result = {} # []
    seen = set([dfa_start])
    todo = [(dfa_start, None)]
    while todo:
        current_dfa, match_type = todo.pop()
        #print "All transitions from", current_dfa
        transitions = all_transitions(nfa, current_dfa)
        if not transitions:
            # Make sure there's always a target.
            # This also stores any handler events
            result[current_dfa] = StateTable(match_type, nfa, current_dfa)
            numbering[current_dfa] = len(numbering)
            continue

        # This adds element, attribute, comment, etc. transitions
        state_table = StateTable(match_type, nfa, current_dfa)
        for to_node_id, test in transitions:
            state_table.add(test, to_node_id)

        for nfa_nodes, match_type in state_table.get_final_nodes():
            some_dfa = frozenset(nfa_nodes)
            if some_dfa not in seen:
                seen.add(some_dfa)
                todo.append( (some_dfa, match_type) )
        result[current_dfa] = state_table
        numbering[current_dfa] = len(numbering)

    

#    for k, table in sorted(result.items(), key=lambda x:sorted(x[0])):
#        print "State", sorted(k)
#        table.dump()

    return result, numbering

def die(expr):
    import inspect
    print "  == FAILURE =="
    print type(expr)
    print dir(expr)
    for k, v in inspect.getmembers(expr):
        if k.startswith("__") and k.endswith("__"):
            continue
        print repr(k), repr(v)
    raise AssertionError(expr)


def build_states(nfa, dfa, numbering):
    # unique node numbers
    states = []
    for dfa_id, node_ids in sorted( (dfa_id, node_ids)
                                    for (node_ids, dfa_id) in numbering.items() ):
        assert dfa_id == len(states)
        if dfa_id == 0:
            assert node_ids == set([None])
            

        # handlers (which are in (id, class) pairs)
        table = dfa[node_ids]
        if dfa_id == 0:
            handlers = ()
        else:
            handler_map = {}
            for node_id in node_ids:
                for (label, handler) in nfa.labeled_handlers[node_id]:
                    handler_map[label] = handler
            # This are PushtreeHandler instances. I could find the
            # actual instances I need except the startElement and
            # endElement use different method.
            handlers = []
            for (label, handler) in sorted(handler_map.items()):
                handlers.append(handler)

        # node tree
        tree = table.node_tree.if_true
        if isinstance(tree, set):
            # Special case when there are no decisions to make
            if not tree:
                node_ops = []  # ... because there are no states
            else:
                node_ops = [(None, None, None, -numbering[frozenset(tree)])]
        else:
            node_ops = [tree]
            todo = [0]
            while todo:
                i = todo.pop()
                #print "Access", i, len(node_ops)
                tree = node_ops[i]
                if isinstance(tree.if_true, set):
                    if tree.if_true:
                        if_true = -numbering[frozenset(tree.if_true)]
                    else:
                        if_true = 0
                else:
                    if_true = len(node_ops)
                    node_ops.append(tree.if_true)
                    
                if isinstance(tree.if_false, set):
                    if tree.if_false:
                        if_false = -numbering[frozenset(tree.if_false)]
                    else:
                        if_false = 0
                else:
                    if_false = len(node_ops)
                    node_ops.append(tree.if_false)

                namespace, localname = tree.test.name
                node_ops[i] = (namespace, localname, None, if_true, if_false)
                #print "Added", node_ops[i]
                if if_false > 0:
                    todo.append(if_false)
                if if_true > 0:
                    todo.append(if_true)

        node_ops = tuple(node_ops)

        # attr tree
        attr_ops = []
        tree = table.attr_tree.if_true
        while not isinstance(tree, set):
            namespace, localname = tree.test.name
            attr_ops.append( (namespace, localname, numbering[frozenset(tree.if_true)]) )
            tree = tree.if_false
        if tree:
            # Match any attribute
            attr_ops.append( (None, None, numbering[frozenset(tree)]) )
        attr_ops = tuple(attr_ops)

        # processing instruction tree
        pi_ops = []
        tree = table.pi_tree.if_true
        while not isinstance(tree, set):
            target = tree.test.target
            pi_ops.append( (target, numbering[frozenset(tree.if_true)]) )
            tree = tree.if_false
        if tree:
            pi_ops.append( (None, numbering[frozenset(tree)]) )
        pi_ops = tuple(pi_ops)
        
        # comment tree
        tree = table.comment_tree.if_true
        assert isinstance(tree, set)
        if tree:
            comment_state = numbering[frozenset(tree)]
        else:
            comment_state = 0
        
        states.append( (handlers, node_ops, attr_ops, pi_ops, comment_state) )


    return tuple(states)

class Expression(object):
    def __init__(self, id, xpath, nfa):
        self.id = id
        self.xpath = xpath
        self._nfa = nfa


def nfas_to_machine_states(nfas):
    union_nfa = nfas[0].copy() # XXX start with empty and union everything?
    for nfa in nfas[1:]:
        union_nfa.union(nfa)
    dfa, numbering = nfa_to_dfa(union_nfa)
    return build_states(union_nfa, dfa, numbering)
        

class PushtreeManager(object):
    def __init__(self, subtree_xpath, subtree_handler = None, namespaces = None):
        if namespaces is None:
            namespaces = {}
        self.namespaces = namespaces
        self.expressions = []
        self._add(subtree_xpath, subtree_handler)
    def _add(self, xpath, xpath_handler):
        nfa = to_nfa(xpath_parser.parse(xpath), self.namespaces)
        i = len(self.expressions)
        nfa.add_handler((i, xpath_handler))
        exp = Expression(i, xpath, nfa)
        self.expressions.append(exp)
        return exp
    def add(self, xpath, xpath_handler=None):
        return self._add(xpath, xpath_handler)

    def _build_machine_states(self):
        return nfas_to_machine_states([x._nfa for x in self.expressions])
    def build_pushtree_handler(self):
        return RuleMachineHandler(self._build_machine_states())
    
# Special handler object to bridge with pushbind support in the builder
# Implemented by beazley.  Note:  This is not a proper SAX handler

class RuleMachineHandler(object):
    def __init__(self, machine_states):
        self.machine_states = machine_states

    def startDocument(self,node):
        self.stack = [0]
        #dump_machine_states(self.machine_states)

    def startElementNS(self, node, name, qname, attrs):
        state = self.stack[-1]
        #print "startElementNS", name, qname, attrs, "state", state
        if state == -1:
            #print "goto -1"
            self.stack.append(-1)
            return
        
        element_ops = self.machine_states[state][1]
        if not element_ops:
            # This was a valid target, but there's nothing leading off from it
            #print "GOTO -1"
            self.stack.append(-1)
            return
        
        namespace, localname = name
        i = 0
        while 1:
            ns, ln, test_function, if_true, if_false = element_ops[i]
            assert test_function is None
            if ((ns is None or ns == namespace) and
                (ln is None or ln == localname)):
                i = if_true
            else:
                i = if_false
            if i == 0:
                # dead-end; no longer part of the DFA and the
                # 0 node is defined to have no attributes
                self.stack.append(-1)
                return
            if i < 0:
                next_state = -i
                break
            # otherwise, loop

        #print "GoTo", next_state
        self.stack.append(next_state)

        handlers = self.machine_states[next_state][0]
        for handler in handlers:
            handler.startElementMatch(node)

        # Also handle any attributes
        attr_ops = self.machine_states[next_state][2]
        if not attr_ops:
            return

        for namespace, localname in attrs.keys():
            for (ns, ln, attr_state_id) in attr_ops:
                #print "attr test:", (ns, ln), (namespace, localname)
                if ((ns is None or namespace == ns) and
                    (ln is None or localname == ln)):
                    # Match!
                    handlers = self.machine_states[attr_state_id][0]
                    for handler in handlers:
                        #print "Notify attribute match:", event_ids, (namespace, localname)
                        # This is a hack until I can figure out how to get
                        # the attribute node
                        handler.attributeMatch( (node, (namespace, localname) ) )

    def endElementNS(self, node, name, qname):
        #print "endElementNS", node, name, qname
        last_state = self.stack.pop()
        if last_state == -1:
            return
        handlers = self.machine_states[last_state][0]
        for handler in reversed(handlers):
            handler.endElementMatch(node)
        
    def processingInstruction(self, node, target, data):
        state = self.stack[-1]
        if state == -1:
            return
        pi_ops = self.machine_states[state][3]
        for (pi_target, pi_state) in pi_ops:
            if pi_target == target:
                handlers = self.machine_states[pi_state][0]
                for handler in handlers:
                    handler.processingInstruction(node)

# For Dave
class RulePatternHandler(RuleMachineHandler):
    def __init__(self, pattern, end_node_handler, attr_handler, namespaces=None):
        self.xpm = xpm = ExpressionManager(namespaces=namespaces);
        xpm.add(pattern)
        nfa, dfa, numbering = xpm.build_dfa_tables()
        machine_states = build_instructions(nfa,dfa,numbering)
        RuleMachineHandler.__init__(self, machine_states,
                                    end_node_handler = end_node_handler,
                                    attr_handler = attr_handler)

def dump_machine_states(machine_states):
    for i, x in enumerate(machine_states):
        print "== INFO FOR", i, "=="
        handlers, node_ops, attr_ops, pi_ops, comment_state = x
        print " HANDLERS", handlers
        print " NODE OPS"
        for node_op in node_ops:
            print node_op
        print " ATTR OPS"
        for attr_op in attr_ops:
            print attr_op
        print " PI OPS"
        for pi_op in pi_ops:
            print pi_op
        print " COMMENT STATE =", comment_state

class PushtreeHandler(object):
    def startSubtree(self, element):
        pass
    def endSubtree(self, element):
        pass
    def startElementMatch(self, node):
        pass
    def endElementMatch(self, node):
        pass
    def attributeMatch(self, node):
        pass
    def commentMatch(self, node):
        pass
    def processingInstructionMatch(self, node):
        pass

class VerbosePushtreeHandler(PushtreeHandler):
    def __init__(self, prefix=None):
        if prefix is None:
            prefix = ""
        else:
            prefix = "(%s) " % (prefix,)
        self.prefix = prefix
    def startSubtree(self, element):
        print self.prefix+"startSubtree", element
    def endSubtree(self, element):
        print self.prefix+"endSubtree", element
    def startElementMatch(self, node):
        print self.prefix+"startElementMatch", node
        
    def endElementMatch(self, node):
        print self.prefix+"endElementMatch", node
    def attributeMatch(self, node):
        print self.prefix+"attributeMatch", node
    def commentMatch(self, node):
        print self.prefix+"commentMatch", node
    def processingInstructionMatch(self, node):
        print self.prefix+"processingInstructionMatch", node
    
    
if __name__ == '__main__':
    testxml = """\
<body>
<li>Ignore me<b/></li>
<ul>
 <li x='1'>This <i>is</i> test</li>
 <li x='2'><a href='spam'>that</a> was nothing</li>
 </ul>
 </body>
    """
    manager = PushtreeManager("body/ul/li", VerbosePushtreeHandler("main"))
    manager.expressions[0]._nfa.dump()
    manager.add("pre/post", VerbosePushtreeHandler("pre/post"))
    manager.expressions[1]._nfa.dump()
    manager.add("//a",  VerbosePushtreeHandler("//a"))
    manager.expressions[2]._nfa.dump()
    manager.add("@x",  VerbosePushtreeHandler("@x"))
    manager.expressions[3]._nfa.dump()
    manager.add("a",  VerbosePushtreeHandler("a"))
    manager.expressions[4]._nfa.dump()
    #manager.add(".//*")

    machine_states = manager._build_machine_states()
    dump_machine_states(machine_states)
    hand = RuleMachineHandler(machine_states)
    import os
    doc = amara.parse(testxml,rule_handler=hand)
    os._exit(0)
    

