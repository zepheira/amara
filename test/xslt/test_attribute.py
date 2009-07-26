########################################################################
# test/xslt/test_attribute.py
from amara.writers import WriterError, xmlwriter
from amara.xslt import XsltError

PREFIX_TEMPLATE = xmlwriter.xmlwriter.GENERATED_PREFIX

from xslt_support import _run_xml

SOURCE_XML = """<?xml version="1.0"?><dummy/>"""

def test_attribute_1():
    """`xsl:attribute` as child of literal result element"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result foo="bar"/>""")


def test_attribute_2():
    """`xsl:attribute` as child of literal result element"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result foo="bar"/>""")

def test_attribute_3():
    """`xsl:attribute` with namespace"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo" namespace="http://example.com/spam">bar</xsl:attribute>
      <xsl:attribute name="y:foo" namespace="http://example.com/eggs">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result xmlns:%(prefix0)s="http://example.com/spam" xmlns:y="http://example.com/eggs" %(prefix0)s:foo="bar" y:foo="bar"/>""" % {
    'prefix0' : PREFIX_TEMPLATE % 0})


def test_attribute_4():
    """adding attributes with the same expanded-name"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo">bar</xsl:attribute>
      <xsl:attribute name="foo">baz</xsl:attribute>
      <xsl:attribute name="foo">maz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result foo="maz"/>""")

def test_attribute_5():
    """adding attributes with the same expanded-name"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result foo="bar">
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo">baz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result foo="baz"/>""")

def test_attribute_6():
    """adding attributes with the same expanded-name"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <xsl:attribute name="foo">bar</xsl:attribute>
      <!-- duplicate attrs override previous -->
      <!-- we use xsl:if to obscure it a bit -->
      <xsl:if test="true()">
        <xsl:attribute name="foo">baz</xsl:attribute>
      </xsl:if>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result foo="baz"/>"""
        )


def test_attribute_7():
    """adding attributes with the same expanded-name"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo" namespace="http://some-ns/">bar</xsl:attribute>
      <xsl:attribute name="x:foo" xmlns:x="http://some-ns/">baz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result xmlns:org.4suite.4xslt.ns0="http://some-ns/" org.4suite.4xslt.ns0:foo="baz"/>"""
        )

def test_attribute_8():
    """adding attributes with the same expanded-name"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result x:foo="bar" xmlns:x="http://some-ns/">
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo" namespace="http://some-ns/">baz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result xmlns:x="http://some-ns/" x:foo="baz"/>"""
        )

def test_attribute_9():
    """serialization of linefeed in attribute value"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- linefeed must be serialized as &#10; -->
      <xsl:attribute name="a">x
y</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result a="x&#10;y"/>"""
        )

def test_attribute_10():
    """substitution of xmlns prefix in attribute name"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- if an attribute prefix would be xmlns, it must be changed to something else -->
      <xsl:attribute name="xmlns:foo" namespace="http://example.com/">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result xmlns:%(prefix0)s="http://example.com/" %(prefix0)s:foo="bar"/>""" % {
            'prefix0': PREFIX_TEMPLATE % 0}
        )

def test_attribute_11():
    """attributes in various namespaces"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- correct results are indicated in the attribute values -->
      <xsl:attribute name="foo">local-name foo, no namespace, no prefix</xsl:attribute>
      <xsl:attribute name="in-empty-ns" namespace="">local-name in-empty-ns, no namespace, no prefix</xsl:attribute>
      <xsl:attribute name="in-foo-ns" namespace="http://foo-ns/">local-name in-foo-ns, namespace http://foo-ns/, generated prefix</xsl:attribute>
      <xsl:attribute name="pre:foo" xmlns:pre="http://ns-for-pre/">local-name foo, namespace http://ns-for-pre/, preferred prefix pre</xsl:attribute>
      <xsl:attribute name="pre:bar" xmlns:pre="http://ns-for-pre/" namespace="http://explicit-ns/">local-name bar, namespace http://explicit-ns/, generated prefix</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result xmlns:pre="http://ns-for-pre/" xmlns:%(prefix0)s="http://foo-ns/" xmlns:%(prefix1)s="http://explicit-ns/" %(prefix1)s:bar="local-name bar, namespace http://explicit-ns/, generated prefix" foo="local-name foo, no namespace, no prefix" in-empty-ns="local-name in-empty-ns, no namespace, no prefix" pre:foo="local-name foo, namespace http://ns-for-pre/, preferred prefix pre" %(prefix0)s:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, generated prefix"/>""" % {'prefix0': PREFIX_TEMPLATE % 0,
                          'prefix1': PREFIX_TEMPLATE % 1}
        )

def test_attribute_12():
    """attributes in empty and in-scope default namespaces"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <!-- the element should be in the http://foo-ns/ namespace. -->
    <!-- the element *may*, but most likely won't, bear the same generated prefix as the in-foo-ns attribute. -->
    <result xmlns="http://foo-ns/">
      <!-- A default namespace is in scope, but this does not affect the value of 'name' in xsl:attribute. -->
      <!-- in-foo-ns attribute does not inherit the default namespace. It *must* have a prefix, bound to http://foo-ns/ -->
      <xsl:attribute name="foo">local-name foo, no namespace, no prefix</xsl:attribute>
      <xsl:attribute name="in-empty-ns" namespace="">local-name in-empty-ns, no namespace, no prefix</xsl:attribute>
      <xsl:attribute name="in-foo-ns" namespace="http://foo-ns/">local-name in-foo-ns, namespace http://foo-ns/, generated prefix</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<result xmlns="http://foo-ns/" xmlns:%(prefix0)s="http://foo-ns/" foo="local-name foo, no namespace, no prefix" in-empty-ns="local-name in-empty-ns, no namespace, no prefix" %(prefix0)s:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, generated prefix"/>""" % {
    'prefix0': PREFIX_TEMPLATE % 0}
        )


def test_attribute_13():
    """attributes in empty and in-scope non-default namespaces"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <!-- element should be in http://foo-ns/ namespace, retaining prefix foo -->
    <foo:result xmlns:foo="http://foo-ns/">
      <xsl:attribute name="foo">local-name foo, no namespace, no prefix</xsl:attribute>
      <xsl:attribute name="in-empty-ns" namespace="">local-name in-empty-ns, no namespace, no prefix</xsl:attribute>
      <xsl:attribute name="in-foo-ns" namespace="http://foo-ns/">local-name in-foo-ns, namespace http://foo-ns/, prefix foo</xsl:attribute>
    </foo:result>
  </xsl:template>
</xsl:stylesheet>
""",
        # it's technically OK for the in-foo-ns attr to have a
        # generated prefix, but it really should re-use the foo.
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<foo:result xmlns:foo="http://foo-ns/" foo="local-name foo, no namespace, no prefix" in-empty-ns="local-name in-empty-ns, no namespace, no prefix" foo:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, prefix foo"/>"""
        )

def test_attribute_14():
    """attributes using in-scope namespaces and duplicate prefixes"""
    _run_xml(
        source_xml = SOURCE_XML,
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <!-- element should be in http://foo-ns/ namespace, retaining prefix foo -->
    <pre:result xmlns:pre="http://foo-ns/">
      <xsl:attribute name="in-foo-ns" namespace="http://foo-ns/">local-name in-foo-ns, namespace http://foo-ns/, prefix pre</xsl:attribute>
      <xsl:attribute name="pre:bar" xmlns:pre="http://ns-for-pre/" namespace="http://explicit-ns/">local-name bar, namespace http://explicit-ns/, generated prefix</xsl:attribute>
    </pre:result>
  </xsl:template>
</xsl:stylesheet>
""",
        # the bar attribute must have a generated prefix.
        # it's technically OK for the in-foo-ns attr to have a
        # generated prefix, but it really should re-use the pre.
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<pre:result xmlns:pre="http://foo-ns/" xmlns:%(prefix0)s="http://explicit-ns/" pre:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, prefix pre" %(prefix0)s:bar="local-name bar, namespace http://explicit-ns/, generated prefix"/>""" % {'prefix0': PREFIX_TEMPLATE % 0}
        )

def test_attribute_error_1():
    """adding attribute ater non-attributes"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:text>Hello World</xsl:text>
      <xsl:attribute name="foo">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except WriterError, err:
        assert err.code == WriterError.ATTRIBUTE_ADDED_TOO_LATE
    else:
        raise AssertionError("should have failed!")


def test_attribute_error_2():
    """adding attribute to non-element"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <xsl:attribute name="foo">bar</xsl:attribute>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except WriterError, err:
        assert err.code == WriterError.ATTRIBUTE_ADDED_TO_NON_ELEMENT
    else:
        raise AssertionError("should have failed!")


def test_attribute_error_3():
    """creating non-text during xsl:attribute instantiation"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <xsl:attribute name="foo">
      <xsl:comment>no-no</xsl:comment>
    </xsl:attribute>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.NONTEXT_IN_ATTRIBUTE
    else:
        raise AssertionError("should have failed!")

def test_attribute_error_4():
    """illegal attribute name ("xmlns")"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="xmlns">http://example.com/</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.BAD_ATTRIBUTE_NAME
    else:
        raise AssertionError("should have failed!")

def test_attribute_error_5():
    """illegal attribute name (non-QName)"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="#invalid">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.INVALID_QNAME_ATTR
    else:
        raise AssertionError("should have failed!")

def test_attribute_error_6():
    """illegal namespace-uri"""
    try:
        _run_xml(
            source_xml = """<?xml version="1.0"?><dummy/>""",
            transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo" namespace="http://www.w3.org/XML/1998/namespace">bar</xsl:attribute>
      <xsl:attribute name="spam" namespace="http://www.w3.org/2000/xmlns/">eggs</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""",
            expected = None)
    except XsltError, err:
        assert err.code == XsltError.INVALID_NS_URIREF_ATTR
    else:
        raise AssertionError("should have failed!")

if __name__ == '__main__':
    raise SystemExit("use nosetests")
