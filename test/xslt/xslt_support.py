from amara.xslt.processor import processor
from amara.lib import inputsource, treecompare
from amara.xpath import util

def _run(source_xml, transform_xml, expected, parameters,
         compare_method, source_uri=None, transform_uri=None,
         processor_kwargs={}):
    P = processor(**processor_kwargs)
    source = inputsource(source_xml, source_uri)
    transform = inputsource(transform_xml, transform_uri)
    P.append_transform(transform)
    if parameters is not None:
        parameters = util.parameterize(parameters)
    result = str(P.run(source, parameters=parameters))
    try:
        diff = compare_method(result, expected)
        diff = list(diff)
        assert not diff, (source_xml, transform_xml, result, expected, diff)
    except Exception, err:
        # I don't have a quick way to tell which string caused
        # the error, so let the person debugging figure it out.
        print "=== RESULT ==="
        print result
        print "=== EXPECTED ==="
        print expected
        print "=== DONE ==="
        raise

def _run_html(source_xml, transform_xml, expected, parameters=None,
              source_uri=None, transform_uri=None,
              processor_kwargs={}):
    _run(source_xml, transform_xml, expected, parameters,
         treecompare.html_diff, source_uri, transform_uri,
         processor_kwargs)

def _run_xml(source_xml, transform_xml, expected, parameters=None,
              source_uri=None, transform_uri=None,
             processor_kwargs={}):
    _run(source_xml, transform_xml, expected, parameters,
         treecompare.xml_diff, source_uri, transform_uri,
         processor_kwargs)

def _compare_text(s1, s2):
    if s1 == s2:
        return []
    i = 0
    for i in range(min(len(s1), len(s2))):
        if s1[i] != s2[i]:
            prefix = s1[:i]
            break
    else:
        prefix = s1
        i += 1
    lineno = prefix.count("\n")+1
    line_start = prefix.rfind("\n")+1
    s1_rest = s1[i:i+20]
    s2_rest = s2[i:i+20]
    return ["Difference at line %d col %d" % (lineno, i-line_start+1),
            "prefix: %r" % (s1[line_start:i],),
            "s1 continues: %r" % (s1_rest,),
            "s2 continues: %r" % (s2_rest,),]

def _run_text(source_xml, transform_xml, expected, parameters=None,
              source_uri=None, transform_uri=None):
    _run(source_xml, transform_xml, expected, parameters,
         _compare_text, source_uri, transform_uri)
