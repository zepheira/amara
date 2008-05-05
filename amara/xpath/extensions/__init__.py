########################################################################
# amara/xpath/extensions/__init__.py
"""
4XPath-specific extensions.

Extension functions are implemented by a module, such as this one,
that defines an `extension_functions` global dictionary that maps (namespace,
local-name) string tuples to a corresponding Python function. The
function must take an `xpathcontext` object as the first argument, and any
additional arguments accepted will correspond to the arguments passed
in. See other API docs to see how to make use of modules that contain
`extension_functions`.
"""

EXTENSION_NAMESPACE = 'http://xmlns.4suite.org/ext'

extension_functions = {}