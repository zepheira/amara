<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  exclude-result-prefixes="exsl">

  <xsl:output method="xml" indent="yes"/>

  <!-- Group cities on country -->
  <xsl:template match="/">
    <result>
      <xsl:call-template name="group-on-key">
        <xsl:with-param name="nodes" select="//city"/>
        <xsl:with-param name="key" select="'country'"/>
      </xsl:call-template>
    </result>
  </xsl:template>

<!--
  Template: group-on-key
  Use this template to group <nodes> which share a common attribute <key>
  The result will be sub-sets of <nodes> surrounded by <group/> tags
-->


<xsl:template name="group-on-key">
  <xsl:param name="nodes"/>
  <xsl:param name="key"/>

  <xsl:variable name="items">
    <xsl:for-each select="$nodes">
      <item>
        <key>
          <xsl:value-of select="./@*[name() = $key]"/>
        </key>
        <value>
          <xsl:copy-of select="."/>
        </value>
      </item>
    </xsl:for-each>
  </xsl:variable>

  <xsl:variable name="grouped-items">
    <xsl:call-template name="group-on-item">
      <xsl:with-param name="nodes" select="exsl:node-set($items)/*"/>
      <xsl:with-param name="key" select="$key"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:for-each select="exsl:node-set($grouped-items)/*">
    <xsl:copy>
      <xsl:for-each select="./*">
        <xsl:copy-of select="./value/*[1]"/>
      </xsl:for-each>
    </xsl:copy>
  </xsl:for-each>
</xsl:template>

<!--
 Template: group-on-item
 Use this template to group <nodes> which share a common structure.
 You can build this structure yourself if you want to group on something else

 The structure is the <item> structure and has the following layout
 <item>
  <key>
   aKey (can be anything, preferrably a string)
  </key>
  <value>
   aValue (can be anything, probably a node(set))
  </value>
 </item>

 <items> will we grouped on the string value of <key>
 The result will be sub-sets of <items> surrounded by <group/> tags
-->

<xsl:template name="group-on-item">
  <xsl:param name="nodes"/>

  <!-- Step 1 -->
  <xsl:variable name="sorted">
    <xsl:for-each select="$nodes">
      <xsl:sort select="./key[1]"/>
      <xsl:copy-of select="."/>
    </xsl:for-each>
  </xsl:variable>

  <xsl:variable name="sorted-tree" select="exsl:node-set($sorted)/*"/>

  <!-- Step 2.1 -->
  <xsl:variable name="pivots">
    <xsl:call-template name="pivots">
      <xsl:with-param name="nodes" select="$sorted-tree"/>
    </xsl:call-template>
  </xsl:variable>

  <!-- Step 2.2 -->
  <xsl:variable name="ranges">
    <xsl:call-template name="ranges">
      <xsl:with-param name="pivots" select="exsl:node-set($pivots)/*"/>
      <xsl:with-param name="length" select="count($sorted-tree)"/>
    </xsl:call-template>
  </xsl:variable>

  <!-- Step 3.1 -->
  <xsl:variable name="partition-ranges">
    <xsl:call-template name="partition-ranges">
      <xsl:with-param name="node" select="$sorted-tree[1]"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="root-partition" select="exsl:node-set($partition-ranges)/*[1]"/>

  <!-- Step 3.2 -->
  <xsl:for-each select="exsl:node-set($ranges)/r">
    <xsl:variable name="s" select="./@s"/>
    <xsl:variable name="e" select="./@e"/>

    <group>
      <xsl:call-template name="range-in-partition">
        <xsl:with-param name="s" select="$s"/>
        <xsl:with-param name="e" select="$e"/>
        <xsl:with-param name="p" select="$root-partition"/>
      </xsl:call-template>
    </group>
  </xsl:for-each>

</xsl:template>

<xsl:template name="pivots">
  <xsl:param name="nodes"/>
  <xsl:param name="key"/>

  <xsl:for-each select="$nodes">
    <xsl:if test="not(string(./key[1]) = string(./following-sibling::*[1]/key[1]))">
      <pivot>
        <xsl:value-of select="position()"/>
      </pivot>
    </xsl:if>
  </xsl:for-each>
</xsl:template>

<xsl:template name="ranges">
  <xsl:param name="pivots" select=".."/>
  <xsl:param name="length" select="0"/>

  <xsl:choose>
  <xsl:when test="count($pivots) &gt;= 1">
  <xsl:for-each select="$pivots">
    <xsl:variable name="p" select="./preceding-sibling::*[1]"/>
    <r>
      <xsl:attribute name="s">
        <xsl:choose>
          <xsl:when test="$p">
            <xsl:value-of select="$p + 1"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="1"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:attribute name="e">
        <xsl:value-of select="string(.)"/>
      </xsl:attribute>
    </r>
  </xsl:for-each>
  </xsl:when>
  <xsl:otherwise>
    <r>
      <xsl:attribute name="s">
        <xsl:value-of select="1"/>
      </xsl:attribute>
      <xsl:attribute name="e">
        <xsl:value-of select="$length"/>
      </xsl:attribute>
    </r>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!--
 Template: range-in-partition
 Selects a RANGE of nodes using a binary tree

 XSLT isn't really helping to make things easy but try to do this in a DVC style
directly without the help of a binary tree.
-->

<xsl:template name="range-in-partition">
  <xsl:param name="p"/>
  <xsl:param name="s" select="$p/@s"/>
  <xsl:param name="e" select="$p/@e"/>

  <xsl:variable name="ps" select="number($p/@s)"/>
  <xsl:variable name="pe" select="number($p/@e)"/>

  <xsl:if test="$s &lt;= $pe and $e &gt;= $ps">
    <xsl:if test="$ps = $pe">
      <xsl:copy-of select="$p/*[1]"/>
    </xsl:if>
    <xsl:choose>
      <xsl:when test="$s &gt; $ps">
        <xsl:variable name="s1" select="$s"/>
        <xsl:choose>
          <xsl:when test="$e &lt; $pe">
            <xsl:variable name="e1" select="$e"/>
            <xsl:for-each select="$p/*">
              <xsl:call-template name="range-in-partition">
                <xsl:with-param name="s" select="$s1"/>
                <xsl:with-param name="e" select="$e1"/>
                <xsl:with-param name="p" select="."/>
              </xsl:call-template>
            </xsl:for-each>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="e1" select="$pe"/>
            <xsl:for-each select="$p/*">
              <xsl:call-template name="range-in-partition">
                <xsl:with-param name="s" select="$s1"/>
                <xsl:with-param name="e" select="$e1"/>
                <xsl:with-param name="p" select="."/>
              </xsl:call-template>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="s1" select="$ps"/>
        <xsl:choose>
          <xsl:when test="$e &lt; $pe">
            <xsl:variable name="e1" select="$e"/>
            <xsl:for-each select="$p/*">
              <xsl:call-template name="range-in-partition">
                <xsl:with-param name="s" select="$s1"/>
                <xsl:with-param name="e" select="$e1"/>
                <xsl:with-param name="p" select="."/>
              </xsl:call-template>
            </xsl:for-each>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="e1" select="$pe"/>
            <xsl:for-each select="$p/*">
              <xsl:call-template name="range-in-partition">
                <xsl:with-param name="s" select="$s1"/>
                <xsl:with-param name="e" select="$e1"/>
                <xsl:with-param name="p" select="."/>
              </xsl:call-template>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:if>
</xsl:template>

  <xsl:template name="partition-ranges">
    <xsl:param name="node"/>
    <xsl:param name="s" select="(count($node/preceding-sibling::*)) + 1"/>
    <xsl:param name="e" select="(count($node/following-sibling::*)) + $s"/>

    <xsl:if test="$node">
      <xsl:element name="r">
        <xsl:attribute name="s">
          <xsl:value-of select="$s"/>
        </xsl:attribute>
        <xsl:attribute name="e">
          <xsl:value-of select="$e"/>
        </xsl:attribute>
        <xsl:choose>
          <xsl:when test="$s = $e">
            <xsl:copy-of select="$node"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="w" select="floor(($e - $s + 1) div 2)"/>
            <xsl:variable name="m" select="$s + $w"/>
            <xsl:call-template name="partition-ranges">
              <xsl:with-param name="node" select="$node"/>
              <xsl:with-param name="s" select="$s"/>
              <xsl:with-param name="e" select="$m - 1"/>
            </xsl:call-template>
            <xsl:call-template name="partition-ranges">
              <xsl:with-param name="node" select="$node/following-sibling::*[$w]"/>
              <xsl:with-param name="s" select="$m"/>
              <xsl:with-param name="e" select="$e"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:element>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>