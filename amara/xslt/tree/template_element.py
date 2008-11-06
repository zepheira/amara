########################################################################
# amara/xslt/tree/template_element.py
"""
Implementation of the `xsl:template` element.
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

from call_template_element import call_template_element
from choose_elements import choose_element
from if_element import if_element
from variable_elements import param_element

class template_element(xslt_element):

    content_model = content_model.seq(
        content_model.rep(content_model.qname(XSL_NAMESPACE, 'xsl:param')),
        content_model.template,
        )
    attribute_types = {
        'match': attribute_types.pattern(),
        'name': attribute_types.qname(),
        'priority': attribute_types.number(),
        'mode': attribute_types.qname(),
        }

    _tail_recursive = False

    def __repr__(self):
      return "<template_element match='%s', name='%s', mode='%s', priority='%s'>" % (
          self._match, self._name, self._mode, self._priority)

    def setup(self):
        params = self._params = []
        for child in self.children:
            if isinstance(child, param_element):
                params.append((child, child._name))
            elif isinstance(child, xslt_element):
                break
        if self._params:
            self._instructions = self.children[len(self._params)+1:-1]
        else:
            self._instructions = self.children
        # Check for tail-recursive invocation (i.e, call-tempates of self)
        if self._name and self._instructions:
            endpoints = [self._instructions[-1]]
            queue = endpoints.append
            for last in endpoints:
                if isinstance(last, call_template_element):
                    if last._name == self._name:
                        self._tail_recursive = True
                        last._tail_recursive = True
                        break
                elif isinstance(last, if_element):
                    last = last.last_instruction
                    if last: queue(last)
                elif isinstance(last, choose_element):
                    for choice in last.children:
                        last = choice.last_instruction
                        if last: queue(last)
        return

    def _printTemplateInfo(self):
        info, tname = self.getTemplateInfo()
        if tname:
            print "Template named %r:" % tname
        else:
            print "Template matching pattern %r :" % self._match
        print "  location: line %d, col %d of %s" % \
                (self.lineNumber, self.columnNumber, self.baseUri)
        for shortcut in info:
            print "  shortcut:"
            importidx, priority, tmode, patterninfo, quickkey = shortcut
            print "    ...import index:", importidx
            print "    .......priority:", priority
            print "    ...........mode:", tmode
            if not tname:
                print "    ......quick key: node type %s, expanded-name %r" % quickkey
                print "    ........pattern: %r  for axis type %s" % patterninfo[0:2]
        return

    def instantiate(self, context, params=None):
        if params is None:
            params = {}

        if self._params:
            variables = context.variables
            context.variables = variables.copy()

        # The optimizer converts this to, roughly, a do/while loop
        while 1:
            context.recursive_parameters = None
            for child, param in self._params:
                if param in params:
                    context.variables[param] = params[param]
                else:
                    child.instantiate(context)

            for child in self._instructions:
                child.instantiate(context)

            # Update the params from the values given in
            # `recursive_parameters`.
            params = context.recursive_parameters
            if params is None:
                break

        if self._params:
            context.variables = variables
        return
