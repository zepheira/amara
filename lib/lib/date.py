'''

Example:

import datetime
from amara.lib.date import timezone, UTC
print datetime.datetime(2008, 10, 8, 19, 38, 8, 0, timezone('-0700')).isoformat()
import datetime
from amara.lib.date import timezone, UTC
print datetime.datetime(2008, 10, 8, 19, 38, 8, 0, UTC).isoformat()

If you need even more timezone mojo, try pytz: http://pypi.python.org/pypi/pytz/
'''

import datetime

# To be moved to amara lib
# Reuses some code from: http://seehuhn.de/blog/52
class timezone(datetime.tzinfo):
    def __init__(self, name="+0000"):
        self.name = name
        seconds = int(name[:-2])*3600+int(name[-2:])*60
        self.offset = datetime.timedelta(seconds=seconds)

    def utcoffset(self, dt):
        return self.offset

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return self.name


UTC = timezone()

