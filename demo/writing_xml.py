#Import the basic writer class for users
from amara import writer
w = writer(indent=u"yes") #Operates in streaming mode
w.start_document()
w.start_element(u'xsa')
w.start_element(u'vendor')
#Element with simple text (#PCDATA) content
w.simple_element(u'name', content=u'Centigrade systems')
#Note writer.text(content) still works
w.simple_element(u'email', content=u"info@centigrade.bogus")
w.end_element(u'vendor')
#Element with an attribute
w.start_element(u'product', attributes={u'id': u"100\u00B0"})
#Note w.attribute(name, value, namespace=None) still works
w.simple_element(u'name', content=u"100\u00B0 Server")
#XML fragment
#w.xml_fragment('<version>1.0</version><last-release>20030401</last-release>')
#Empty element
w.simple_element(u'changes')
w.end_element(u'product')
w.end_element(u'xsa')
w.end_document()

