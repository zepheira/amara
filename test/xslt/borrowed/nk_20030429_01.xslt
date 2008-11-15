<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns="http://www.w3.org/1999/xhtml" 
  version="1.0" 
  >
 
  <xsl:output method='html' indent='yes' encoding="UTF-8" /> 
  
  <xsl:param name="homepath"/> 
  <xsl:param name="previous"/> 
  <xsl:param name="next"/> 
  <xsl:param name="printable_version"/> 
  <xsl:param name="ads"/> 
 
  <xsl:variable name="ads_declared" 
    select="string((/html/body/tab/@ads | /html/body/@ads)[position()=last()])"/>
  <xsl:variable name="column_format" 
    select="string((/html/body/tab/@column_format | /html/body/@column_format)[position()=last()])"/> 
  <!-- is either "" (default: two) or "one" or "two" --> 
 
  <xsl:variable name="horizontal_contents" 
    select="string((/html/body/tab/@horizontal_contents | /html/body/@horizontal_contents)[position()=last()])"/> 
  
  <xsl:variable name="html-ns">http://www.w3.org/1999/xhtml</xsl:variable> 
 
  <xsl:template match="/html/head"> 
    <head> 
      <meta http-equiv='Content-Type' content='text/html; charset=UTF-8'/> 
      <xsl:apply-templates/> 
    </head> 
  </xsl:template>  
  
  <xsl:template match="*"> 
    <xsl:element name="{local-name(.)}" namespace="{$html-ns}"> 
      <xsl:apply-templates select="@*|node()"/> 
    </xsl:element> 
  </xsl:template> 
 
  <xsl:template match="@* | processing-instruction()"> 
    <xsl:copy/> 
  </xsl:template> 
 
  <xsl:template match="text()"> 
    <xsl:call-template name="do-symbols"> 
      <xsl:with-param name="str" select="."/> 
    </xsl:call-template> 
  </xsl:template> 
 
  <xsl:template name="do-symbols"> 
    <xsl:param name="str"/> 
    <xsl:choose> 
      <xsl:when test="contains($str,'---')"> 
        <xsl:call-template name="do-symbols"> 
          <xsl:with-param name="str" 
            select="concat(substring-before($str, '---'), 
                    '&#x2014;',
                    substring-after($str, '---'))"/> 
        </xsl:call-template> 
      </xsl:when> 
      <xsl:when test="contains($str,'``')"> 
        <xsl:call-template name="do-symbols"> 
          <xsl:with-param name="str" 
            select="concat(substring-before($str, 
                    '``'), 
                    '&#x201C;', 
                    substring-after($str, '``'))"/> 
        </xsl:call-template> 
      </xsl:when> 
      <xsl:when test='contains($str,"&apos;&apos;")'> 
        <xsl:call-template name="do-symbols"> 
          <xsl:with-param name="str" 
            select='concat(substring-before($str, "&apos;&apos;"), 
                    &quot;&#x201D;&quot;, 
                    substring-after($str, "&apos;&apos;"))' /> 
        </xsl:call-template> 
      </xsl:when> 
      <xsl:otherwise> 
        <xsl:value-of select="$str"/> 
      </xsl:otherwise> 
    </xsl:choose> 
  </xsl:template> 
 
  <xsl:template match="html"> 
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"> 
      <xsl:apply-templates select="*"/> 
    </html> 
  </xsl:template> 
 
  <xsl:template match="related"/> 
 
  <xsl:template match="printable"/> 
 
  <xsl:template match="head/*"> 
    <xsl:if test="not (local-name(.) = 'related' or 
                  local-name(.) = 'contents' or 
                  local-name(.) = 'ads')"> 
      <xsl:copy-of select="."/> 
    </xsl:if> 
  </xsl:template> 
 
  <xsl:template match="body"> 
    <body> 
      <xsl:choose> 
        <xsl:when test="$column_format='two' or 
                        $column_format=''"> 
          <xsl:if test="$horizontal_contents='yes'"> 
            <xsl:call-template name="horizontal_contents"/> 
          </xsl:if> 
          <table class="columntwo"> 
            <tr>
              <!-- index and related column --> 
              <td valign="top" class="firstcolumn"> 
                <xsl:if test="count(/html/head/contents/*) > 1 and not 
                  ($horizontal_contents='yes')"> 
                  <div class="contents">
                    <h2>Contents</h2> 
                    <ul>
                      <xsl:for-each select="/html/head/contents/*"> 
                        <li> 
                          <h3>
                            <xsl:copy-of select="."/> 
                          </h3> 
                        </li> 
                      </xsl:for-each>
                    </ul> 
                  </div> 
                </xsl:if> 
              </td> 
            </tr>
          </table>
        </xsl:when>
        <xsl:otherwise>ERROR column_format='<xsl:value-of select='$column_format'/>'</xsl:otherwise> 
      </xsl:choose>
    </body> 
  </xsl:template>

</xsl:stylesheet>
