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
        self.event_ids = {}

    def copy(self):
        nfa = NFA()
        nfa.start_edges[:] = self.start_edges
        nfa.edges.update(self.edges)
        nfa.terminal_nodes.update(self.terminal_nodes)
        nfa.match_types.update(self.match_types)
        nfa.event_ids.update(self.event_ids)

    def get_edges(self, node_id):
        if node_id is None:
            return self.start_edges
        return self.edges[node_id]

    def add_event_id(self, event_id):
        for node_id in self.terminal_nodes:
            self.event_ids[node_id].append(event_id)


    def new_node(self, from_node_id, test):
        edges = self.get_edges(from_node_id)
        to_node_id = next(counter)
        self.edges[to_node_id] = []
        self.match_types[to_node_id] = test.match_type
        self.event_ids[to_node_id] = []
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
        self.event_ids.update(other.event_ids)

    def union(self, other):
        assert not set(self.edges) & set(other.edges), "non-empty intersection"
        self.start_edges.extend(other.start_edges)
        self.edges.update(other.edges)
        self.match_types.update(other.match_types)
        self.terminal_nodes.update(other.terminal_nodes)
        self.event_ids.update(other.event_ids)

    def dump(self):
        for node_id, edges in [(None, self.start_edges)] + sorted(self.edges.items()):
            if node_id is None:
                node_name = "(start)"
                events = ""
            else:
                node_name = str(node_id)
                action = str(self.match_types[node_id])
                events += " " + str(self.event_ids[node_id])
            is_terminal = "(terminal)" if (node_id in self.terminal_nodes) else ""
            print node_name, is_terminal, events
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
    if (expr.__class__ is locationpaths.relative_location_path):
        # This is a set of path specifiers like
        #  "a" "a/b", "a/b/c[0]/d[@x]"   (relative location path)
        #  "@a", "a/@b", and even "@a/@b", which gives nothing
        # It should match with an arbitrary number of nodes as parents.
        nfa = NFA()
        for step in expr._steps:
            nfa.extend(to_nfa(step, namespaces))
        # The above is rooted. I want an unrooted version
        # That means allowing any number of nodes as parents.
        _add_initial_loop(nfa)

        return nfa

    if (expr.__class__ is locationpaths.absolute_location_path or
        expr.__class__ is locationpaths.abbreviated_absolute_location_path):
        
        # This is an absolute path like
        #   "/a", "/a[0]/b[@x]"
        # or an abbreviated_absolute_location_path
        #  "//a" (?? did I do this right? I don't thinks so. XXX)
        
        nfa = NFA()
        for step in expr._steps:
            nfa.extend(to_nfa(step, namespaces))
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
        else:
            die(node_test)

        nfa.terminal_nodes.add(node_id)

        if axis_name == "descendant":
            _add_initial_loop(nfa)
            
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

class Branch(object):
    def __init__(self, test, if_true, if_false):
        self.test = test
        self.if_true = if_true
        self.if_false = if_false


class StateTable(object):
    def __init__(self, nfa, nfa_node_ids):
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
        result = set()
        for tree in (self.node_tree, self.attr_tree, self.pi_tree, self.comment_tree):
            visit = [tree]
            while visit:
                node = visit.pop()
                if isinstance(node, set):
                    if node:
                        result.add(frozenset(node))
                elif node is not None:
                    visit.append(node.if_true)
                    visit.append(node.if_false)
        return result

    def dump(self, numbering):
        # Do I report anything for having reached here?
        if list(self.nfa_node_ids) != [None]:
            for nfa_node in self.nfa_node_ids:
                event_ids = self.nfa.event_ids[nfa_node]
                if event_ids:
                    print "Report", self.nfa.match_types[nfa_node], event_ids
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

'''
    def prune(self, dfa):
        self.tree = self._prune(dfa, self.tree)
    def _prune(self, dfa, tree):
        if tree is None:
            return tree
        if isinstance(tree.if_true, Branch):
            tree.if_true = self._prune(dfa, tree.if_true)
        if isinstance(tree.if_false, Branch):
            tree.if_false = self._prune(dfa, tree.if_false)
            
        if isinstance(tree.if_true, set):
            x = frozenset(tree.if_true)
            if x not in dfa:
                tree.if_true = set()
        if isinstance(tree.if_false, set):
            x = frozenset(tree.if_false)
            if x not in dfa:
                tree.if_false = set()
        if not tree.if_true and not tree.if_false:
            return set()
        return tree
'''
                
def all_transitions(nfa, current_dfa):
    transitions = []
    for node_id in current_dfa:
        if node_id is None:
            new_transitions = nfa.start_edges
        else:
            # XXX I can't transition from something
            # which wasn't a node
            match_type = nfa.match_types[node_id]
            if match_type != "node":
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
    todo = [dfa_start]
    while todo:
        current_dfa = todo.pop()
        #print "All transitions from", current_dfa
        transitions = all_transitions(nfa, current_dfa)
        #print transitions
        if not transitions:
            # Make sure there's always a target.
            # This also stores any reporting events.
            result[current_dfa] = StateTable(nfa, current_dfa)
            numbering[current_dfa] = len(numbering)
            continue

        # This adds element, attribute, comment, etc. transitions
        state_table = StateTable(nfa, current_dfa)
        for to_node_id, test in transitions:
            state_table.add(test, to_node_id)

        for nfa_nodes in state_table.get_final_nodes():
            some_dfa = frozenset(nfa_nodes)
            if some_dfa not in seen:
                seen.add(some_dfa)
                todo.append(some_dfa)
        result[current_dfa] = state_table
        numbering[current_dfa] = len(numbering)

#    for k, table in sorted(result.items(), key=lambda x:sorted(x[0])):
#        print "State", sorted(k)
#        table.dump()

    return result, numbering

def dfa_dump(dfa, numbering):
    if not dfa:
        print "EMPTY DFA"
        return
    
    for id, k, table in sorted((numbering[k], k, v) for (k,v) in dfa.items()):
        print "State", id, k
        table.dump(numbering)
        
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


def build_instructions(nfa, dfa, numbering):
    # unique node numbers
    states = []
    for dfa_id, node_ids in sorted( (dfa_id, node_ids)
                                    for (node_ids, dfa_id) in numbering.items() ):
        assert dfa_id == len(states)
        if dfa_id == 0:
            assert node_ids == set([None])

        # event identifiers
        table = dfa[node_ids]
        if dfa_id == 0:
            event_identifiers = ()
        else:
            event_ids = set()
            for node_id in node_ids:
                event_ids.update(nfa.event_ids[node_id])
            event_identifiers = tuple(sorted(event_ids))

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
                    if tree:
                        if_true = -numbering[frozenset(tree.if_true)]
                    else:
                        if_true = 0
                else:
                    if_true = len(node_ops)
                    node_ops.append(tree.if_true)
                    
                if isinstance(tree.if_false, set):
                    if tree:
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
        
        states.append( (event_identifiers, node_ops, attr_ops, pi_ops, comment_state) )

    return tuple(states)

class Expression(object):
    def __init__(self, id, xpath, nfa):
        self.id = id
        self.xpath = xpath
        self._nfa = nfa

class ExpressionManager(object):
    def __init__(self, namespaces = None):
        if namespaces is None:
            namespaces = {}
        self._expressions = []
        self.namespaces = namespaces
    def add(self, xpath, context=None): # XXX context
        nfa = to_nfa(xpath_parser.parse(xpath), self.namespaces)
        i = len(self._expressions)
        nfa.add_event_id(i)
        self._expressions.append(Expression(i, xpath, nfa))

    def build_dfa_tables(self):
        nfa = self._expressions[0]._nfa
        for expr in self._expressions[1:]:
            nfa.union(expr._nfa)
        dfa, numbering = nfa_to_dfa(nfa)
        return nfa, dfa, numbering

# Special handler object to bridge with pushbind support in the builder
# Implemented by beazley.  Note:  This is not a proper SAX handler

class RuleMachineHandler(object):
    def __init__(self, machine_states, node_handler=None):
        self.machine_states = machine_states
        self.node_handler = node_handler

    def startDocument(self,node):
        self.stack = [0]

    def startElementNS(self, node, name, qname, attrs):
        #print "startElementNS", name, qname, attrs
        state = self.stack[-1]
        if state == -1:
            self.stack.append(-1)
            return
        
        element_ops = self.machine_states[state][1]
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
                # dead-end ?
                1/0
            if i < 0:
                next_state = -i
                break
            # otherwise, loop

        self.stack.append(next_state)

        #event_ids = self.machine_states[next_state][0]
        #if event_ids:
        #    print "Notify node match:", event_ids, name

        # Also handle any attributes
        attr_ops = self.machine_states[next_state][2]

        for namespace, localname in attrs.keys():
            for (ns, ln, attr_state_id) in attr_ops:
                if ((ns is None or namespace == ns) and
                    (ln is None or localname == ln)):
                    # Match!
                    event_ids = self.machine_states[attr_state_id][0]
                    if event_ids:
                        # print "Notify attribute match:", event_ids, (namespace, localname)
                        if self.node_handler:
                            self.node_handler(node)

    def endElementNS(self, node, name, qname):
        #print "endElementNS", node, name, qname
        last_state = self.stack.pop()
        event_ids = self.machine_states[last_state][0]
        if event_ids:
            #print "Notify node match:", event_ids, name
            if self.node_handler:
                self.node_handler(node)
        
    def processingInstruction(self, node, target, data):
        print "PI", node, repr(target), "AND", data
        state = self.stack[-1]
        if state == -1:
            return
        pi_ops = self.machine_states[state][3]
        for (pi_target, pi_state) in pi_ops:
            if pi_target == target:
                event_ids = self.machine_states[pi_state][0]
                if event_ids:
                    #print "Notify PI match:", event_ids, target
                    if self.node_handler:
                        self.node_handler(node)

class RulePatternHandler(RuleMachineHandler):
    def __init__(self, pattern,node_handler=None,namespaces=None):
        xpm = ExpressionManager(namespaces=namespaces);
        xpm.add(pattern)
        nfa, dfa, numbering = xpm.build_dfa_tables()
        machine_states = build_instructions(nfa,dfa,numbering)
        RuleMachineHandler.__init__(self,machine_states,node_handler)
                    
if __name__ == '__main__':
    #1/0
    print "========="
    xpm = ExpressionManager(namespaces = {"q": "http://spam.com/"})
    xpm.add("/a")
    xpm.add("/a//q:a")
    xpm.add("processing-instruction('xml-stylesheet')")
    #xpm.add("/b//c")
    xpm.add("c/@d")
    nfa, dfa, numbering = xpm.build_dfa_tables()
    dfa_dump(dfa, numbering)

    print "FINAL"
    machine_states = build_instructions(nfa, dfa, numbering)
    for i, x in enumerate(machine_states):
        print "== INFO FOR", i, "=="
        event_ids, node_ops, attr_ops, pi_ops, comment_state = x
        print " EVENTS", event_ids
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

    import cStringIO as StringIO
    import amara

    def print_node(n):
        print n
    
    hand = RuleMachineHandler(machine_states,print_node)
    hand = RulePatternHandler("//a",print_node)
    testdoc = StringIO.StringIO("""\
    <a xmlns:x='http://spam.com/'>
    <?xml-stylesheet href='mystyle.css' type='text/css'?>
    <blah>
    <x:a b='2'></x:a>
    </blah>
    <c d='3'/>
    </a>
    """)

    doc = amara.parse(testdoc,rule_handler=hand)
    

