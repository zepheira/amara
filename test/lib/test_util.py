import unittest

import amara
from amara.lib import util

class Test_trim_word_count(unittest.TestCase):
    'Testing amara.lib.util.trim_word_count'
    def test_flat_doc(self):
        'Input doc with just top-level text'
        x = amara.parse('<a>one two three four five six seven eight nine</a>')
        for i in range(1, 11):
            trimmed_tree = util.trim_word_count(x, i)
            word_count = len(trimmed_tree.xml_select(u'string(.)').split())
            self.assertEquals(word_count, min(i, 9))

    def test_nested_doc(self):
        'Input doc with text in nested elements'
        x = amara.parse('<a>one two <b>three four </b><c>five <d>six seven</d> eight</c> nine</a>')
        for i in range(1, 11):
            trimmed_tree = util.trim_word_count(x, i)
            word_count = len(trimmed_tree.xml_select(u'string(.)').split())
            self.assertEquals(word_count, min(i, 9))


if __name__ == '__main__':
    raise SystemExit("Use nosetests (nosetests path/to/test/file)")


