########################################################################
# test/xslt/dg_20010503.py
# Duncan Grisby <dgrisby@uk.research.att.com> reports dependence on the order of the false attributes in an xml-stylesheet PI
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_order_dependence_dg_20010503(xslt_test):
    source = stringsource("""\
<?xml version="1.0" encoding="ISO-8859-1" standalone="yes"?>
<?xml-stylesheet type="text/xml" href="Xml/Xslt/Core/addr_book1.xsl"?>
<ADDRBOOK>
    <ENTRY ID="pa">
        <NAME>Pieter Aaron</NAME>
        <ADDRESS>404 Error Way</ADDRESS>
        <PHONENUM DESC="Work">404-555-1234</PHONENUM>
        <PHONENUM DESC="Fax">404-555-4321</PHONENUM>
        <PHONENUM DESC="Pager">404-555-5555</PHONENUM>
        <EMAIL>pieter.aaron@inter.net</EMAIL>
    </ENTRY>
</ADDRBOOK>
""")
    transform = []
    expected = """<html>
  <head>
    <meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'>
    <title>Address Book</title>
  </head>
  <body>
    <h1>Tabulate Just Names and Phone Numbers</h1>
    <table>
      <tr>
        <td align='center'><b>Pieter Aaron</b></td>
        <td>(Work) 404-555-1234<br>(Fax) 404-555-4321<br>(Pager) 404-555-5555</td>
      </tr>
    </table>
  </body>
</html>"""


if __name__ == '__main__':
    test_main()
