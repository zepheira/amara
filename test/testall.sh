#!/bin/sh

# -v increases verbosity; shows the test names as they are being run
# --exe to include test_*.py programs which are executable
# -P to not tweak the PYTHONPATH to include ..
# Use "-e" to exclude tests, using a regular expression#

nosetests -v --exe -P $*

