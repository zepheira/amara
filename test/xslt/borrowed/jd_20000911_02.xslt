<?xml version="1.0" ?>

<!-- rdf (syntax sucks) 1.0 "parser" -->
<!-- revision: 2000-09-11 -->
<!-- contact: jason@injektilo.org -->

<!-- todo: containers, parseType="Literal", reified statements?, and more -->

<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  exclude-result-prefixes="rdf"
>

<xsl:output method="xml" indent="yes"/>

<xsl:variable name="rdf" select="'http://www.w3.org/1999/02/22-rdf-syntax-ns#'"/>

<!-- disable the built-in templates that copies text through -->
<xsl:template match="text()|@*"></xsl:template>

<xsl:template match="rdf:RDF">

<model>
  <xsl:apply-templates/>
</model>

</xsl:template>

<!-- match a description or a resource -->
<xsl:template match="rdf:RDF//*">

<xsl:variable name="subject">
  <xsl:call-template name="resource"/>
</xsl:variable>

<!-- if this isn't an rdf:Description node then it's probably
  an abbreviated typed node so output a statement telling
  what type it is -->
<xsl:if test="namespace-uri() != $rdf and local-name() != 'Description' and @rdf:about">
  <xsl:call-template name="statement">
    <xsl:with-param name="subject-value" select="@rdf:about"/>
    <xsl:with-param name="predicate-namespace-uri" select="$rdf"/>
    <xsl:with-param name="predicate-local-name" select="'type'"/>
    <xsl:with-param name="object-type" select="'resource'"/>
    <xsl:with-param name="object-value" select="concat(namespace-uri(), local-name())"/>
  </xsl:call-template>
</xsl:if>

<!-- output the statments for this node's attributes -->
<xsl:call-template name="attributes">
  <xsl:with-param name="subject" select="$subject"/>
</xsl:call-template>

<!-- output statements for each child element (property) -->
<xsl:for-each select="*">

  <xsl:choose>
    <!-- if this node has an rdf:Description child then the the resource
      described by that Description is the object for this property. -->
    <xsl:when test="rdf:Description">

      <xsl:variable name="object-value">
        <xsl:call-template name="resource">
          <xsl:with-param name="node" select="rdf:Description"/>
        </xsl:call-template>
      </xsl:variable>      

      <xsl:call-template name="statement">
        <xsl:with-param name="subject-value" select="$subject"/>
        <xsl:with-param name="predicate-namespace-uri" select="namespace-uri()"/>
        <xsl:with-param name="predicate-local-name" select="local-name()"/>
        <xsl:with-param name="object-type" select="'resource'"/>
        <xsl:with-param name="object-value" select="$object-value"/>
      </xsl:call-template>
      
      <!-- now recursively output the statments for this child resource -->
      <xsl:apply-templates select="rdf:Description"/>

    </xsl:when>
    <xsl:otherwise>
    
      <!-- determine the object type and value -->
      <xsl:variable name="object-type">
        <xsl:choose>
          <xsl:when test="@rdf:resource">resource</xsl:when>
          <xsl:when test="namespace-uri() = $rdf and @resource">resource</xsl:when>
          <!-- watch out for typed nodes -->
          <xsl:when test="*[1]/@rdf:about">resource</xsl:when>
          <xsl:otherwise>literal</xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <xsl:variable name="object-value">
        <xsl:choose>
          <xsl:when test="@rdf:resource">
            <xsl:value-of select="@rdf:resource"/>
          </xsl:when>
          <xsl:when test="namespace-uri() = $rdf and @resource">
            <xsl:value-of select="@resource"/>
          </xsl:when>
          <xsl:when test="*[1]/@rdf:about">
            <xsl:value-of select="*[1]/@rdf:about"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="."/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <xsl:call-template name="statement">
        <xsl:with-param name="subject-value" select="$subject"/>
        <xsl:with-param name="predicate-namespace-uri" select="namespace-uri()"/>
        <xsl:with-param name="predicate-local-name" select="local-name()"/>
        <xsl:with-param name="object-type" select="$object-type"/>
        <xsl:with-param name="object-value" select="$object-value"/>
      </xsl:call-template>

      <xsl:if test="$object-type = 'resource'">
        <xsl:choose>
          <xsl:when test="*[1]/@rdf:about">
            <!-- handle this child resource's properties -->            
            <xsl:apply-templates select="*[1]"/>
          </xsl:when>
          <xsl:otherwise>
            <!-- handle this resource's properties -->
            <xsl:apply-templates select="."/>
          </xsl:otherwise>
        </xsl:choose>            
      </xsl:if>

    </xsl:otherwise>
  </xsl:choose>

</xsl:for-each>

</xsl:template>

<!-- return the resource uri for a node or generate a unique one -->
<xsl:template name="resource">
  <xsl:param name="node" select="."/>
  
<xsl:choose>
  <xsl:when test="namespace-uri($node) = $rdf and $node/@about">
    <xsl:value-of select="$node/@about"/>
  </xsl:when>
  <xsl:when test="namespace-uri($node) = $rdf and $node/@resource">
    <xsl:value-of select="$node/@resource"/>
  </xsl:when>
  <xsl:when test="namespace-uri($node) != $rdf and $node/@rdf:resource">
    <xsl:value-of select="$node/@rdf:resource"/>
  </xsl:when>
  <xsl:when test="namespace-uri($node) != $rdf and $node/@rdf:about">
    <xsl:value-of select="$node/@rdf:about"/>
  </xsl:when>
  <xsl:otherwise>
    <xsl:value-of select="concat('anonymous:', generate-id())"/>
  </xsl:otherwise>
</xsl:choose>
  
</xsl:template>

<!-- output statements for the current node's attributes -->
<xsl:template name="attributes">
  <xsl:param name="subject"/>

<xsl:for-each select="@*">
  <xsl:variable name="attribute-namespace-uri" select="namespace-uri()"/>
  <xsl:if test="$attribute-namespace-uri != $rdf">
    <xsl:if test="$attribute-namespace-uri != ''">
      <xsl:call-template name="statement">
        <xsl:with-param name="subject-value" select="$subject"/>
        <xsl:with-param name="predicate-namespace-uri" select="$attribute-namespace-uri"/>
        <xsl:with-param name="predicate-local-name" select="local-name()"/>
        <xsl:with-param name="object-type" select="'literal'"/>
        <xsl:with-param name="object-value" select="."/>
      </xsl:call-template>
    </xsl:if>
  </xsl:if>
</xsl:for-each>

</xsl:template>

<!-- output a statment -->
<xsl:template name="statement">
  <xsl:param name="subject-value"/>
  <xsl:param name="predicate-namespace-uri"/>
  <xsl:param name="predicate-local-name"/>
  <xsl:param name="object-type"/>
  <xsl:param name="object-value"/>

<statement>
  <subject><xsl:value-of select="$subject-value"/></subject>
  <predicate><xsl:value-of select="concat($predicate-namespace-uri, $predicate-local-name)"/></predicate>
  <object type="{$object-type}"><xsl:value-of select="$object-value"/></object>
</statement>

</xsl:template>

</xsl:transform>
