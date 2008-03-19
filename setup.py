#!/usr/bin/env python
import os
kw = {
      #'install_requires': ['python-dateutil'],
      'license': 'Apache Software License',
      'download_url': 'ftp://ftp.4suite.org/pub/Amara/',
      'license_file': 'COPYING',
      }

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
      packages=['amara'],
      **kw)

