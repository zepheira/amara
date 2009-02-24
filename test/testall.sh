#!/bin/sh
#./bindery/test_basics.py \
#./tree/test_gc.py \
EXCLUSIONS="\
./bindery/test_performance.py \
"

echo $EXCLUSIONS

for test in `find . -name "test_*.py"`; do
    echo $EXCLUSIONS | grep $test > /dev/null 2>&1
    if [ "$?" -eq "0" ]; then
        echo "Skipped " $test;
    else
        echo $test;
        python $test $* ;
    fi
done
#Can't figure out a way to add echo to this version.  The -i supports the {}
#ls -1 *.py | xargs -i python {}
