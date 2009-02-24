########################################################################
# test/xslt/test_attribute.py
from amara.test import test_main
from amara.test.xslt import xslt_test, xslt_error, filesource, stringsource
from amara.writers import WriterError, xmlwriter
from amara.xslt import XsltError

PREFIX_TEMPLATE = xmlwriter.xmlwriter.GENERATED_PREFIX

class test_attribute_1(xslt_test):
    """`xsl:attribute` as child of literal result element"""
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result foo="bar"/>"""


class test_attribute_2(test_attribute_1):
    """`xsl:attribute` as child of literal result element"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result foo="bar"/>"""


class test_attribute_3(test_attribute_1):
    """`xsl:attribute` with namespace"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo" namespace="http://example.com/spam">bar</xsl:attribute>
      <xsl:attribute name="y:foo" namespace="http://example.com/eggs">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result xmlns:%(prefix0)s="http://example.com/spam" xmlns:y="http://example.com/eggs" %(prefix0)s:foo="bar" y:foo="bar"/>""" % {
    'prefix0' : PREFIX_TEMPLATE % 0}


class test_attribute_4(test_attribute_1):
    """adding attributes with the same expanded-name"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0"?>
<result foo="maz"/>"""


class test_attribute_5(test_attribute_1):
    """adding attributes with the same expanded-name"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result foo="bar">
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo">baz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result foo="baz"/>"""


class test_attribute_6(test_attribute_1):
    """adding attributes with the same expanded-name"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0"?>
<result foo="baz"/>"""


class test_attribute_7(test_attribute_1):
    """adding attributes with the same expanded-name"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo" namespace="http://some-ns/">bar</xsl:attribute>
      <xsl:attribute name="x:foo" xmlns:x="http://some-ns/">baz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result xmlns:org.4suite.4xslt.ns0="http://some-ns/" org.4suite.4xslt.ns0:foo="baz"/>"""


class test_attribute_8(test_attribute_1):
    """adding attributes with the same expanded-name"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result x:foo="bar" xmlns:x="http://some-ns/">
      <!-- duplicate attrs override previous -->
      <xsl:attribute name="foo" namespace="http://some-ns/">baz</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result xmlns:x="http://some-ns/" x:foo="baz"/>"""


class test_attribute_9(test_attribute_1):
    """serialization of linefeed in attribute value"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- linefeed must be serialized as &#10; -->
      <xsl:attribute name="a">x
y</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result a="x&#10;y"/>"""


class test_attribute_10(test_attribute_1):
    """substitution of xmlns prefix in attribute name"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <result>
      <!-- if an attribute prefix would be xmlns, it must be changed to something else -->
      <xsl:attribute name="xmlns:foo" namespace="http://example.com/">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version="1.0"?>
<result xmlns:%(prefix0)s="http://example.com/" %(prefix0)s:foo="bar"/>""" % {
    'prefix0': PREFIX_TEMPLATE % 0}


class test_attribute_11(test_attribute_1):
    """attributes in various namespaces"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0"?>
<result xmlns:pre="http://ns-for-pre/" xmlns:%(prefix0)s="http://foo-ns/" xmlns:%(prefix1)s="http://explicit-ns/" %(prefix1)s:bar="local-name bar, namespace http://explicit-ns/, generated prefix" foo="local-name foo, no namespace, no prefix" in-empty-ns="local-name in-empty-ns, no namespace, no prefix" pre:foo="local-name foo, namespace http://ns-for-pre/, preferred prefix pre" %(prefix0)s:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, generated prefix"/>""" % {'prefix0': PREFIX_TEMPLATE % 0,
                          'prefix1': PREFIX_TEMPLATE % 1}


class test_attribute_12(test_attribute_1):
    """attributes in empty and in-scope default namespaces"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    expected = """<?xml version="1.0"?>
<result xmlns="http://foo-ns/" xmlns:%(prefix0)s="http://foo-ns/" foo="local-name foo, no namespace, no prefix" in-empty-ns="local-name in-empty-ns, no namespace, no prefix" %(prefix0)s:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, generated prefix"/>""" % {
    'prefix0': PREFIX_TEMPLATE % 0}


class test_attribute_13(test_attribute_1):
    """attributes in empty and in-scope non-default namespaces"""
    transform = stringsource("""<?xml version="1.0"?>
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
""")
    # it's technically OK for the in-foo-ns attr to have a
    # generated prefix, but it really should re-use the foo.
    expected = """<?xml version="1.0"?>
<foo:result xmlns:foo="http://foo-ns/" foo="local-name foo, no namespace, no prefix" in-empty-ns="local-name in-empty-ns, no namespace, no prefix" foo:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, prefix foo"/>"""


class test_attribute_14(test_attribute_1):
    """attributes using in-scope namespaces and duplicate prefixes"""
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <!-- element should be in http://foo-ns/ namespace, retaining prefix foo -->
    <pre:result xmlns:pre="http://foo-ns/">
      <xsl:attribute name="in-foo-ns" namespace="http://foo-ns/">local-name in-foo-ns, namespace http://foo-ns/, prefix pre</xsl:attribute>
      <xsl:attribute name="pre:bar" xmlns:pre="http://ns-for-pre/" namespace="http://explicit-ns/">local-name bar, namespace http://explicit-ns/, generated prefix</xsl:attribute>
    </pre:result>
  </xsl:template>
</xsl:stylesheet>
""")
    # the bar attribute must have a generated prefix.
    # it's technically OK for the in-foo-ns attr to have a
    # generated prefix, but it really should re-use the pre.
    expected = """<?xml version="1.0"?>
<pre:result xmlns:pre="http://foo-ns/" xmlns:%(prefix0)s="http://explicit-ns/" pre:in-foo-ns="local-name in-foo-ns, namespace http://foo-ns/, prefix pre" %(prefix0)s:bar="local-name bar, namespace http://explicit-ns/, generated prefix"/>""" % {'prefix0': PREFIX_TEMPLATE % 0}


class test_attribute_error_1(xslt_error):
    """adding attribute ater non-attributes"""
    error_class = WriterError
    error_code = WriterError.ATTRIBUTE_ADDED_TOO_LATE
    recoverable = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:text>Hello World</xsl:text>
      <xsl:attribute name="foo">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")


class test_attribute_error_2(xslt_error):
    """adding attribute to non-element"""
    error_class = WriterError
    error_code = WriterError.ATTRIBUTE_ADDED_TO_NON_ELEMENT
    recoverable = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <xsl:attribute name="foo">bar</xsl:attribute>
  </xsl:template>
</xsl:stylesheet>
""")


class test_attribute_error_3(xslt_error):
    """creating non-text during xsl:attribute instantiation"""
    error_code = XsltError.NONTEXT_IN_ATTRIBUTE
    recoverable = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <xsl:attribute name="foo">
      <xsl:comment>no-no</xsl:comment>
    </xsl:attribute>
  </xsl:template>
</xsl:stylesheet>
""")


class test_attribute_error_4(xslt_error):
    """illegal attribute name ("xmlns")"""
    error_code = XsltError.BAD_ATTRIBUTE_NAME
    recoverable = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="xmlns">http://example.com/</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")


class test_attribute_error_5(xslt_error):
    """illegal attribute name (non-QName)"""
    error_code = XsltError.INVALID_QNAME_ATTR
    recoverable = True
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="#invalid">bar</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")


class test_attribute_error_6(xslt_error):
    """illegal namespace-uri"""
    error_code = XsltError.INVALID_NS_URIREF_ATTR
    recoverable = False
    source = stringsource("""<?xml version="1.0"?><dummy/>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match='/'>
    <result>
      <xsl:attribute name="foo" namespace="http://www.w3.org/XML/1998/namespace">bar</xsl:attribute>
      <xsl:attribute name="spam" namespace="http://www.w3.org/2000/xmlns/">eggs</xsl:attribute>
    </result>
  </xsl:template>
</xsl:stylesheet>
""")


if __name__ == '__main__':
    test_main()
