########################################################################
# amara/namespaces.py
"""
Common namespaces, for sake of convenience
"""

COMMON_PREFIXES = {}

AKARA_NAMESPACE = u"http://purl.org/dc/org/xml3k/akara"; COMMON_PREFIXES[AKARA_NAMESPACE] = u'ak'

XML_NAMESPACE = u"http://www.w3.org/XML/1998/namespace"
XMLNS_NAMESPACE = u"http://www.w3.org/2000/xmlns/"

XHTML_NAMESPACE = u"http://www.w3.org/1999/xhtml"; COMMON_PREFIXES[XHTML_NAMESPACE] = u'xhtml'
XSL_NAMESPACE = u'http://www.w3.org/1999/XSL/Transform'; COMMON_PREFIXES[XSL_NAMESPACE] = u'xsl'

RNG_NAMESPACE = u"http://relaxng.org/ns/structure/1.0"; COMMON_PREFIXES[RNG_NAMESPACE] = u'rng'
EG_NAMESPACE = u"http://examplotron.org/0/"; COMMON_PREFIXES[EG_NAMESPACE] = u'eg'

#XML Linking Language: http://www.w3.org/TR/xlink/
XLINK_NAMESPACE = u"http://www.w3.org/1999/xlink"; COMMON_PREFIXES[XLINK_NAMESPACE] = u'xlink'
XINCLUDE_NAMESPACE = u'http://www.w3.org/2001/XInclude'; COMMON_PREFIXES[XINCLUDE_NAMESPACE] = u'xinclude'

SVG_NAMESPACE = u"http://www.w3.org/2000/svg"; COMMON_PREFIXES[SVG_NAMESPACE] = u'svg'

#RDF

RDF_NAMESPACE = u"http://www.w3.org/1999/02/22-rdf-syntax-ns#"; COMMON_PREFIXES[RDF_NAMESPACE] = u'rdf'
RDFS_NAMESPACE = u"http://www.w3.org/2000/01/rdf-schema#"; COMMON_PREFIXES[RDFS_NAMESPACE] = u'rdfs'
DC_NAMESPACE = u"http://purl.org/dc/elements/1.1/"; COMMON_PREFIXES[DC_NAMESPACE] = u'dc'
SKOS_NAMESPACE = u"http://www.w3.org/2008/05/skos#"; COMMON_PREFIXES[SKOS_NAMESPACE] = u'skos'
OWL_NAMESPACE = u"http://www.w3.org/2002/07/owl#"; COMMON_PREFIXES[OWL_NAMESPACE] = u'owl'

RDF_GROUP = [RDF_NAMESPACE, RDFS_NAMESPACE, DC_NAMESPACE, OWL_NAMESPACE, SKOS_NAMESPACE]

ATOM_NAMESPACE = u'http://www.w3.org/2005/Atom'; COMMON_PREFIXES[ATOM_NAMESPACE] = u'atom'
ATOMPUB_NAMESPACE = u'http://www.w3.org/2007/app'; COMMON_PREFIXES[ATOMPUB_NAMESPACE] = u'app'
ATOMTHR_EXT_NAMESPACE = u'http://purl.org/syndication/thread/1.0'; COMMON_PREFIXES[ATOMTHR_EXT_NAMESPACE] = u'thr'


#obsolete
EXTENSION_NAMESPACE = u'http://xmlns.4suite.org/ext'



"""
Probably out of date (from pyxml)

#DSIG, XML-Signature Syntax and Processing: http://www.w3.org/TR/xmldsig-core/

DSIG_BASE = u"http://www.w3.org/2000/09/xmldsig#" #basic namespace defined by the specification
DIGEST_SHA1 = BASE + u"sha1" #The SHA-1 digest method
DIGEST_MD2 = BASE + u"md2" #The MD2 digest method
DIGEST_MD5 = BASE + u"md5" #The MD5 digest method
SIG_DSA_SHA1 = BASE + u"dsa-sha1" #The DSA/DHA-1 signature method
SIG_RSA_SHA1 = BASE + u"rsa-sha1" #The RSA/DHA-1 signature method
HMAC_SHA1 = BASE + u"hmac-sha1" #The SHA-1 HMAC method
ENC_BASE64 = BASE + u"base64" #The Base64 encoding method
ENVELOPED = BASE + u"enveloped-signature" #an enveloped XML signature

#C14N
C14N_NAMESPACE = u"http://www.w3.org/TR/2000/CR-xml-c14n-20010315" #XML canonicalization
C14N_COMM_NAMESPACE = C14N + u"#WithComments" #XML canonicalization, retaining comments
C14N_EXCL_NAMESPACE = u"http://www.w3.org/2001/10/xml-exc-c14n#" #XML exclusive canonicalization

XPATH_NAMESPACE = u"http://www.w3.org/TR/1999/REC-xpath-19991116"
XSLT_NAMESPACE = u"http://www.w3.org/TR/1999/REC-xslt-19991116"


SOAPENV_NAMESPACE = u"http://schemas.xmlsoap.org/soap/envelope/"
SOAPENC_NAMESPACE = u"http://schemas.xmlsoap.org/soap/encoding/"

class ENCRYPTION:
    \"""ENCRYPTION, XML-Encryption Syntax and Processing

    ENCRYPTION (26-Jun-2001) is a W3C Working Draft.  It is specified in
    http://www.w3.org/TR/xmlenc-core/
        BASE -- the basic namespace defined by the specification
        BLOCK_3DES -- The triple-DES symmetric encryption method
        BLOCK_AES128 -- The 128-bit AES symmetric encryption method
        BLOCK_AES256 -- The 256-bit AES symmetric encryption method
        BLOCK_AES192 -- The 192-bit AES symmetric encryption method
        STREAM_ARCFOUR -- The ARCFOUR symmetric encryption method
        KT_RSA_1_5 -- The RSA v1.5 key transport method
        KT_RSA_OAEP -- The RSA OAEP key transport method
        KA_DH -- The Diffie-Hellman key agreement method
        WRAP_3DES -- The triple-DES symmetric key wrap method
        WRAP_AES128 -- The 128-bit AES symmetric key wrap method
        WRAP_AES256 -- The 256-bit AES symmetric key wrap method
        WRAP_AES192 -- The 192-bit AES symmetric key wrap method
        DIGEST_SHA256 -- The SHA-256 digest method
        DIGEST_SHA512 -- The SHA-512 digest method
        DIGEST_RIPEMD160 -- The RIPEMD-160 digest method
    \"""

    BASE             = "http://www.w3.org/2001/04/xmlenc#"
    BLOCK_3DES       = BASE + "des-cbc"
    BLOCK_AES128     = BASE + "aes128-cbc"
    BLOCK_AES256     = BASE + "aes256-cbc"
    BLOCK_AES192     = BASE + "aes192-cbc"
    STREAM_ARCFOUR   = BASE + "arcfour"
    KT_RSA_1_5       = BASE + "rsa-1_5"
    KT_RSA_OAEP      = BASE + "rsa-oaep-mgf1p"
    KA_DH            = BASE + "dh"
    WRAP_3DES        = BASE + "kw-3des"
    WRAP_AES128      = BASE + "kw-aes128"
    WRAP_AES256      = BASE + "kw-aes256"
    WRAP_AES192      = BASE + "kw-aes192"
    DIGEST_SHA256    = BASE + "sha256"
    DIGEST_SHA512    = BASE + "sha512"
    DIGEST_RIPEMD160 = BASE + "ripemd160"

class SCHEMA:
    \"""SCHEMA, XML Schema

    XML Schema (30-Mar-2001) is a W3C candidate recommendation.  It is
    specified in http://www.w3.org/TR/xmlschema-1 (Structures) and
    http://www.w3.org/TR/xmlschema-2 (Datatypes). Schema has been under
    development for a comparitively long time, and other standards have
    at times used earlier drafts.  This class defines the most-used, and
    sets BASE to the latest.
        BASE -- the basic namespace (2001)
        XSD1, XSI1 -- schema and schema-instance for 1999
        XSD2, XSI2 -- schema and schema-instance for October 2000
        XSD3, XSI3 -- schema and schema-instance for 2001
        XSD_LIST -- a sequence of the XSDn values
        XSI_LIST -- a sequence of the XSIn values
    \"""

    XSD1        = "http://www.w3.org/1999/XMLSchema"
    XSD2        = "http://www.w3.org/2000/10/XMLSchema"
    XSD3        = "http://www.w3.org/2001/XMLSchema"
    XSD_LIST    = [ XSD1, XSD2, XSD3 ]
    XSI1        = "http://www.w3.org/1999/XMLSchema-instance"
    XSI2        = "http://www.w3.org/2000/10/XMLSchema-instance"
    XSI3        = "http://www.w3.org/2001/XMLSchema-instance"
    XSI_LIST    = [ XSI1, XSI2, XSI3 ]
    BASE        = XSD3

class WSDL:
    \"""WSDL, Web Services Description Language

    WSDL (V1.1, 15-Mar-2001) is a W3C Note.  It is specified in
    http://www.w3.org/TR/wsdl
        BASE -- the basic namespace defined by this specification
        BIND_SOAP -- SOAP binding for WSDL
        BIND_HTTP -- HTTP GET and POST binding for WSDL
        BIND_MIME -- MIME binding for WSDL
    \"""

    BASE        = "http://schemas.xmlsoap.org/wsdl/"
    BIND_SOAP   = BASE + "soap/"
    BIND_HTTP   = BASE + "http/"
    BIND_MIME   = BASE + "mime/"


class RNG:
    \"""RELAX NG, schema language for XML

    RELAX NG (03-Dec-2001) is a simple schema languge for XML,
    published under the auspices of OASIS.  The specification, tutorial,
    and other information are available from http://www.relaxng.org.
    \"""
    BASE = "http://relaxng.org/ns/structure/1.0"

class DCMI:
    \"""Dublin Core Metadata Initiative

    The DCMI defines a commonly-used set of general metadata elements.
    There is a base set of elements, a variety of refinements of
    those, a set of value encodings, and a 'type vocabulary' used to
    describe what something described in metadata actually is (a text,
    a physical object, a collection, etc.).

    Documentation on the Dublin Core, including recommendations for
    encoding Dublin Core metadata in XML and HTML/XHTML can be found
    at http://dublincore.org/.
    \"""
    # not used directly:
    BASE = "http://purl.org/dc/"

    # the core element set:
    DCMES_1_1 = BASE + "elements/1.1/"
    DCMES = DCMES_1_1

    # standardized additions and refinements:
    TERMS = BASE + "terms/"

    # type vocabulary:
    TYPE = BASE + "dcmitype/"


"""


