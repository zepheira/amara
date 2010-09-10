__version__ = '2.0a5'

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


