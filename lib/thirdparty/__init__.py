#amara.thirdparty

#XXX: A good discussion of perf of JSON libs: https://convore.com/python/faster-json-library/

try:
    #XXX Maybe better to explicitly check for Python 2.6?
    import json
except ImportError, e:
#except ImportError as e: #Python 2.6+ only
    try:
        import simplejson as json
    except ImportError:
        try:
            from django.utils import simplejson as json
        except ImportError:
            #No json library found
            class json_dummy(object):
                def __str__():
                    return "Stand-in for missing JSON library.  Use Python 2.6 or install simplejson"
            json = json_dummy()

