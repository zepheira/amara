#!/bin/bash
#e.g. setversionwrapper.sh 2.0.0a1
./setversion.py -q $1
git add lib/version.py
git commit -m "Bumping version to $1"
git tag -af $1 -m "Tagging as $1"
echo "Don't forget to git push; git push --tags when ready"

# Check for proper number of command line args.

#EXPECTED_ARGS=1
#E_BADARGS=65

#if [ $# -ne $EXPECTED_ARGS ]
#then
#  echo "Usage: `basename $0` {arg}"
#  exit $E_BADARGS
#fi
