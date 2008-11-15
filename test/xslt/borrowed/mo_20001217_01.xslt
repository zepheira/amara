<?xml version='1.0'?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method='text'/>

  <xsl:template match='/'>
    <xsl:call-template name='charcount'>
      <xsl:with-param name='node' select='.'/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name='charcount'>
    <xsl:param name='node'/>
    <xsl:call-template name='chars-in-text'>
      <xsl:with-param name='texts' select='$node//text()'/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name='chars-in-text'>
    <xsl:param name='texts'/>
    <xsl:param name='num-chars' select='0'/>
    <xsl:choose>
      <xsl:when test='count($texts) > 0'>
        <xsl:variable name='cur-count'>
          <xsl:call-template name='count-chars'>
            <xsl:with-param name='string' select='$texts[1]'/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:call-template name='chars-in-text'>
          <xsl:with-param name='texts' select='$texts[position() > 1]'/>
          <xsl:with-param name='num-chars' select='$num-chars + $cur-count'/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select='$num-chars'/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name='count-chars'>
    <xsl:param name='string'/>
    <xsl:param name='cur-pos' select='1'/>
    <xsl:param name='non-ns-chars' select='0'/>
    <xsl:choose>
      <xsl:when test='$cur-pos &lt;= string-length($string)'>
        <xsl:variable name='cur-char' select='substring($string,$cur-pos,1)'/>
        <xsl:variable name='new-count'>
          <xsl:choose>
            <xsl:when test="$cur-char = ' '">0</xsl:when>
            <xsl:when test="$cur-char = '&#10;'">0</xsl:when>
            <xsl:otherwise>1</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:call-template name='count-chars'>
          <xsl:with-param name='string' select='$string'/>
          <xsl:with-param name='cur-pos' select='$cur-pos + 1'/>
          <xsl:with-param name='non-ns-chars' select='$non-ns-chars + $new-count'/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select='$non-ns-chars'/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
            
</xsl:stylesheet>
