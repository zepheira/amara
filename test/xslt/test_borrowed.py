########################################################################
# test/xslt/test_borrowed.py

# This runs tests which came from external sources. Quoting Uche:
#
#    Borrowed was my old term for a test case that came form some real
#    world bug or use-case published somewhere.  In Amara I renamed
#    those "user case" tests (I also considered calling them "end
#    user", "black box" or "scenaio" tests), but we didn't apply that
#    renaming when we asked for help from the community to port the
#    "borrowed" tests from 4Suite.

import os
import glob
import warnings

from amara.lib import inputsource

from amara.test.xslt.xslt_support import _run_xml, _run_text, _run_html

# Collect a dictionary of test functions, created on the fly based on
# tests from the "borrowed" directory.

def _bootstrap():
    module_dir = os.path.dirname(os.path.abspath(__file__))
    borrowed_dir = os.path.join(module_dir, 'borrowed')
    tests = {}
    for source_xml in glob.iglob(os.path.join(borrowed_dir, '*.xml')):
        basename, ext = os.path.splitext(source_xml)
        transform_xml = basename + '.xslt'
        if not os.path.exists(transform_xml):
            warnings.warn('SKIP: missing XSLT for %r' % source_xml)
            continue

        expected_out = basename + '.out.xml'
        expected_txt = basename + '.out.txt'
        expected_html = basename + '.out.html'
        if os.path.exists(expected_out):
            def test_borrowed(source_xml=source_xml, transform_xml=transform_xml, expected=expected_out):
                _run_xml(
                    source_xml = inputsource(source_xml),
                    transform_xml = inputsource(transform_xml),
                    expected = inputsource(expected).stream.read())
        elif os.path.exists(expected_txt):
            def test_borrowed(source_xml=source_xml, transform_xml=transform_xml, expected=expected_txt):
                _run_text(
                    source_xml = inputsource(source_xml),
                    transform_xml = inputsource(transform_xml),
                    expected = inputsource(expected).stream.read())
        elif os.path.exists(expected_html):
            def test_borrowed(source_xml=source_xml, transform_xml=transform_xml, expected=expected_html):
                _run_html(
                    source_xml = inputsource(source_xml),
                    transform_xml = inputsource(transform_xml),
                    expected = inputsource(expected).stream.read())
        else:
            warnings.warn('SKIP: missing output for transform of %r' % source_xml)
            continue

        test_name = 'test_borrowed_' + os.path.basename(basename)
        test_borrowed.__name__ = test_name

        assert test_name not in tests
        tests[test_name] = test_borrowed

    return tests

# Add those tests to the global namespace
globals().update(_bootstrap())

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
