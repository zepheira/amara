<?xml version="1.0"?> 

<!-- Identify transformation -->
<xsl:stylesheet version="1.1"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
                

        <xsl:strip-space elements="*"/>


        <xsl:template match="urlpattern">
                <xsl:param name="context"/>
                <xsl:choose>
                        <xsl:when test="boolean(year) and not( boolean( //request/year ) )">
                                <font size="-1">
                                        <xsl:text>(</xsl:text>
                                        <b><xsl:value-of select="$context"/></b>
                                        <xsl:text>: no year)</xsl:text> 
                                </font>
                        </xsl:when>
                        <xsl:when test="boolean(volume) and not( boolean( //request/volume ) )">
                                <font size="-1">
                                        <xsl:text>(</xsl:text>
                                        <b><xsl:value-of select="$context"/></b>
                                        <xsl:text>: no volume)</xsl:text>
                                </font>
                        </xsl:when>
                        <xsl:when test="boolean(issue) and not( boolean( //request/issue ) )">
                                <font size="-1">
                                        <xsl:text>(</xsl:text>
                                        <b><xsl:value-of select="$context"/></b>
                                        <xsl:text>: no issue)</xsl:text>
                                </font>
                        </xsl:when>
                        <xsl:when test="boolean(page) and not( boolean( //request/page ) )">
                                <font size="-1">
                                        <xsl:text>(</xsl:text>
                                        <b><xsl:value-of select="$context"/></b>
                                        <xsl:text>: no page)</xsl:text>
                                </font>
                        </xsl:when>
                        <xsl:when test="boolean(issn) and not( boolean( //request/issn ) )">
                                <font size="-1">
                                        <xsl:text>(</xsl:text>
                                        <b><xsl:value-of select="$context"/></b>
                                        <xsl:text>: no issn)</xsl:text>
                                </font>
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:text disable-output-escaping="yes">&lt;a href="</xsl:text>
                                <xsl:apply-templates/> 
                                <xsl:text disable-output-escaping="yes">"&gt;</xsl:text>
                                <xsl:value-of select="$context"/>
                                <xsl:text disable-output-escaping="yes">&lt;/a&gt;</xsl:text>
                        </xsl:otherwise>
                </xsl:choose>
        </xsl:template>
     

        <xsl:template match="baseurl">
                <!-- keeps looking for $localinfo even if it's Null 
                <xsl:choose>
                        <xsl:when test="not( boolean( $localinfo ) )">
                                <xsl:value-of select="@default"/>
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:value-of select="$localinfo//local[@jakeid='389']//baseurl"/>
                        </xsl:otherwise>
                </xsl:choose>
                -->
                <xsl:value-of select="@default"/>
        </xsl:template>


        <xsl:template match="volume">
                <xsl:call-template name="standard">
                        <xsl:with-param name="value" select="//request/volume"/>
                </xsl:call-template>
        </xsl:template>

        <xsl:template match="issue">
                <xsl:call-template name="standard">
                        <xsl:with-param name="value" select="//request/issue"/>
                </xsl:call-template>
        </xsl:template>

        <xsl:template match="page">
                <xsl:choose>
                        <xsl:when test="contains( //request/page, '-' )">
                                <xsl:call-template name="standard">
                                <xsl:with-param name="value" select="substring-before( //request/page, '-' )"/>
                                </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:call-template name="standard">
                                <xsl:with-param name="value" select="//request/page"/>
                                </xsl:call-template>
                        </xsl:otherwise>
                </xsl:choose>
        </xsl:template>



        <xsl:template name="standard">
                <xsl:param name="value"/>
                <xsl:variable name="format" select="@format"/>
                <xsl:choose>
                        <xsl:when test="$format!=''">
                                <xsl:number format="{@format}" 
                                            value="$value"
                                            level="single"/>
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:value-of select="$value"/>
                        </xsl:otherwise>
                </xsl:choose>
        </xsl:template>

        <xsl:template match="year">
                <xsl:variable name="year" select="//request/year"/>
                <xsl:choose>
                        <xsl:when test="boolean(@length)">
                                <xsl:value-of select="substring( $year,
                                                      string-length( $year ) - @length + 1,
                                                      @length )"/>
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:value-of select="$year"/>
                        </xsl:otherwise>
                </xsl:choose>
        </xsl:template>
                

        <xsl:template match="issn">
                <xsl:variable name="issn" select="//request/issn"/>
                <xsl:variable name="dash" select="@dash"/>
                <xsl:choose>
                        <xsl:when test="boolean(@dash)">
                                <xsl:variable name="issndashed"
                                        select="concat(substring($issn,1,4),
                                                        $dash,
                                                        substring($issn,
                                                                string-length($issn)-3, 4) )"/>
                                <xsl:call-template name="case">
                                        <xsl:with-param name="issndashed" select="$issndashed"/>
                                </xsl:call-template>    
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:call-template name="case">
                                        <xsl:with-param name="issndashed" select="$issn"/>
                                </xsl:call-template>
                        </xsl:otherwise>
                </xsl:choose>
        </xsl:template>


        <xsl:template name="case">
                <xsl:param name="issndashed"/>
                <xsl:variable name="case" select="@case"/>
                <xsl:choose>
                        <xsl:when test="$case='upper'">
                                <xsl:variable name="issntranslated" 
                                        select="translate($issndashed,'x','X')"/>
                                <xsl:value-of select="$issntranslated"/>
                        </xsl:when>
                        <xsl:when test="$case='lower'">
                                <xsl:variable name="issntranslated" 
                                        select="translate($issndashed,'X','x')"/>
                                <xsl:value-of select="$issntranslated"/>
                        </xsl:when>      
                        <xsl:otherwise>
                                <xsl:variable name="issntranslated"
                                        select="$issndashed"/>
                                <xsl:value-of select="$issntranslated"/>
                        </xsl:otherwise>
                </xsl:choose>
        </xsl:template>


</xsl:stylesheet>
