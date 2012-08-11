# -*- coding: utf-8 -*-

'''
Tests about comparing attributes with or / and connectors

It has to do with this ticket: https://github.com/zepheira/amara/issues/8

@lmorillas
'''

import amara

XML = '''<?xml version="1.0" encoding="utf-8"?>
<school>
<teacher lang="es" date="1998">
    <name>Luis</name>
</teacher>
<student date="1990">
    <name>María</name>
</student>
<student lang="es" date="1992">
    <name>Jesús</name>
</student>
<student lang="en" date="2002">
    <name>Peter</name>
</student>
<student lang="es" date="2001">
    <name>Mary</name>
</student>
<student lang="en ni">
    <name>Uche</name>
</student>
<student>
    <name>Anonymous</name>
</student>

</school>
'''


doc = amara.parse(XML)

# Testing attributes

def test_or_attributes_exist():
    assert len(doc.xml_select(u'//student[@lang or @date]')) == 5

def test_or_attributes_equal():
    assert len(doc.xml_select(u'//student[@lang="en" or @lang="es"]')) == 3

def test_or_attributes_gt_integer():
    # compares as integer
    assert len(doc.xml_select(u'//student[@lang="es" or @date>2000]')) == 5

def test_and_attributes_exist():
    assert len(doc.xml_select(u'//student[@lang and @date]')) == 3

def test_and_attributes_equal():
    assert len(doc.xml_select(u'//student[@lang="en" and @date>2000]')) == 1

# tests with elements
def test_or_nodes():
    assert len(doc.xml_select(u'//student  | //teacher')) == 7



if __name__ == '__main__':
    raise SystemExit('Use nosetests')
