#!/usr/bin/env python
import sys

#Get the current (pre-script) version setting
genv = {}
execfile('lib/version.py', genv)
preversion = genv['__version__']

#Can't use Advanced formatting because that's Python 2.6+ http://www.python.org/dev/peps/pep-3101/
#VERSION_TEMPLATE = "__version__ = '{0}'"
VERSION_TEMPLATE = "__version__ = '%s'\n"


def get_git_tag():
	return '2.0a5'

def set_git_version(baseversion=None):
	if not baseversion:
		baseversion = get_git_tag()
	vfile = open('lib/version.py', 'w')
	vfile.write(VERSION_TEMPLATE%baseversion)
	return


#----- No longer used stuff follows -----

#try:
#    hgversionstamp()
#except (KeyboardInterrupt, SystemExit):
#    raise
#except Exception, e:
##except Exception as e: #Python 2.6+ only
#    print >> sys.stderr, 'Error trying to tag with HG revision:', repr(e)
#    pass

#

def hgversionstamp():
    #Note: check_call is Python 2.6 or later
    #python -c "from subprocess import *; check_call(['hg -q id'], shell=True)"
    import os
    from subprocess import Popen, CalledProcessError, PIPE
    #raise RuntimeError('Foo Bar') #Just to test handling failure
    #check_call(['hg -q id'], shell=True)
    p = Popen(['hg -q id'], stdout=PIPE, shell=True)
    hgid = p.communicate()[0].strip()
    hgid_file = os.path.join('lib', '__hgid__.py')
    open(hgid_file, 'w').write('HGID = \'%s\'\n'%hgid)
    print >> sys.stderr, 'Setup run from a Mercurial repository, so putting the version ID,', hgid, ', in ', hgid_file

