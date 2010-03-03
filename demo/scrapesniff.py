#!/usr/bin/env python
"""
scrapesniff.py a tool to help write Web scrapers

"""

import sys
import amara
from amara import tree
from amara.xpath import util
from amara import xml_print as xp

class waypoint(object):
    def __init__(self, node):
        self.node = node
    

class nav(object):
    def __init__(self, source, html=False):
        self.records = []
        if html:
            from amara.bindery.html import parse as htmlparse
            self.doc = htmlparse(source)
            #html5lib generates adjacent text nodes
            self.doc.xml_normalize()
        else:
            self.doc = amara.parse(source)
        self.new_record()
        self.common_ancestor = None
        self.record_pattern = None
        return

    def find(s):
        record = self.records[-1]
        expr = u'.//text()[contains(., "%s")]'%s.decode('utf-8')
        results = self.context.xml_select(expr)
        if not results:
            expr = u'.//@*[contains(., "%s")]'%s.decode('utf-8')
            results = self.context.xml_select(expr)
        wp = (results[0] if results else None)
        if wp:
            wp = waypoint(wp)
            wp.path = util.abspath(wp.node)
            if self.common_ancestor:
                while not self.common_ancestor in wp.node.xml_select('ancestor::*'):
                    self.common_ancestor = self.common_ancestor.xml_parent
            else:
                self.common_ancestor = wp.node.xml_parent
            record.append(wp)
        return

    def new_record(s):
        self.context = self.doc
        self.records.append([])

    def report():
        common_ancestor_path = util.abspath(self.common_ancestor)
        print common_ancestor_path
        common_ancestor_path_len = len(common_ancestor_path)
        for wp in self.records[0]:
            wp.path = wp.path[self.common_ancestor_path_len+1:]
            print wp.path
            print wp.node
        return

