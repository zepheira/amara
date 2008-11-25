########################################################################
# amara/xslt/extensions/__init__.py
from __future__ import absolute_import

from . import functions
from . import elements

__all__ = ('extension_namespaces', 'extension_functions', 'extension_elements')

extension_namespaces, extension_functions, extension_elements = {}, {}, {}
for submodule in (functions, elements):
    extension_namespaces.update(getattr(submodule, 'extension_namespaces'))
    extension_functions.update(getattr(submodule, 'extension_functions'))
    extension_elements.update(getattr(submodule, 'extension_elements'))
