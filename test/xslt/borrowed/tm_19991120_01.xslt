<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">
<!--
    (C) Tom Myers, 11/19/1999  tom.myers@worldnet.att.net
    use it freely, tell me if you have ideas for it.
-->
<xsl:output method="html"/>
<xsl:param name="boardsize" select="8"/>

<xsl:template match="/">

<html><head><title>N Queens</title></head>
<body>
   <h3>We will now call "queens"</h3>
to generate all solutions of the
<xsl:value-of select="$boardsize"/>-Queens problem.
   <table border="1">
   <xsl:call-template name="queens"/>
   </table>

<pre>
queens(lim,list,upd,downd,listlen)=list, if lim=listlen
  =queenstry(1,lim,list,upd,downd,listlen) otherwise

queenstry(val,lim,list,upd,downd,listlen)= "", if val<xsl:text
           disable-output-escaping="yes">&gt;</xsl:text>lim
  =addifnew(val,lim,list,upd,downd,listlen) +
     queenstry(val+1,lim,list,listlen) otherwise.

addifnew(val,lim,list,upd,downd,listlen)="",
               if val in list or udv in upd or ddv in downd
     = queens(lim,list+val+",",
              upd+udv+",",downd+ddv+",",listlen+1) otherwise.
       where udv=val+listlen, ddv=boardsize+val-listlen;
</pre>
In other words,
<p>queens(lim,list,upd,downd,listlen) assumes that "list" is
of length "listlen", with each number followed by a
comma, and the goal of queens is to add to that list
in every possible way to bring it to length "lim"
with numbers no greater than "lim" and without repeats.
</p><p>queenstry(val,lim,list,upd,downd,listlen) will try the
value "val" and all values between it and "lim" in
extending the list.
</p><p>addifnew(val,lim,list,upd,downd,listlen) does nothing
if "val" is already in the list; otherwise adds it
and goes on with "queens" of the longer list.
</p>
</body>
</html>

</xsl:template>

<xsl:template name="queens">
  <xsl:param name="lim" select="$boardsize"/>
  <xsl:param name="list" select="','"/>
  <xsl:param name="upd" select="','"/>
  <xsl:param name="dnd" select="','"/>
  <xsl:param name="listlen" select="0"/>
  <xsl:if test="$lim>$listlen">
    <xsl:call-template name="queenstry">
       <xsl:with-param name="lim" select="$lim"/>
       <xsl:with-param name="list" select="$list"/>
       <xsl:with-param name="upd" select="$upd"/>
       <xsl:with-param name="dnd" select="$dnd"/>
       <xsl:with-param name="listlen" select="$listlen"/>
    </xsl:call-template>
  </xsl:if>
  <xsl:if test="$listlen>=$lim">
    <tr>
    <xsl:call-template name="outperm">
      <xsl:with-param name="list" select="substring($list,2)"/>
    </xsl:call-template>
    </tr>
  </xsl:if>
</xsl:template>

<!--
queenstry(val,lim,list,upd,dnd,listlen)= "", if val>lim
  =addifnew(val,lim,list,upd,dnd,listlen) +
     queenstry(val+1,lim,list,upd,dnd,listlen) otherwise.
-->

<xsl:template name="queenstry">
  <xsl:param name="val" select="1"/>
  <xsl:param name="lim" select="$boardsize"/>
  <xsl:param name="list" select="','"/>
  <xsl:param name="upd" select="','"/>
  <xsl:param name="dnd" select="','"/>
  <xsl:param name="listlen" select="0"/>
  <xsl:if test="$lim>=$val" >
    <xsl:call-template name="addifnew">
       <xsl:with-param name="val" select="$val"/>
       <xsl:with-param name="lim" select="$lim"/>
       <xsl:with-param name="list" select="$list"/>
       <xsl:with-param name="upd" select="$upd"/>
       <xsl:with-param name="dnd" select="$dnd"/>
       <xsl:with-param name="listlen" select="$listlen"/>
    </xsl:call-template>
    <xsl:call-template name="queenstry">
       <xsl:with-param name="val" select="1+$val"/>
       <xsl:with-param name="lim" select="$lim"/>
       <xsl:with-param name="list" select="$list"/>
       <xsl:with-param name="upd" select="$upd"/>
       <xsl:with-param name="dnd" select="$dnd"/>
       <xsl:with-param name="listlen" select="$listlen"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<!--
addifnew(val,lim,list,listlen)="", if val in list
     = queens(lim,list+":"+val,listlen+1) otherwise.
-->
<xsl:template name="addifnew">
  <xsl:param name="val" select="1"/>
  <xsl:param name="lim" select="$boardsize"/>
  <xsl:param name="list" select="','"/>
  <xsl:param name="upd" select="','"/>
  <xsl:param name="dnd" select="','"/>
  <xsl:param name="listlen" select="0"/>
  <xsl:variable name="valcomma"
               select="concat(',',$val,',')"/>
  <xsl:variable name="valup"
               select="concat(',',($val+$listlen),',')"/>
  <xsl:variable name="valdn"
               select="concat(',',(($boardsize+$val)-$listlen),',')"/>
  <xsl:if
     test="not(contains($list,$valcomma) or contains($upd,$valup) or contains($dnd,$valdn))">
    <xsl:call-template name="queens">
       <xsl:with-param name="lim" select="$lim"/>
       <xsl:with-param name="list"
            select="concat($list,substring($valcomma,2))"/>
       <xsl:with-param name="upd"
            select="concat($upd,substring($valup,2))"/>
       <xsl:with-param name="dnd"
            select="concat($dnd,substring($valdn,2))"/>
       <xsl:with-param name="listlen" select="1+$listlen"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template name="outperm">
  <xsl:param name="list" select="''"/>
  <xsl:if test="contains($list,',')">
    <td>
     <xsl:value-of select="substring-before($list,',')"/>
    </td>
    <xsl:call-template name="outperm">
      <xsl:with-param name="list" select="substring-after($list,',')"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
