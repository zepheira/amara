########################################################################
# amara/xslt/expressions.py
import operator

class rtf_expression:
    def __init__(self, instruction):
        self.instruction = instruction

    def evaluate(self, context):
        context.push_tree_writer(self.instruction.baseUri)
        try:
            self.instruction.process_children(context)
        finally:
            writer = context.pop_writer()
        return writer.get_result()

    def pprint(self, indent=''):
        print indent + str(self)

    def __str__(self):
        return '<rtf_expression at %x: %s>' % (id(self), self.instruction)


class sorted_expression:
    def __init__(self, expression, keys):
        self.expression = expression
        self.keys = tuple(reversed(keys or ()))
        return

    def __str__(self):
        return "<sorted_expression at 0x%x: %r>" % (id(self), self.expression)

    def evaluate_as_nodeset(self, context):
        if self.expression is None:
            nodes = context.node.xml_children
        else:
            nodes = self.expression.evaluate_as_nodeset(context)

        # create initial sort structure
        initial_focus = context.node, context.position, context.size
        context.size = size = len(nodes)
        decorated = [None]*size
        position = 0
        for node in nodes:
            keys = decorated[position] = [node]
            position += 1
            context.node = context.current_node = node
            context.position = position
            keys[1:] = [ key.get_key(context) for key in self.keys ]
        context.node, context.position, context.size = initial_focus

        # Now sort the nodes based on the `xsl:sort` parameters
        index = 1
        for key in self.keys:
            compare, reverse = key.get_parameters(context)
            decorated.sort(cmp=compare, key=operator.itemgetter(index),
                           reverse=reverse)
            index += 1
        return map(operator.itemgetter(0), decorated)
    evaluate = evaluate_as_nodeset
