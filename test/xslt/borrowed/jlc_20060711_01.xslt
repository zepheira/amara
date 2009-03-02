<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:variable name="other" select="document('resources/jlc_20060711.xml',/)"/>
  <xsl:variable name="main" select="/"/>

  <xsl:template match="/">
    <xsl:apply-templates select="$other/*"/>
  </xsl:template>

  <xsl:template match="file">
    <xsl:variable name="foos" select="foo"/>

    <msg>List of all `foo`s from 'other.xml'...</msg>
    <xsl:apply-templates select="foo" mode="debug"/>

    <msg>List of all `foo`s from 'other.xml' (using a variable)...</msg>
    <xsl:apply-templates select="$foos" mode="debug"/>

    <msg>List of all `thing`s from the main input document...</msg>
    <xsl:apply-templates select="$main/file/thing" mode="debug"/>

    <msg>List of all `thing`s that do not correspond to some `foo` (using current())...</msg>
    <xsl:apply-templates select="
      $main/file/thing[not(. = current()/foo)]" mode="debug"/>

    <msg>List of all `thing`s that do not correspond to some `foo` (using a variable)...</msg>
    <xsl:apply-templates select="
      $main/file/thing[not(. = $foos)]" mode="debug"/>
  </xsl:template>

  <xsl:template match="*" mode="debug">
    <xsl:value-of select="name()"/>
    <xsl:text> := `</xsl:text>
    <xsl:value-of select="."/>
    <xsl:text>'&#10;</xsl:text>
  </xsl:template>
</xsl:stylesheet>
