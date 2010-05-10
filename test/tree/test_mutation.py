# Testing new amara.tree API

import copy

import amara
from amara import parse, tree
from amara.lib import treecompare


XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

ATTRIBUTE_NODE = tree.attribute.xml_type

BOGUS_X_NS = u"urn:bogus:x"

def test_attr_setnode1():
    EXPECTED = """<a x="1"/>"""
    doc = parse('<a x="1"/>')
    doc2 = parse('<a/>')
    #x = doc.xml_first_child.xml_attributes[None, u'x']
    attr_x = doc.xml_first_child.xml_attributes.getnode(None, u'x')
    #doc.xml_first_child.xml_attributes[None, u'y'] = attr_x
    doc2.xml_first_child.xml_attributes.setnode(attr_x)
    treecompare.check_xml(doc2.xml_encode(), XMLDECL+EXPECTED)
    return

def test_attr_setnode2():
    EXPECTED = """<a x="1" y="1" z=""/>"""
    doc = parse('<a x="1"/>')
    attr_y = tree.attribute(None, u'y', u'1')
    doc.xml_first_child.xml_attributes.setnode(attr_y)
    attr_z = tree.attribute(None, u'z')
    doc.xml_first_child.xml_attributes.setnode(attr_z)
    treecompare.check_xml(doc.xml_encode(), XMLDECL+EXPECTED)
    return

def test_attr_setnode3():
    EXPECTED = """<a x="1"/>"""
    doc = parse('<a x="1"/>')
    #x = doc.xml_first_child.xml_attributes[None, u'x']
    attr_x = copy.copy(doc.xml_first_child.xml_attributes.getnode(None, u'x'))
    del doc.xml_first_child.xml_attributes[None, u'x']
    doc.xml_first_child.xml_attributes.setnode(attr_x)
    treecompare.check_xml(doc.xml_encode(), XMLDECL+EXPECTED)
    return

def test_attr_setnode4():
    EXPECTED = """<a xmlns:ns="urn:bogus:x" ns:x="1"/>"""
    doc = parse('<a xmlns:ns="urn:bogus:x" ns:x="1"/>')
    doc2 = parse('<a xmlns:ns="urn:bogus:x"/>')
    attr_x = doc.xml_first_child.xml_attributes.getnode(BOGUS_X_NS, u'x')
    doc2.xml_first_child.xml_attributes.setnode(attr_x)
    treecompare.check_xml(doc2.xml_encode(), XMLDECL+EXPECTED)
    return

def test_attr_setnode5():
    EXPECTED = """<a xmlns:ns="urn:bogus:x" ns:x="1" ns:y="1" ns:z=""/>"""
    doc = parse('<a xmlns:ns="urn:bogus:x" ns:x="1"/>')
    attr_y = tree.attribute(BOGUS_X_NS, u'ns:y', u'1')
    doc.xml_first_child.xml_attributes.setnode(attr_y)
    attr_z = tree.attribute(BOGUS_X_NS, u'ns:z')
    doc.xml_first_child.xml_attributes.setnode(attr_z)
    treecompare.check_xml(doc.xml_encode(), XMLDECL+EXPECTED)
    return

def test_simpe_attr_update2():
    EXPECTED = """<a x="2"/>"""
    doc = parse('<a x="1"/>')
    attr_x = doc.xml_first_child.xml_attributes[None, u'x'] = u'2'
    treecompare.check_xml(doc.xml_encode(), XMLDECL+EXPECTED)
    return

def test_simpe_attr_update3():
    EXPECTED = """<a xmlns:ns="urn:bogus:x" ns:x="2"/>"""
    doc = parse('<a xmlns:ns="urn:bogus:x" ns:x="1"/>')
    attr_x = doc.xml_first_child.xml_attributes[BOGUS_X_NS, u'x'] = u'2'
    treecompare.check_xml(doc.xml_encode(), XMLDECL+EXPECTED)
    return

def test_delns1():
    EXPECTED = """<a/>"""
    doc = parse('<a xmlns:ns="urn:bogus:x"/>')
    del doc.xml_first_child.xml_namespaces[u'ns']
    treecompare.check_xml(doc2.xml_encode(), XMLDECL+EXPECTED)
    return


if __name__ == '__main__':
    raise SystemExit("use nosetests")

