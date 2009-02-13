from amara.test import test_case
from amara.xpath import datatypes

def _argstr(arg):
    #if isinstance(arg, unicode):
    #    return arg.encode('unicode_escape')
    # This is correct, we do want an exact type check
    if type(arg) in (tuple, list):
        return '(%s)' % ', '.join(_argstr(arg) for arg in arg)
    else:
        return unicode(arg)

class test_metaclass(type):
    # The name of module where the class to be tested is defined
    module_name = None
    # The name of the class to be tested
    class_name = None
    # The return type of the expression class' evaluate method
    return_type = None
    # list of test cases to add; item is a 2-item tuple of (args, expected)
    test_cases = ()

    def __init__(cls, name, bases, namespace):
        # load the expression factory
        if cls.module_name and cls.class_name:
            module = __import__(cls.module_name, {}, {}, [cls.class_name])
            factory = getattr(module, cls.class_name)
        # create the test methods
        digits = len(str(len(cls.test_cases)))
        for count, test in enumerate(cls.test_cases):
            args, expected, extra = cls.unpack_test_case(*test)
            if cls.return_type is not None:
                if not isinstance(expected, cls.return_type):
                    expected = cls.return_type(expected)
            test_method = cls.new_test_method(expected, factory, args, *extra)
            # build the docstring
            test_method.__doc__ = cls.class_name + _argstr(args)
            method_name = 'test_%s_%0*d' % (cls.class_name, digits, count)
            setattr(cls, method_name, test_method)

    def unpack_test_case(cls, args, expected, *extras):
        return args, expected, extras

    def new_test_method(cls, expected, factory, args, *extras):
        raise NotImplementedError


class test_xpath(test_case, object):
    __metaclass__ = test_metaclass

    def assertIsInstance(self, obj, cls):
        if isinstance(cls, tuple):
            expected = ' or '.join(cls.__name__ for cls in cls)
        else:
            expected = cls.__name__
        msg = "expected %s, not %s" % (expected, type(obj).__name__)
        self.assertTrue(isinstance(obj, cls), msg)

    def assertEquals(self, first, second, msg=None):
        if msg is None:
            msg = '%r == %r' % (first, second)
        # convert nan's to strings to prevent IEEE 754-style compares
        if isinstance(first, float) and isinstance(second, float):
            if datatypes.number(first).isnan():
                first = 'NaN'
            if datatypes.number(second).isnan():
                second = 'NaN'
        # convert nodesets to lists to prevent XPath-style nodeset compares
        elif isinstance(first, list) and isinstance(second, list):
            first, second = list(first), list(second)
        return test_case.assertEquals(self, first, second, msg)
    # update aliases as well
    assertEqual = failUnlessEqual = assertEquals
