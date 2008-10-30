#######################################################################
# amara/xslt/result.py
import operator
import cStringIO

from amara.writers import outputparameters, treewriter
from amara.xslt import proxywriter

__all__ = ('result', 'streamresult', 'stringresult', 'treeresult')

class result(object):

    writer_factory = proxywriter.proxywriter

    _writer = None
    writer = property(operator.attrgetter('_writer'))

    _uri = None
    uri = property(operator.attrgetter('_uri'))

    _parameters = None
    get_parameters = operator.attrgetter('_parameters')
    def set_parameters(self, parameters,
                       outputparameters=outputparameters.outputparameters):
        writer = self._writer
        if not writer:
            writer = self._writer = self.writer_factory(parameters, self._stream)
        else:
            writer.output_parameters.update(parameters)
        self._parameters = writer.output_parameters
    parameters = property(get_parameters, set_parameters)
    del get_parameters, set_parameters

    def __init__(self, uri=None):
        self._uri = uri


class streamresult(result):

    _stream = None
    stream = property(operator.attrgetter('_stream'))

    def __init__(self, stream, uri=None):
        self._stream = stream
        self._uri = uri


class stringresult(str, result):

    def __new__(cls, uri=None, data=''):
        return str.__new__(cls, data)

    def __init__(self, uri=None, data=''):
        self._stream = cStringIO.StringIO()
        self._uri = uri

    def clone(self):
        data = self + self._stream.getvalue()
        copy = type(self)(self._uri, data)
        copy._writer = self._writer
        copy._parameters = self._parameters
        return copy


class treeresult(result):

    writer_factory = treewriter.treewriter
