#!/usr/bin/env python
from distutils.core import setup, Extension

# add'l setup keywords
kw = {}

setup(name='Amara',
      version='1.9.0',
      description="Library for XML processing in Python",
      long_description="Library for XML processing in Python, designed to balance the native idioms of Python with the native character of XML.",
      url='http://wiki.xml3k.org/Amara2',
      author='Amara team',
      author_email='amara-dev@googlegroups.com',
      classifiers=[
         'Development Status :: 3 - Alpha',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: Apache Software License',
         'Programming Language :: Python',
         'Topic :: Software Development :: Libraries :: Python Modules',
         'Topic :: Text Processing :: Markup :: XML',
         ],
      download_url='ftp://ftp.4suite.org/pub/Amara/',
      license='Apache Software License',
      #license_file='COPYING',
      packages=['amara',
                'amara.lib',
                'amara.xml',
                ],
      ext_modules=[
          Extension('amara.xml._expat',
                    define_macros=[('HAVE_EXPAT_CONFIG_H', None),
                                   ('Expat_BUILDING_MODULE', None),
                                   ],
                    include_dirs=['amara/xml/src', 'amara/xml/src/expat'],
                    sources=[# Expat XML parser
                             'amara/xml/src/expat/lib/xmlparse.c',
                             'amara/xml/src/expat/lib/xmlrole.c',
                             'amara/xml/src/expat/lib/xmltok.c',

                             # Miscellaneous supporting routines
                             'amara/xml/src/expat/util.c',
                             # XML_Char <-> PyUnicode
                             'amara/xml/src/expat/xmlchar.c',
                             # Optimized stack implementation
                             'amara/xml/src/expat/stack.c',
                             # XML_Char HashTable implementation
                             'amara/xml/src/expat/hash_table.c',
                             # DTD validation support
                             'amara/xml/src/expat/content_model.c',
                             # DTD validation support
                             'amara/xml/src/expat/validation.c',
                             # StateTable implementation
                             'amara/xml/src/expat/state_machine.c',

                             # basic InputSource object
                             'amara/xml/src/expat/input_source.c',
                             # Attributes object
                             'amara/xml/src/expat/attributes.c',
                             # ExpatReader object
                             'amara/xml/src/expat/reader.c',

                             # SaxFilter object
                             'amara/xml/src/expat/sax_filter.c',

                             # Module interface
                             'amara/xml/src/expat/expat.c',
                             ],
                    ),
                 ],
      #'install_requires': ['python-dateutil'],
      **kw)

