#!/usr/bin/env python
import sys

execfile('lib/version.py')

try:
    hgversionstamp()
except (KeyboardInterrupt, SystemExit):
    raise
except Exception, e:
#except Exception as e: #Python 2.6+ only
    print >> sys.stderr, 'Error trying to tag with HG revision:', repr(e)
    pass


