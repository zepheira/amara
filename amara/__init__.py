#amara

XML_NAMESPACE = u"http://www.w3.org/XML/1998/namespace"
XMLNS_NAMESPACE = u"http://www.w3.org/2000/xmlns/"

class Error(Exception): 
    pass

class ReaderError(Error):
    pass

class XIncludeError(ReaderError):
    pass
