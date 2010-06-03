#amara.thirdparty


try:
    #XXX Maybe better to explicitly chck for Python 2.6?
    import json
except ImportError as e:
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

