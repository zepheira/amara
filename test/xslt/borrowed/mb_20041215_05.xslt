<?xml version="1.0" encoding="us-ascii"?>
<zz:KeyDump xmlns:zz="http://xmlns.4suite.org/reserved">
  <zz:Key name="bar">
    <zz:MatchSet value="sometextmoretext">
      <z:foo xmlns:z="planetz" a="b">sometext<bar>moretext</bar>
      </z:foo>
    </zz:MatchSet>
  </zz:Key>
  <zz:Key name="foo">
    <zz:MatchSet value="sometextmoretext">
      <z:foo xmlns:z="planetz" a="b">sometext<bar>moretext</bar>
      </z:foo>
    </zz:MatchSet>
    <zz:MatchSet value="sometext">sometext</zz:MatchSet>
    <zz:MatchSet value="moretext">
      <bar xmlns:z="planetz">moretext</bar>moretext</zz:MatchSet>
  </zz:Key>
</zz:KeyDump>