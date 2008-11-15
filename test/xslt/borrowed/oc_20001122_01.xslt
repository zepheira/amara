<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?> 

                            <xsl:stylesheet 
                            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
                            version="1.0" 
                            > 

                            <xsl:output method="html" encoding="ISO-8859-1"/> 

                            <xsl:template match="/"> 
                            <html> 
                            <head> 
                            <title>Address Book Test</title> 
                            </head> 
                            <body> 
                            <xsl:apply-templates/> 
                            </body> 
                            </html> 
                            </xsl:template> 
                            <xsl:template match="addressbook"> 
                            <p>My friends are: 
                            <ul> 
                            <xsl:apply-templates/> 
                            </ul> 
                            </p> 
                            </xsl:template> 

                            <xsl:template match="entry"> 
                            <li> 
                            <xsl:value-of select="firstname"/><xsl:text> </xsl:text> 
                            <xsl:value-of select="lastname"/> 
                            </li> 
                            </xsl:template> 

                            </xsl:stylesheet>