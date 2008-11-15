#!/bin/sh
for test in `find . -name "test_*.py"`; do
  echo $test;
  python $test $* ;
done
#Can't figure out a way to add echo to this version.  The -i supports the {}
#ls -1 *.py | xargs -i python {}
