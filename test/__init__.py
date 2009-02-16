"""
Supporting definitions for the Python regression tests.

Mostly cribbed from Python core's: http://svn.python.org/view/python/trunk/Lib/test/test_support.py
(initially rev 62234)
"""

import contextlib
import errno
import socket
import sys
import os
import shutil
import warnings
import unittest
import types
import operator
import time

# Defined here as to have stack frames originating in this module removed
# from unittest reports. See `unittest.TestResult._is_relevant_tb_level()`
__unittest = True

class TestError(Exception):
    """Base class for regression test exceptions."""
    __slots__ = ('message', 'detail')
    def __init__(self, message=None, detail=None):
        self.message = message or 'assertion failed'
        self.detail = detail
    def __str__(self):
        return self.message

class TestFailed(TestError):
    """Test failed."""

class TestSkipped(TestError):
    """Test skipped.

    This can be raised to indicate that a test was deliberatly
    skipped, but not because a feature wasn't available.  For
    example, if some resource can't be used, such as the network
    appears to be unavailable, this should be raised instead of
    TestFailed.
    """

class ResourceDenied(TestSkipped):
    """Test skipped because it requested a disallowed resource.

    This is raised when a test calls requires() for a resource that
    has not be enabled.  It is used to distinguish between expected
    and unexpected skips.
    """

verbose = 1              # Flag set to 0 by regrtest.py
use_resources = None     # Flag set to [] by regrtest.py
max_memuse = 0           # Disable bigmem tests (they will still be run with
                         # small sizes, to make sure they work.)

# _original_stdout is meant to hold stdout at the time regrtest began.
# This may be "the real" stdout, or IDLE's emulation of stdout, or whatever.
# The point is to have some flavor of stdout the user can actually see.
_original_stdout = None
def record_original_stdout(stdout):
    global _original_stdout
    _original_stdout = stdout

def get_original_stdout():
    return _original_stdout or sys.stdout

def unload(name):
    try:
        del sys.modules[name]
    except KeyError:
        pass

def unlink(filename):
    try:
        os.unlink(filename)
    except OSError:
        pass

def rmtree(path):
    try:
        shutil.rmtree(path)
    except OSError, e:
        # Unix returns ENOENT, Windows returns ESRCH.
        if e.errno not in (errno.ENOENT, errno.ESRCH):
            raise

def forget(modname):
    '''"Forget" a module was ever imported by removing it from sys.modules and
    deleting any .pyc and .pyo files.'''
    unload(modname)
    for dirname in sys.path:
        unlink(os.path.join(dirname, modname + os.extsep + 'pyc'))
        # Deleting the .pyo file cannot be within the 'try' for the .pyc since
        # the chance exists that there is no .pyc (and thus the 'try' statement
        # is exited) but there is a .pyo file.
        unlink(os.path.join(dirname, modname + os.extsep + 'pyo'))

def is_resource_enabled(resource):
    """Test whether a resource is enabled.  Known resources are set by
    regrtest.py."""
    return use_resources is not None and resource in use_resources

def requires(resource, msg=None):
    """Raise ResourceDenied if the specified resource is not available.

    If the caller's module is __main__ then automatically return True.  The
    possibility of False being returned occurs when regrtest.py is executing."""
    # see if the caller's module is __main__ - if so, treat as if
    # the resource was set
    if sys._getframe().f_back.f_globals.get("__name__") == "__main__":
        return
    if not is_resource_enabled(resource):
        if msg is None:
            msg = "Use of the `%s' resource not enabled" % resource
        raise ResourceDenied(msg)

HOST = 'localhost'

def find_unused_port(family=socket.AF_INET, socktype=socket.SOCK_STREAM):
    """Returns an unused port that should be suitable for binding.  This is
    achieved by creating a temporary socket with the same family and type as
    the 'sock' parameter (default is AF_INET, SOCK_STREAM), and binding it to
    the specified host address (defaults to 0.0.0.0) with the port set to 0,
    eliciting an unused ephemeral port from the OS.  The temporary socket is
    then closed and deleted, and the ephemeral port is returned.

    Either this method or bind_port() should be used for any tests where a
    server socket needs to be bound to a particular port for the duration of
    the test.  Which one to use depends on whether the calling code is creating
    a python socket, or if an unused port needs to be provided in a constructor
    or passed to an external program (i.e. the -accept argument to openssl's
    s_server mode).  Always prefer bind_port() over find_unused_port() where
    possible.  Hard coded ports should *NEVER* be used.  As soon as a server
    socket is bound to a hard coded port, the ability to run multiple instances
    of the test simultaneously on the same host is compromised, which makes the
    test a ticking time bomb in a buildbot environment. On Unix buildbots, this
    may simply manifest as a failed test, which can be recovered from without
    intervention in most cases, but on Windows, the entire python process can
    completely and utterly wedge, requiring someone to log in to the buildbot
    and manually kill the affected process.

    (This is easy to reproduce on Windows, unfortunately, and can be traced to
    the SO_REUSEADDR socket option having different semantics on Windows versus
    Unix/Linux.  On Unix, you can't have two AF_INET SOCK_STREAM sockets bind,
    listen and then accept connections on identical host/ports.  An EADDRINUSE
    socket.error will be raised at some point (depending on the platform and
    the order bind and listen were called on each socket).

    However, on Windows, if SO_REUSEADDR is set on the sockets, no EADDRINUSE
    will ever be raised when attempting to bind two identical host/ports. When
    accept() is called on each socket, the second caller's process will steal
    the port from the first caller, leaving them both in an awkwardly wedged
    state where they'll no longer respond to any signals or graceful kills, and
    must be forcibly killed via OpenProcess()/TerminateProcess().

    The solution on Windows is to use the SO_EXCLUSIVEADDRUSE socket option
    instead of SO_REUSEADDR, which effectively affords the same semantics as
    SO_REUSEADDR on Unix.  Given the propensity of Unix developers in the Open
    Source world compared to Windows ones, this is a common mistake.  A quick
    look over OpenSSL's 0.9.8g source shows that they use SO_REUSEADDR when
    openssl.exe is called with the 's_server' option, for example. See
    http://bugs.python.org/issue2550 for more info.  The following site also
    has a very thorough description about the implications of both REUSEADDR
    and EXCLUSIVEADDRUSE on Windows:
    http://msdn2.microsoft.com/en-us/library/ms740621(VS.85).aspx)

    XXX: although this approach is a vast improvement on previous attempts to
    elicit unused ports, it rests heavily on the assumption that the ephemeral
    port returned to us by the OS won't immediately be dished back out to some
    other process when we close and delete our temporary socket but before our
    calling code has a chance to bind the returned port.  We can deal with this
    issue if/when we come across it."""
    tempsock = socket.socket(family, socktype)
    port = bind_port(tempsock)
    tempsock.close()
    del tempsock
    return port

def bind_port(sock, host=HOST):
    """Bind the socket to a free port and return the port number.  Relies on
    ephemeral ports in order to ensure we are using an unbound port.  This is
    important as many tests may be running simultaneously, especially in a
    buildbot environment.  This method raises an exception if the sock.family
    is AF_INET and sock.type is SOCK_STREAM, *and* the socket has SO_REUSEADDR
    or SO_REUSEPORT set on it.  Tests should *never* set these socket options
    for TCP/IP sockets.  The only case for setting these options is testing
    multicasting via multiple UDP sockets.

    Additionally, if the SO_EXCLUSIVEADDRUSE socket option is available (i.e.
    on Windows), it will be set on the socket.  This will prevent anyone else
    from bind()'ing to our host/port for the duration of the test.
    """
    if sock.family == socket.AF_INET and sock.type == socket.SOCK_STREAM:
        if hasattr(socket, 'SO_REUSEADDR'):
            if sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) == 1:
                raise TestFailed("tests should never set the SO_REUSEADDR "   \
                                 "socket option on TCP/IP sockets!")
        if hasattr(socket, 'SO_REUSEPORT'):
            if sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT) == 1:
                raise TestFailed("tests should never set the SO_REUSEPORT "   \
                                 "socket option on TCP/IP sockets!")
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)

    sock.bind((host, 0))
    port = sock.getsockname()[1]
    return port

FUZZ = 1e-6


def transient_internet():
    """Return a context manager that raises ResourceDenied when various issues
    with the Internet connection manifest themselves as exceptions."""
    time_out = TransientResource(IOError, errno=errno.ETIMEDOUT)
    socket_peer_reset = TransientResource(socket.error, errno=errno.ECONNRESET)
    ioerror_peer_reset = TransientResource(IOError, errno=errno.ECONNRESET)
    return contextlib.nested(time_out, socket_peer_reset, ioerror_peer_reset)


@contextlib.contextmanager
def captured_output(stream_name):
    """Run the 'with' statement body using a StringIO object in place of a
    specific attribute on the sys module.
    Example use (with 'stream_name=stdout')::

       with captured_stdout() as s:
           print "hello"
       assert s.getvalue() == "hello"
    """
    import StringIO
    orig_stdout = getattr(sys, stream_name)
    setattr(sys, stream_name, StringIO.StringIO())
    yield getattr(sys, stream_name)
    setattr(sys, stream_name, orig_stdout)

def captured_stdout():
    return captured_output("stdout")


#=======================================================================
# Big-memory-test support. Separate from 'resources' because memory use should be configurable.

# Some handy shorthands. Note that these are used for byte-limits as well
# as size-limits, in the various bigmem tests
_1M = 1024*1024
_1G = 1024 * _1M
_2G = 2 * _1G

# Hack to get at the maximum value an internal index can take.
class _Dummy:
    def __getslice__(self, i, j):
        return j
MAX_Py_ssize_t = _Dummy()[:]

def set_memlimit(limit):
    import re
    global max_memuse
    sizes = {
        'k': 1024,
        'm': _1M,
        'g': _1G,
        't': 1024*_1G,
    }
    m = re.match(r'(\d+(\.\d+)?) (K|M|G|T)b?$', limit,
                 re.IGNORECASE | re.VERBOSE)
    if m is None:
        raise ValueError('Invalid memory limit %r' % (limit,))
    memlimit = int(float(m.group(1)) * sizes[m.group(3).lower()])
    if memlimit > MAX_Py_ssize_t:
        memlimit = MAX_Py_ssize_t
    if memlimit < _2G - 1:
        raise ValueError('Memory limit %r too low to be useful' % (limit,))
    max_memuse = memlimit

def bigmemtest(minsize, memuse, overhead=5*_1M):
    """Decorator for bigmem tests.

    'minsize' is the minimum useful size for the test (in arbitrary,
    test-interpreted units.) 'memuse' is the number of 'bytes per size' for
    the test, or a good estimate of it. 'overhead' specifies fixed overhead,
    independant of the testsize, and defaults to 5Mb.

    The decorator tries to guess a good value for 'size' and passes it to
    the decorated test function. If minsize * memuse is more than the
    allowed memory use (as defined by max_memuse), the test is skipped.
    Otherwise, minsize is adjusted upward to use up to max_memuse.
    """
    def decorator(f):
        def wrapper(self):
            if not max_memuse:
                # If max_memuse is 0 (the default),
                # we still want to run the tests with size set to a few kb,
                # to make sure they work. We still want to avoid using
                # too much memory, though, but we do that noisily.
                maxsize = 5147
                self.failIf(maxsize * memuse + overhead > 20 * _1M)
            else:
                maxsize = int((max_memuse - overhead) / memuse)
                if maxsize < minsize:
                    # Really ought to print 'test skipped' or something
                    if verbose:
                        sys.stderr.write("Skipping %s because of memory "
                                         "constraint\n" % (f.__name__,))
                    return
                # Try to keep some breathing room in memory use
                maxsize = max(maxsize - 50 * _1M, minsize)
            return f(self, maxsize)
        wrapper.minsize = minsize
        wrapper.memuse = memuse
        wrapper.overhead = overhead
        return wrapper
    return decorator

def bigaddrspacetest(f):
    """Decorator for tests that fill the address space."""
    def wrapper(self):
        if max_memuse < MAX_Py_ssize_t:
            if verbose:
                sys.stderr.write("Skipping %s because of memory "
                                 "constraint\n" % (f.__name__,))
        else:
            return f(self)
    return wrapper

#=======================================================================
# unittest integration.


class test_case(unittest.TestCase):
    failureException = TestFailed

    def run(self, result):
        result.startTest(self)
        if result.simulate:
            testMethod = lambda: None
        else:
            testMethod = getattr(self, self._testMethodName)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                return

            ok = False
            try:
                testMethod()
                ok = True
            except self.failureException:
                result.addFailure(self, self._exc_info())
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())

            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                ok = False
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)

    def assertIsInstance(self, obj, cls):
        if isinstance(cls, tuple):
            expected = ' or '.join(cls.__name__ for cls in cls)
        else:
            expected = cls.__name__
        msg = "expected %s, not %s" % (expected, type(obj).__name__)
        self.assertTrue(isinstance(obj, cls), msg)


class test_loader(unittest.TestLoader):
    """
    Extends `unittest.TestLoader` to support defining TestCases as members
    of a TestSuite.
    """
    def loadTestsFromTestSuite(self, testSuiteClass):
        """Return a suite of all tests cases contained in `testSuiteClass`."""
        cases = []
        for name in dir(testSuiteClass):
            obj = getattr(testSuiteClass, name)
            if (isinstance(obj, (type, types.ClassType)) and
                issubclass(obj, unittest.TestCase)):
                cases.append(obj)
        tests = []
        for case in sorted(cases, key=operator.attrgetter('__name__')):
            tests.append(self.loadTestsFromTestCase(case))
        return testSuiteClass(tests)

    def loadTestsFromModule(self, module):
        suites, cases = [], []
        for name, obj in vars(module).iteritems():
            if (isinstance(obj, (type, types.ClassType))
                and '__unittest__' not in obj.__dict__
                and '__unittest' not in sys.modules[obj.__module__].__dict__):
                if issubclass(obj, unittest.TestSuite):
                    suites.append(obj)
                elif issubclass(obj, unittest.TestCase):
                    cases.append(obj)
        tests = []
        for suite in sorted(suites, key=operator.attrgetter('__name__')):
            tests.append(self.loadTestsFromTestSuite(suite))
        for case in sorted(cases, key=operator.attrgetter('__name__')):
            tests.append(self.loadTestsFromTestCase(case))
        return self.suiteClass(tests)


# On Windows, the best timer is time.clock().
# On most other platforms the best timer is time.time().
if sys.platform == 'win32':
    default_timer = time.clock
else:
    default_timer = time.time

class _test_result(unittest.TestResult):

    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream, verbosity, simulate, timer=default_timer):
        unittest.TestResult.__init__(self)
        self.stream = stream
        self.dots = verbosity == 1
        self.verbose = verbosity > 1
        self.simulate = simulate
        self.timer = timer
        self.total_time = 0
        return

    def startSuite(self):
        self.total_time = self.timer()
        return

    def stopSuite(self):
        stop_time = self.timer()
        self.total_time = stop_time - self.total_time
        if self.dots:
            self.stream.write('\n')
        return

    def _write_errors(self, what, errors, color):
        for test, err in errors:
            self.stream.write(self.separator1 + '\n')
            self.stream.setcolor(color)
            description = test.shortDescription() or str(test)
            self.stream.write('%s: %s\n' % (what, description))
            self.stream.setcolor('NORMAL')
            self.stream.write(self.separator2 + '\n')
            self.stream.write(err + '\n')
        return len(errors)

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        if self.verbose:
            self.stream.write('%s ... ' % (test.shortDescription() or test))

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        if self.dots:
            self.stream.setcolor('GREEN')
            self.stream.write('.')
            self.stream.setcolor('NORMAL')
        elif self.verbose:
            self.stream.setcolor('GREEN')
            self.stream.write('OK')
            self.stream.setcolor('NORMAL')
            self.stream.write('\n')

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        if self.dots:
            self.stream.setcolor('WHITE')
            self.stream.write('E')
            self.stream.setcolor('NORMAL')
        elif self.verbose:
            self.stream.setcolor('WHITE')
            self.stream.write('ERROR')
            self.stream.setcolor('NORMAL')
            self.stream.write('\n')

    def addFailure(self, test, err):
        exc, val, tb = err
        if self.verbose and issubclass(exc, TestError):
            err = val.detail or val.message
            self.failures.append((test, err))
        else:
            unittest.TestResult.addFailure(self, test, err)
        if self.dots:
            self.stream.setcolor('RED')
            self.stream.write('F')
            self.stream.setcolor('NORMAL')
        elif self.verbose:
            self.stream.setcolor('RED')
            self.stream.write('FAIL')
            self.stream.setcolor('NORMAL')
            self.stream.write('\n')


_ansi_terms = frozenset([
    'linux', 'console', 'con132x25', 'con132x30', 'con132x43',
    'con132x60', 'con80x25', 'con80x28', 'con80x30', 'con80x43',
    'con80x50', 'con80x60', 'xterm', 'xterm-color', 'color-xterm',
    'vt100', 'vt100-color', 'rxvt', 'ansi', 'Eterm', 'putty',
    'vt220-color', 'cygwin',
    ])

class _test_stream(object):
    def __init__(self, stream):
        self._stream = stream
        self._encoding = getattr(stream, 'encoding', None)
        if stream.isatty():
            if sys.platform == 'win32':
                # assume Windows console (cmd.exe or the like)
                self._init_win32()
            elif os.name == 'posix' and os.environ.get('TERM') in _ansi_terms:
                self._colors = {
                    'NORMAL': '\033[0m',
                    'RED': '\033[1;31m',
                    'GREEN': '\033[1;32m',
                    'YELLOW': '\033[1;33m',
                    'WHITE': '\033[1;37m',
                }
                self.setcolor = self._setcolor_ansi

    def _init_win32(self):
        import ctypes
        import msvcrt
        class COORD(ctypes.Structure):
            _fields_ = [('x', ctypes.c_short), ('y', ctypes.c_short)]
        class SMALL_RECT(ctypes.Structure):
            _fields_ = [('left', ctypes.c_short), ('top', ctypes.c_short),
                        ('right', ctypes.c_short), ('bottom', ctypes.c_short),
                        ]
        class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
            _fields_ = [('dwSize', COORD),
                        ('dwCursorPosition', COORD),
                        ('wAttributes', ctypes.c_short),
                        ('srWindow', SMALL_RECT),
                        ('dwMaximumSize', COORD),
                        ]
        # Apparently there exists an IDE where isatty() is True, but
        # the stream doesn't have a backing file descriptor.
        try:
            fileno = self._stream.fileno()
        except AttributeError:
            return
        try:
            self._handle = msvcrt.get_osfhandle(fileno)
        except:
            return
        info = CONSOLE_SCREEN_BUFFER_INFO()
        pinfo = ctypes.byref(info)
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(self._handle, pinfo)
        self._colors = {
            'NORMAL': info.wAttributes,
            'RED': 12, # INTENSITY (8) | RED (4)
            'GREEN': 10, # INTENSITY (8) | GREEN (2)
            'YELLOW': 14, # INTENSITY (8) | GREEN (2) | RED (1)
            'WHITE': 15, # INTENSITY (8) | BLUE (1) | GREEN (2) | RED (4)
        }
        self.setcolor = self._setcolor_win32

    def _setcolor_ansi(self, color):
        self._stream.write(self._colors[color])

    def _setcolor_win32(self, color):
        import ctypes
        attr = self._colors[color]
        ctypes.windll.kernel32.SetConsoleTextAttribute(self._handle, attr)

    def __getattr__(self, name):
        return getattr(self._stream, attr)

    def write(self, data):
        if isinstance(data, unicode) and self._encoding is not None:
            data = data.encode(self._encoding)
        self._stream.write(data)

    def setcolor(self, color):
        return


class test_runner(object):
    """
    A test runner the display results in colorized textual form.
    """
    __slots__ = ('stream', 'verbosity', 'simulate')

    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream=None, verbosity=1, simulate=False):
        self.stream = _test_stream(stream or sys.stderr)
        self.verbosity = verbosity
        self.simulate = simulate

    def run(self, test):
        # Run the tests
        result = _test_result(self.stream, self.verbosity, self.simulate)
        result.startSuite()
        test(result)
        result.stopSuite()

        # Display details for unsuccessful tests
        for items, what, color in [(result.failures, 'FAIL', 'RED'),
                                   (result.errors, 'ERROR', 'WHITE')]:
            for test, traceback in items:
                self.stream.write(self.separator1 + '\n')
                self.stream.setcolor(color)
                description = test.shortDescription() or str(test)
                self.stream.write('%s: %s\n' % (what, description))
                self.stream.setcolor('NORMAL')
                self.stream.write(self.separator2 + '\n')
                self.stream.write(traceback + '\n')

        # Display the summary
        failed = []
        if result.failures:
            failed.append('failures=%d' % len(result.failures))
        if result.errors:
            failed.append('errors=%d' % len(result.errors))
        if failed:
            status = 'FAILED (%s)' % ', '.join(failed)
            color = 'RED'
            self.stream.write(self.separator1 + '\n')
        else:
            status = 'OK'
            color = 'GREEN'
            if self.verbosity > 0:
                self.stream.write(self.separator1 + '\n')

        summary = 'Ran %d tests in %0.3fs' % (result.testsRun,
                                              result.total_time)

        self.stream.write('%s ... ' % summary)
        self.stream.setcolor(color)
        self.stream.write(status)
        self.stream.setcolor('NORMAL')
        self.stream.write('\n')
        return result


def test_main(*modules):
    if not modules:
        modules = ('__main__',)

    def load_module(module):
        if not isinstance(module, types.ModuleType):
            module = __import__(module, {}, {}, ['__name__'])
        return module

    def usage_exit(msg=None):
        progName = os.path.basename(sys.argv[0] or __file__)
        if msg: print msg
        print unittest.TestProgram.USAGE % locals()
        raise SystemExit(2)

    # parse args
    import getopt
    verbosity = 1
    simulate = False
    try:
        options, args = getopt.getopt(sys.argv[1:], 'hvqn', 
                                      ['help', 'verbose', 'quiet', 'dry-run'])
        for option, value in options:
            if option in ('-h', '--help'):
                usage_exit()
            if option in ('-q', '--quiet'):
                verbosity -= 1
            if option in ('-v', '--verbose'):
                verbosity += 1
            if option in ('-n', '--dry-run'):
                simulate = True
    except getopt.error, msg:
        usage_exit(msg)

    # create the tests
    loader = test_loader()
    if args:
        suites = []
        for module in modules:
            if not isinstance(module, types.ModuleType):
                module = __import__(module, {}, {}, ['__name__'])
            suites.append(loader.loadTestsFromNames(args, module))
        test = loader.suiteClass(suites)
    else:
        test = loader.loadTestsFromNames(modules)

    # run the tests
    runner = test_runner(sys.stderr, verbosity, simulate)
    result = runner.run(test)
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    test_main()
