
import unittest

import amara
from amara.lib import util

class Test_util(unittest.TestCase):
    def test_trim_word_count(self):
        x = amara.parse('<a>one two <b>three four </b><c>five <d>six seven</d> eight</c> nine</a>')
        for i in range(1, 11):
            trimmed_tree = util.trim_word_count(x, i)
            word_count = len(trimmed_tree.xml_select(u'string(.)').split())
            self.assertEquals(word_count, min(i, 9))


if __name__ == '__main__':
    raise SystemExit("Use nosetests")


