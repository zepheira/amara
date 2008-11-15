<?xml version="1.0"?>

<xsl:transform xmlns:xsl='http://www.w3.org/1999/XSL/Transform' version='1.0'>
  <xsl:strip-space elements='*'/>

  <xsl:template match='rss'>
    <html-body>
      <h1>
        <xsl:apply-templates select="channel"/>
      </h1>
    </html-body>
  </xsl:template>

  <xsl:template match='channel'>
    <h2>
      <xsl:value-of select='./title'/>
    </h2>
    <table>
      <tr>
        <td>Description:</td>
        <td>
          <xsl:value-of select='./description'/>
        </td>
      </tr>
<tr>
<td>URL:</td>
<td>
<xsl:apply-templates mode='multilink' select='link'/>
</td>
</tr>
</table>
<xsl:apply-templates select='item'/>
</xsl:template>

<xsl:template match='item'>
<h3>
<xsl:apply-templates select='title'/>
</h3>
<table>
<xsl:apply-templates mode='first' select='description'/>
<xsl:apply-templates mode='first' select='link'/>
</table>
</xsl:template>
<xsl:template match='title'>
<xsl:value-of select='.'/>
</xsl:template>

<xsl:template match='link'>
<xsl:element name='a'>
<xsl:attribute name='href'>
<xsl:value-of select='.'/>
</xsl:attribute>
<xsl:value-of select='.'/>
</xsl:element>
</xsl:template>

<xsl:template mode='multi' match='*'>
<xsl:value-of select='.'/>
</xsl:template>

<xsl:template mode='first' match='description'>
<tr>
<td>
Description:
</td>
<td>
<xsl:apply-templates mode='multi'
select='../description'/>
</td>
</tr>
</xsl:template>
<xsl:template mode='multilink' match='*'>
<xsl:element name='a'>
<xsl:attribute name='href'>
<xsl:value-of select='.'/>
</xsl:attribute>
<xsl:value-of select='.'/>
</xsl:element>
</xsl:template>

<xsl:template mode='first' match='link'>
<tr>
<td>
More detail at:
</td>
<td>
<xsl:apply-templates mode='multilink' select='../link'/>
</td>
</tr>
</xsl:template>

</xsl:transform>
