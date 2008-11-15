########################################################################
# test/xslt/test_borrowed.py
import os
import glob
import warnings

from amara.test import test_main
from amara.test.xslt import xslt_test, filesource

def __bootstrap__(module_dict):
    module_dir = os.path.dirname(os.path.abspath(__file__))
    borrowed_dir = os.path.join(module_dir, 'borrowed')
    for source in glob.iglob(os.path.join(borrowed_dir, '*.xml')):
        basename, ext = os.path.splitext(source)
        transform = basename + '.xslt'
        expected = basename + '.out'
        if not os.path.exists(transform):
            warnings.warn('SKIP: missing XSLT for %r' % source)
            continue
        if not os.path.exists(expected):
            warnings.warn('SKIP: missing output for transform of %r' % source)
            continue
        class_name = 'test_borrowed_' + os.path.basename(basename)
        class_dict = {
            'source': filesource(source),
            'transform': filesource(transform),
            'expected': open(expected).read(),
            }
        source = filesource(source)
        module_dict[class_name] = type(class_name, (xslt_test,), class_dict)
    global __bootstrap__
    del __bootstrap__
    return
__bootstrap__(locals())


if __name__ == '__main__':
    test_main()
