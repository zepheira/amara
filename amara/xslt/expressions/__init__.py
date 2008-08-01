########################################################################
# amara/xslt/xpathextensions.py

class rtf_expression:
    def __init__(self, nodes):
        self.nodes = nodes

    def evaluate(self, context):
        processor = context.processor
        processor.pushResultTree(context.currentInstruction.xml_base)
        try:
            for child in self.nodes:
                child.instantiate(context, processor)
            result = processor.popResult()
        finally:
            #FIXME: This causes assertion error to be thrown in the event
            #of an exception in instantiating child nodes, which
            #masks the true exception.  Find a better way to clean up --UO
            #result = processor.popResult()
            pass
        return result

    def pprint(self, indent=''):
        print indent + str(self)

    def __str__(self):
        return '<RtfExpr at %x: %s>' % (id(self), str(self.nodes))


class sorted_expression:
    def __init__(self, expression, sortKeys):
        self.expression = expression
        self.sortKeys = sortKeys or []
        return

    def __str__(self):
        return "<SortedExpr at 0x%x: %s>" % (id(self), repr(self.expression))

    def compare(self, (node1, keys1), (node2, keys2)):
        for i in xrange(len(self.cmps)):
            diff = self.cmps[i](keys1[i], keys2[i])
            if diff: return diff
        # compare in document order
        # WARNING - This assumes domlette trees
        #return cmp(node1.docIndex, node2.docIndex)
        return cmp(node1, node2)

    def evaluate(self, context):
        if self.expression is None:
            base = context.node.xml_children
        else:
            base = self.expression.evaluate(context)
            if type(base) is not type([]):
                raise TypeError('expected nodeset, %s found' % type(base).__name__)

        # create initial sort structure
        state = context.copy()
        size = len(base)
        nodekeys = [None]*size
        pos = 1
        for node in base:
            context.node, context.position, context.size = node, pos, size
            context.currentNode = node
            keys = map(lambda sk, c=context: sk.evaluate(c), self.sortKeys)
            nodekeys[pos - 1] = (node, keys)
            pos += 1
        context.set(state)

        # get the compare function for each of the sort keys
        self.cmps = map(lambda sk, c=context: sk.getComparer(c), self.sortKeys)
        nodekeys.sort(self.compare)
        # extract the sorted nodes
        return map(lambda nk: nk[0], nodekeys)
