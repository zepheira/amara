########################################################################
# amara/xslt/exslt/__init__.py
from __future__ import absolute_import

from . import common
from . import datetime
from . import dynamic
from . import functions
from . import math
from . import regular_expressions
from . import sets
from . import strings

__all__ = ('extension_namespaces', 'extension_functions', 'extension_elements')

extension_namespaces, extension_functions, extension_elements = {}, {}, {}
for submodule in (common, dynamic, datetime, functions, math,
                  regular_expressions, sets, strings):
    extension_namespaces.update(getattr(submodule, 'extension_namespaces'))
    extension_functions.update(getattr(submodule, 'extension_functions'))
    extension_elements.update(getattr(submodule, 'extension_elements'))
