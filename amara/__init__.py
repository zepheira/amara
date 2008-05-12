########################################################################
# amara/__init__.py

XML_NAMESPACE = u"http://www.w3.org/XML/1998/namespace"
XMLNS_NAMESPACE = u"http://www.w3.org/2000/xmlns/"

class Error(Exception):

    _message_table = None

    # defer localization of the messages until needed
    def __new__(cls, code, **kwds):
        if cls._message_table is None:
            cls._message_table = cls._load_messages()
            # change `cls.__new__` to default __new__ as loading is complete
            # and will just waste cycles.
            cls.__new__ = Exception.__new__
        return Exception.__new__(cls)

    def __init__(self, code, **kwds):
        assert self._message_table is not None
        message = self._message_table[code]
        if kwds:
            message %= kwds
        Exception.__init__(self, code, message)
        self.code = code
        self.message = message
        # map keywords into attributes
        for name, value in kwds.iteritems():
            setattr(self, name, value)

    def __str__(self):
        return self.message

    @classmethod
    def _load_messages(cls):
        raise NotImplementedError("subclass %s must override" % cls.__name__)


class ReaderError(Error):
    pass


class XIncludeError(ReaderError):
    pass
