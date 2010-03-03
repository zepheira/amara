#!/usr/bin/env python
from amara.xpath import context
from amara.xpath.expressions.booleans import and_expr, or_expr



PLACES = """<places>
    <place name="Santiago, Regi\xc3\xb3n Metro De Santiago"/>
    <place name="London"/>
</places>
"""

def test_simple_attr_update3():
    import amara
    doc = amara.parse(PLACES)
    ns = doc.xml_select(u'/places/place[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'/places/*[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'/*/place[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'/*/*[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'places/place[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'places/*[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'*/place[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    ns = doc.xml_select(u'*/*[@name="Santiago, Regi\xf3n Metro De Santiago"]')
    assert len(ns) == 1, (len(ns), 1)
    return

#XXX The rest are in old unittest style.  Probably best to add new test cases above in nose test style

from test_expressions import (
    # boolean literals
    TRUE, FALSE,
    # IEEE 754 "special" numbers as expressions
    NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY,
    # nodeset literals
    nodeset_literal, ROOT
    )

from amara.xpath.locationpaths.predicates import predicate

def test_predicate():
    ctx = context(ROOT, 1, 1)
    for args, expected in (
        # FIXME: test literal optimization
        # FIXME: test `position() = Expr` optimization
        # FIXME: test `position() [>,>=] Expr` optimization
        # FIXME: test `Expr [<,<=] position()` optimization
        # FIXME: test numeric-type expression
        # test boolean-type expression
        (and_expr(TRUE, 'and', FALSE), []),
        (or_expr(TRUE, 'or', FALSE), [ROOT]),
        # FIXME: test object-type expression
        ):
        result = predicate(args).select(ctx, [ROOT])
        result = list(result)
        assert result == expected, (result, expected)

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
