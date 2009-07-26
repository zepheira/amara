<!--
Example from David Carlisle to ??? on 10 Feb 2000, with
well-formedness corrections.

  Note: this one is tricky.  We have the default namespace in exclude-result
  So it shouldn't appear, right?  Wrong.  The literal result element output
  by the template is actually in the http://duncan.com ns by virtue of default
  So it must be declared as such in the output.
-->
<xsl:stylesheet
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:boo="http://banquo.com"
 xmlns="http://duncan.com"
 exclude-result-prefixes='#default boo'
 version="1.0"
>

<xsl:template match="/boo:a">
  <foo><xsl:value-of select="translate(.,'&#10; ','')"/></foo>
</xsl:template>

</xsl:stylesheet> 
