<?xml version="1.0"?> 
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template match="Document">
        <html><body>
        <h1>XSL Numbering test</h1>
        <blockquote>
            <xsl:apply-templates select="*"/>
        </blockquote>
        </body></html>
    </xsl:template>
    
    <xsl:template match="Topic|Section">
        <p>For <xsl:value-of select="name"/> '<xsl:value-of select="@name"/>':
            <ul>
                <li>'single' number = <xsl:number level="single"/></li>
                <li>'multiple' number = <xsl:number level="multiple" format='1.'/></li>
                <li>'any' number = <xsl:number level="any"/></li>
            </ul>
        </p>
        <xsl:apply-templates select="*"/>
    </xsl:template>
    
</xsl:stylesheet>