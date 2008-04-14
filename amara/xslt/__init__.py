#amara.xslt

def paramvalue(obj):
    """
    Try to convert a Python object into an XPath data model value
    
    returns the value if successful, else None
    """
    if isinstance(obj, unicode):
        return obj
    elif isinstance(obj, str):
        try:
            return obj.decode('utf-8')
        except UnicodeError:
            return None
    elif (isinstance(obj, int) or isinstance(obj, long)
          or isinstance(obj, float)):
        return obj
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, list) or isinstance(obj, tuple):
        #NOTE: At one time (WSGI.xml days) it attemped to be smart and handle all iterables
        #But this would mean blindly dealing with dangerous creatures, such as sockets
        #So now it's more conservative
        obj = [ paramvalue(o) for o in obj ]
        #We can only use the list if all of its members are scalars that are not None
        if [ o for o in obj if obj is None or (isinstance(obj, list) or isinstance(obj, tuple)) ]:
            return None
        else:
            return obj
    else:
        return None


def parameterize(inputdict, defaultns=None):
    """
    Convert a dictionary of name to object mappings into a dict of parameters suitable for
    passing into an XSLT transform
    
    inputdict - input mapping of name (string or tuple) to values
    
    defaultns - the namespace to use for parameter names given as string/unicode rather than tuple
    
    return the resulting param dict if successful.  If inputdict cannot completely be converted, return None
    """
    resultdict = {}
    for key in inputdict:
        value = paramvalue(inputdict[key])
        if value is None: return None
        if isinstance(key, basestring):
            if isinstance(key, str): key = key.decode('utf-8')
            if defaultns:
                resultdict[(defaultns, key)] = value
            else:
                resultdict[key] = value
        elif isinstance(key, list) or isinstance(key, tuple):
            resultdict[key] = value
        else:
            return None

    return resultdict

