########################################################################
# $Header: /var/local/cvsroot/4Suite/Ft/Lib/ImportUtil.py,v 1.3 2006-12-08 22:52:20 jkloth Exp $
"""
Utilites for working with Python PEP 302 import hooks.

Copyright 2006-2008 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

import os
import sys
import imp
import time
import types
import cStringIO
from zipimport import zipimporter

__all__ = [
    # Module Utilities
    'find_loader', 'find_importer', 'get_importer', 'iter_modules',
    'get_last_modified', 'get_search_path', 'proxy_module',
    # Resource Utilities
    'os_path_to_resource', 'normalize_resource', 'get_resource_filename',
    'get_resource_string', 'get_resource_stream', 'get_resource_last_modified',
    ]

# Indicate that the use of "special" names is handled in a "zip-safe" way.
__zipsafe__ = True

IMP_SEARCH_ORDER = [ desc[0] for desc in imp.get_suffixes() ]

# ZIP imports always search for .pyc AND .pyo, but reverse their order
# depending on the optimzation flag (-O).
ZIP_SEARCH_ORDER = [ '.py', '.pyc', '.pyo']
if not __debug__:
    ZIP_SEARCH_ORDER.remove('.pyc')
    ZIP_SEARCH_ORDER.append('.pyc')

from pkgutil import iter_importers, get_loader, find_loader, iter_modules, get_importer

try:
    from pkg_resources import get_provider, resource_filename
except ImportError:
    #Then setuptools is not installed
    class default_provider(object):
        """Resource provider for "classic" loaders"""
        def __init__(self, module):
            self.loader = getattr(module, '__loader__', None)
            self.module_path = os.path.dirname(module.__file__)

        def get_resource_filename(self, manager, resource_name):
            return self._fn(self.module_path, resource_name)

        def get_resource_stream(self, manager, resource_name):
            return open(self._fn(self.module_path, resource_name), 'rb')

        def get_resource_string(self, manager, resource_name):
            stream = self.get_resource_stream(manager, resource_name)
            try:
                return stream.read()
            finally:
                stream.close()

        def has_resource(self, resource_name):
            return self._has(self._fn(self.module_path, resource_name))

        def resource_isdir(self, resource_name):
            return self._isdir(self._fn(self.module_path, resource_name))

        def resource_listdir(self, resource_name):
            return self._listdir(self._fn(self.module_path, resource_name))

        def _fn(self, base, resource_name):
            return os.path.join(base, *resource_name.split('/'))

        def _has(self, pathname):
            return os.path.exists(pathname)

        def _isdir(self, pathname):
            return os.path.isdir(pathname)

        def _listdir(self, pathname):
            return os.listdir(pathname)

    class zip_provider(default_provider):
        """Resource provider for ZIP loaders"""

        _dirindex = None

        def __init__(self, module):
            default_provider.__init__(self, module)
            self.zipinfo = self.loader._files
            self.zip_pre = self.loader.archive + os.sep

        def get_resource_filename(self, manager, resource_name):
            raise NotImplementedError("not supported by ZIP loaders")

        def get_resource_stream(self, manager, resource_name):
            data = self.get_resource_string(manager, resource_name)
            return cStringIO.StringIO(data)

        def get_resource_string(self, manager, resource_name):
            pathname = self._fn(self.module_path, resource_name)
            return self.loader.get_data(pathname)

        def _zipinfo_name(self, pathname):
            # Convert a virtual filename (full path to file) into a zipfile
            # subpath usable with the zipimport directory cache for our
            # target archive.
            if pathname.startswith(self.zip_pre):
                return pathname[len(self.zip_pre):]
            raise ValueError("%s not in %s" % (pathname, self.zip_pre))

        def _build_index(self):
            self._dirindex = index = {}
            for path in self.zipinfo:
                parts = path.split(os.sep)
                while parts:
                    parent = os.sep.join(parts[:-1])
                    if parent in index:
                        index[parent].append(parts[-1])
                        break
                    else:
                        index[parent] = [parts.pop()]
            return index

        def _has(self, pathname):
            arcname = self._zipinfo_name(fspath)
            return (arcname in self.zipinfo or
                    arcname in (self._dirindex or self._build_index()))

        def _isdir(self, pathname):
            arcname = self._zipinfo_name(pathname)
            return arcname in (self._dirindex or self._build_index())

        def _listdir(self, pathname):
            arcname = self._zipinfo_name(pathname)
            if arcname in (self._dirindex or self._build_index()):
                return self._dirindex[arcname][:]
            return []

    def get_provider(fullname):
        if fullname not in sys.modules:
            __import__(fullname)
        module = sys.modules[fullname]
        loader = getattr(module, '__loader__', None)
        if loader is None:
            provider = default_provider(module)
        elif isinstance(loader, zipimporter):
            provider = zip_provider(module)
        else:
            raise NotImplementedError('unsupported loader type: %s' % loader)
        return provider

    _resource_manager = None
else:
    # pkg_resources (aka setuptools) installed.; the resource_filename
    # top-level name is actually the bound method of the global
    # ResourceManager (at least that is what the PkgResources docs say).
    _resource_manager = resource_filename.im_self
    del resource_filename

def find_importer(fullname):
    """Find a PEP 302 "loader" object for fullname

    If fullname contains dots, path must be the containing package's
    __path__. Returns None if the module cannot be found or imported.
    """
    for importer in iter_importers(fullname):
        if importer.find_module(fullname) is not None:
            return importer
    return None

def get_last_modified(fullname):
    """
    Returns the last modified timestamp for the given module.
    """
    loader = get_loader(fullname)
    if hasattr(loader, 'get_filename'):
        suffixes = IMP_SEARCH_ORDER
    elif isinstance(loader, zipimporter):
        suffixes = ZIP_SEARCH_ORDER
    else:
        raise NotImplementedError("unsupported loader %s" % laoder)

    barename = '/' + fullname.replace('.', '/')
    if loader.is_package(fullname):
        barename += '/__init__'
    for suffix in suffixes:
        resource = barename + suffix
        try:
            timestamp = get_resource_last_modified(fullname, resource)
        except EnvironmentError:
            timestamp = 0
        else:
            break
    return timestamp

def get_search_path(fullname):
    loader = get_loader(fullname)
    if loader.is_package(fullname):
        if fullname in sys.modules:
            package = sys.modules[fullname]
        else:
            package = loader.load_module(fullname)
        return package.__path__
    return None

def proxy_module(fullname, realname):
    class moduleproxy(types.ModuleType):
        def __getattribute__(self, name):
            if realname not in sys.modules:
                # Load the module
                module = __import__(realname, {}, {}, [name])
                # Replace ourselves in `sys.modules`
                sys.modules[fullname] = module
            else:
                module = sys.modules[realname]
            return module.__getattribute__(name)
        def __repr__(self):
            return "<moduleproxy '%s' to '%s'>" % (fullname, realname)
    module = sys.modules[fullname] = moduleproxy(fullname)
    return module

# -- Resource Handling ------------------------------------------------

def OsPathToResource(pathname):
    components = []
    for component in pathname.split(os.sep):
        if component == '..':
            del components[-1:]
        elif component not in ('', '.'):
            components.append(component)
    resource = '/'.join(components)
    if pathname.startswith(os.sep):
        resource = '/' + resource
    return resource

def normalize_resource(package, resource):
    # normalize the resource pathname
    # Note, posixpath is not used as it doesn't remove leading '..'s
    components = []
    for component in resource.split('/'):
        if component == '..':
            del components[-1:]
        elif component not in ('', '.'):
            components.append(component)
    absolute = resource.startswith('/')
    resource = '/'.join(components)
    provider = get_provider(package)
    if absolute:
        # Find the provider for the distribution directory
        module_path = provider.module_path
        packages = package.split('.')
        if not get_loader(package).is_package(package):
            del packages[-1]
        for module in packages:
            module_path = os.path.dirname(module_path)
        provider.module_path = module_path
    return (provider, resource)

def get_resource_filename(package, resource):
    """Returns a true filesystem name for the specified resource.
    """
    provider, resource = normalize_resource(package, resource)
    return provider.get_resource_filename(_resource_manager, resource)

def get_resource_string(package, resource):
    """Return a string containing the contents of the specified resource.

    If the pathname is absolute it is retrieved starting at the path of
    the importer for 'fullname'.  Otherwise, it is retrieved relative
    to the module within the loader.
    """
    provider, resource = NormalizeResource(package, resource)
    return provider.get_resource_string(_resource_manager, resource)

def get_resource_stream(package, resource):
    """Return a readable stream for specified resource"""
    provider, resource = NormalizeResource(package, resource)
    return provider.get_resource_stream(_resource_manager, resource)

def get_resource_last_modified(package, resource):
    """Return a timestamp indicating the last-modified time of the
    specified resource.  Raises IOError is the pathname cannot be found
    from the loader for 'fullname'.
    """
    provider, resource = normalize_resource(package, resource)
    if isinstance(provider.loader, zipimporter):
        if not resource:
            # it is the archive itself
            timestamp = os.stat(provider.module_path).st_mtime
        else:
            filename = provider._fn(provider.module_path, resource)
            zipinfo_name = provider._zipinfo_name(filename)
            try:
                dostime, dosdate = provider.zipinfo[zipinfo_name][5:7]
            except:
                import errno
                errorcode = errno.ENOENT
                raise IOError(errorcode, os.strerror(errorcode), zipinfo_name)
            timestamp = time.mktime((
                ((dosdate >> 9)  & 0x7f) + 1980, # tm_year
                ((dosdate >> 5)  & 0x0f) - 1,    # tm_mon
                ((dosdate >> 0)  & 0x1f),        # tm_mday
                ((dostime >> 11) & 0x1f),        # tm_hour
                ((dostime >> 5)  & 0x3f),        # tm_min
                ((dostime >> 0)  & 0x1f) * 2,    # tm_secs
                0, 0, -1))
    else:
        filename = provider.get_resource_filename(_resource_manager, resource)
        timestamp = os.stat(filename).st_mtime
    return timestamp
