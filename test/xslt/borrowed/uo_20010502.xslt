<?xml version='1.0' encoding='UTF-8'?>
<!--
#This source doc used to bomb cDomlette just on parse, as Uche found out
-->
<xsl:stylesheet xhtml:dummy-for-xmlns='' exslt:dummy-for-xmlns='' version='1.0' rdf:dummy-for-xmlns='' dc:dummy-for-xmlns='' xmlns:xsl='http://www.w3.org/1999/XSL/Transform' xmlns:dc='http://purl.org/dc/elements/1.1/' xmlns:exslt='http://exslt.org/documentation' xmlns:xhtml='http://www.w3.org/1999/xhtml' xmlns:sch='http://www.ascc.net/xml/schematron' xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'><xsl:output method='text' xmlns:axsl='http://www.w3.org/1999/XSL/TransformAlias'/><xsl:template match='*|@*' mode='schematron-get-full-path'><xsl:apply-templates select='parent::*' mode='schematron-get-full-path'/><xsl:text>/</xsl:text><xsl:if test='count(. | ../@*) = count(../@*)'>@</xsl:if><xsl:value-of select='name()'/><xsl:text>[</xsl:text><xsl:value-of select='1+count(preceding-sibling::*[name()=name(current())])'/><xsl:text>]</xsl:text></xsl:template><xsl:template match='/'>EXSLT 1.9
<xsl:apply-templates select='/' mode='M5'/></xsl:template><xsl:template match='/' mode='M5' priority='4000'><xsl:choose><xsl:when test='exslt:function'/><xsl:otherwise>In pattern exslt:function:
   The root element must be exslt:function element.
</xsl:otherwise></xsl:choose><xsl:apply-templates mode='M5'/></xsl:template><xsl:template match='exslt:function' mode='M5' priority='3999'><xsl:choose><xsl:when test='exslt:name or count(exslt:name) > 1'/><xsl:otherwise>In pattern exslt:name or count(exslt:name) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain one exslt:name element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='rdf:Description or count(rdf:Description) > 1'/><xsl:otherwise>In pattern rdf:Description or count(rdf:Description) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain one rdf:Description element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:doc or count(exslt:doc) > 1'/><xsl:otherwise>In pattern exslt:doc or count(exslt:doc) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain one exslt:doc element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:definition or count(exslt:definition) > 1'/><xsl:otherwise>In pattern exslt:definition or count(exslt:definition) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain one exslt:definition element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:implementations or count(exslt:implementations) > 1'/><xsl:otherwise>In pattern exslt:implementations or count(exslt:implementations) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain one exslt:implementations element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:use-cases or count(exslt:use-cases) > 1'/><xsl:otherwise>In pattern exslt:use-cases or count(exslt:use-cases) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain one exslt:use-cases element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@module'/><xsl:otherwise>In pattern @module:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a module attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@version'/><xsl:otherwise>In pattern @version:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a version attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test="@status and (@status='new' or @status='revised' or @status='reviewed' or @status='implemented' or @status='stable')"/><xsl:otherwise>In pattern @status and (@status='new' or @status='revised' or @status='reviewed' or @status='implemented' or @status='stable'):
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a status attribute of value 'new', 'revised', 'reviewed', 'implemented' or 'stable.
</xsl:otherwise></xsl:choose><xsl:apply-templates mode='M5'/></xsl:template><xsl:template match='exslt:implementation' mode='M5' priority='3998'><xsl:choose><xsl:when test='@function'/><xsl:otherwise>In pattern @function:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a function attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@src'/><xsl:otherwise>In pattern @src:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a src attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@language'/><xsl:otherwise>In pattern @language:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a language attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@version'/><xsl:otherwise>In pattern @version:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a version attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@algorithm'/><xsl:otherwise>In pattern @algorithm:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have an algorithm attribute.
</xsl:otherwise></xsl:choose><xsl:apply-templates mode='M5'/></xsl:template><xsl:template match='exslt:use-case' mode='M5' priority='3997'><xsl:choose><xsl:when test='@function'/><xsl:otherwise>In pattern @function:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a function attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@type'/><xsl:otherwise>In pattern @type:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a type attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@template'/><xsl:otherwise>In pattern @template:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a template attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@data'/><xsl:otherwise>In pattern @data:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a data attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@xslt'/><xsl:otherwise>In pattern @xslt:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a xslt attribute.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='@result'/><xsl:otherwise>In pattern @result:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must have a result attribute.
</xsl:otherwise></xsl:choose><xsl:apply-templates mode='M5'/></xsl:template><xsl:template match='rdf:Description' mode='M5' priority='3996'><xsl:choose><xsl:when test='exslt:revision|exslt:version'/><xsl:otherwise>In pattern exslt:revision|exslt:version:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element must contain either one exslt:version element or at least one exslt:revision element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:revision and count(dc:title) > 1'/><xsl:otherwise>In pattern exslt:revision and count(dc:title) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element with exslt:revision must contain no more than one dc:title element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:revision and count(dc:rights) > 1'/><xsl:otherwise>In pattern exslt:revision and count(dc:rights) > 1:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element with exslt:revision must contain no more than one dc:rights element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:version and dc:creator'/><xsl:otherwise>In pattern exslt:version and dc:creator:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element with exslt:version must contain at least one dc:creator element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:version and dc:date'/><xsl:otherwise>In pattern exslt:version and dc:date:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element with exslt:version must contain one dc:date element.
</xsl:otherwise></xsl:choose><xsl:choose><xsl:when test='exslt:version and dc:description'/><xsl:otherwise>In pattern exslt:version and dc:description:
   A<xsl:text xml:space='preserve'> </xsl:text><xsl:value-of select='name(.)'/><xsl:text xml:space='preserve'> </xsl:text>element with exslt:version must contain one dc:description element.
</xsl:otherwise></xsl:choose><xsl:apply-templates mode='M5'/></xsl:template><xsl:template match='text()' mode='M5' priority='-1'/><xsl:template match='text()' priority='-1'/></xsl:stylesheet>
