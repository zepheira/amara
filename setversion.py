#!/usr/bin/env python
#References:
# * http://www.xml3k.org/Amara/Developer_notes
# * http://packages.python.org/distribute/setuptools.html#specifying-your-project-s-version
# * http://www.python.org/dev/peps/pep-3001/
import sys
import warnings

#Get the current (pre-script) version setting
try:
    genv = {}
    execfile('lib/version.py', genv)
    PREVERSION = genv['version_info']
except IOError:
    warnings.warn('The lib/version.py file appears to be missing or inaccessible. Please be sure you are running from the Amara source root')
    PREVERSION = None
except KeyError:
    PREVERSION = None
#PREVERSION = genv['__version__']

#Can't use Advanced formatting because that's Python 2.6+ http://www.python.org/dev/peps/pep-3101/
#VERSION_TEMPLATE = "__version__ = '{0},{1},{2}'"
VERSION_TEMPLATE = "version_info = ('%s', '%s', '%s')\n"
GIT_DESCRIBE = 'git describe --match "v[0-9]*" HEAD'


def tuple_from_git_tag():
    import os
    from subprocess import Popen, CalledProcessError, PIPE
    p = Popen([GIT_DESCRIBE], stdout=PIPE, shell=True)
    gitid = p.communicate()[0].strip()
    return tuple(gitid[1:].split('.'))
    #return tuple('v2.0.0a5'[1:].split('.'))


def set_git_version(baseversiontuple=None):
    if not baseversiontuple:
        baseversiontuple = tuple_from_git_tag()
    if PREVERSION != baseversiontuple:
        vfile = open('lib/version.py', 'w')
        vfile.write(VERSION_TEMPLATE%baseversiontuple)
        if not QUIET_FLAG: print >> sys.stderr, 'Version number changed to', '.'.join(baseversiontuple)
        if not QUIET_FLAG: print >> sys.stderr, 'Please commit and move the corresponding version VCS tag if necessary'
    return


cmdargs = sys.argv[1:]
QUIET_FLAG = False
if '-q' in cmdargs:
    QUIET_FLAG = True
    cmdargs.remove('-q')

if not QUIET_FLAG: print >> sys.stderr, 'Previous version number', '.'.join(PREVERSION)

version = tuple(cmdargs[0].split('.')) if len(cmdargs) > 0 else None
set_git_version(version)

#General, useful info:
NOTES = '''
Short hash of current commit:

git log -1 --format=%h
or
git log -1 --format=%h HEAD

Search for tags matching a pattern

git tag -l -n "2.*"

Like above, but just get the current:

git describe --match "2.[0-9]*"
or
git describe --match "2.[0-9]*" HEAD


Another thing to look at is simplified branching for bugfix branches:

Start with a release: 3.0.8. Then, after that release, do this:

git branch bugfixes308
This will create a branch for bugfixes. Checkout the branch:

git checkout bugfixes308
Now make any bugfix changes you want.

git commit -a
Commit them, and switch back to the master branch:

git checkout master
Then pull in those changes from the other branch:

git merge bugfixes308
That way, you have a separate release-specific bugfix branch, but you're still pulling the bugfix changes into your main dev trunk.
'''

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

