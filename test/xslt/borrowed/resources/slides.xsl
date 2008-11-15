<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xt="http://www.jclark.com/xt"
                extension-element-prefixes="xt"
                version="1.0"
>

  <xsl:template match="/presentation">
     <xt:document method="html" encoding="ISO-8859-1" href="index.html">
       <html>
         <head>
           <meta name="description" content="Elliotte Rusty Harold's presentation on XLinks and XPointers to the XML SIG of the Object Developer's Group, August 25, 1999"></meta>
           <title><xsl:value-of select="title"/></title>         
         </head>
         <body> 
           <h1><xsl:value-of select="title" align="center"/></h1> 
           <ul>
             <xsl:for-each select="slide">
               <li><a href="{format-number(position(),'00')}.html"><xsl:value-of select="title"/></a></li>
             </xsl:for-each>    
           </ul>              
           <hr/>
           <div align="center">
             <A HREF="01.html">Start</A> | <A HREF="/xml/">Cafe con Leche</A>
           </div>
           <hr/>
           <font size="-1">
              Copyright 1999 
              <a href="http://www.macfaq.com/personal.html">Elliotte Rusty Harold</a><br/>       
              <a href="mailto:elharo@metalab.unc.edu">elharo@metalab.unc.edu</a><br/>
              Last Modified <xsl:apply-templates select="last_modified" mode="lm"/>
           </font>
         </body>     
       </html>     
     </xt:document>     
     <xsl:apply-templates select="slide"/>
  </xsl:template>
  
  <xsl:template match="slide">
  
     <!-- For online use default styles --> 
     <xt:document method="html" encoding="ISO-8859-1" href="{format-number(position(),'00')}.html">
       <html>
         <head>
           <meta name="description" 
                 content="A slide from Elliotte Rusty Harold's presentation on XLinks and XPointers to the XML SIG of the Object Developer's Group, August 25, 1999"/>
           <title><xsl:value-of select="title"/></title>
           <script language="JAVASCRIPT"> 
              <xsl:text disable-output-escaping="yes">&lt;!-- </xsl:text>
              var isnav
              
              if (parseInt(navigator.appVersion) >= 4) {
                if (navigator.appName == "Netscape") {
                  isNav = true
                  document.captureEvents(Event.KEYPRESS)
                }
                else {
                  isNav = false
                }
              }
              document.onkeypress = flipslide

              function flipslide(evt) {
                var key = isNav ? evt.which : window.event.keyCode
                if (key == 32 || key == 29 || key == 30 || key == 11) {
                  <xsl:if test="position()!=last()">
                    location.href="<xsl:number value="position()+1" format="01"/>.html"
                  </xsl:if>
                }
                else if (key == 28 || key == 31 || key == 12) {
                  <xsl:if test="position()!=1">
                    location.href="<xsl:number value="position()-1" format="01"/>.html"
                  </xsl:if>
                  <xsl:if test="position()=1">
                    location.href="index.html"
                  </xsl:if>
                }
                else if (key == 1) {
                  location.href="index.html";
                }
              } // <xsl:text disable-output-escaping="yes"> --&gt;</xsl:text>             
           </script>         
         </head>
         <body>           
             <xsl:apply-templates/>                  
           <hr/>
           <!-- Need to treat first and last slide specially --> 
           <xsl:choose>
             <xsl:when test="position()=1">
               <div align="center">
                 <A HREF="{format-number(position()+1,'00')}.html">Next</A> | <A HREF="index.html">Top</A> | <A HREF="/xml/">Cafe con Leche</A>
               </div>
             </xsl:when>
             <xsl:when test="position()=last()">
               <div align="center">
                 <A HREF="01.html">Start</A> | <A HREF="{format-number(position()-1,'00')}.html">Previous</A> | <A HREF="/xml/">Cafe con Leche</A>
               </div>
             </xsl:when>
             <xsl:otherwise>
               <div align="center">
                 <A HREF="{format-number(position()-1,'00')}.html">Previous</A> | <A HREF="{format-number(position()+1,'00')}.html">Next</A> | 
                 <A HREF="index.html">Top</A> | <A HREF="/xml/">Cafe con Leche</A>
               </div>
             </xsl:otherwise>
           </xsl:choose>

           <hr/>
           <div style="font-size: x-small">
              Copyright 1999 
              <a href="http://www.macfaq.com/personal.html">Elliotte Rusty Harold</a><br/>       
              <a href="mailto:elharo@metalab.unc.edu">elharo@metalab.unc.edu</a><br/>
              Last Modified 
              <xsl:choose>
                <xsl:when test="last_modified">
                  <xsl:value-of select="last_modified" mode="lm"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="/presentation/default_last_modified"/>
                </xsl:otherwise>
              </xsl:choose>
           </div>
         </body>     
       </html>
     </xt:document>
     
     <!-- Now make print slide that doesn't have navigation and uses larger fonts -->     
     <xt:document method="html" encoding="ISO-8859-1" href="print{format-number(position(),'00')}.html">
       <html>
         <head>
           <style type="text/css">
             <xsl:text disable-output-escaping="yes">
               &lt;!-- 
             </xsl:text>
              body {font-family: "New York" "Times New Roman" Times serif;
                    font-size: 16pt }
              h1 {font-size: 28pt}
              code {font-size: 14pt; font-weight: bold}
             <xsl:text disable-output-escaping="yes">
                -->
             </xsl:text>
           </style>

           <meta name="description" content="A slide from Elliotte Rusty Harold's presentation on XLinks and XPointers to the XML SIG of the Object Developer's Group, August 25, 1999"></meta>

           <title><xsl:value-of select="title"/></title>         
         </head>
         <body>           
             <xsl:apply-templates/>                  
           <hr/>
           <div style="font-size: x-small">
              Copyright 1999 
              <a href="http://www.macfaq.com/personal.html">Elliotte Rusty Harold</a><br/>       
              <a href="mailto:elharo@metalab.unc.edu">elharo@metalab.unc.edu</a><br/>
              Last Modified 
              <xsl:choose>
                <xsl:when test="last_modified">
                  <xsl:value-of select="last_modified" mode="lm"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="/presentation/default_last_modified"/>
                </xsl:otherwise>
              </xsl:choose>
           </div>
         </body>     
       </html>
     </xt:document>   
     
     <!-- For onscreen presentation, use larger fonts with navigation --> 
    <xt:document method="html" encoding="ISO-8859-1" href="onscreen{format-number(position(),'00')}.html">
       <html>
         <head>
           <style type="text/css">
             <xsl:text disable-output-escaping="yes">
               &lt;!-- 
             </xsl:text>
              body {font-family: "New York" "Times New Roman" Times serif;
                    font-size: 15pt }
              h1 {font-size: 28pt}
              code {font-size: 13pt; font-weight: bold}
             <xsl:text disable-output-escaping="yes">
                -->
             </xsl:text>
           </style>

           <meta name="description" content="A slide from Elliotte Rusty Harold's presentation on XLinks and XPointers to the XML SIG of the Object Developer's Group, August 25, 1999"></meta>

           <title><xsl:value-of select="title"/></title>         
           <script language="JAVASCRIPT"> 
              <xsl:text disable-output-escaping="yes">&lt;!-- </xsl:text>
              var isnav
              
              if (parseInt(navigator.appVersion) >= 4) {
                if (navigator.appName == "Netscape") {
                  isNav = true
                  document.captureEvents(Event.KEYPRESS)
                }
                else {
                  isNav = false
                }
              }
              document.onkeypress = flipslide

              function flipslide(evt) {
                var key = isNav ? evt.which : window.event.keyCode
                if (key == 32 || key == 29 || key == 30 || key == 11) {
                  <xsl:if test="position()!=last()">
                    location.href="onscreen<xsl:number value="position()+1" format="01"/>.html"
                  </xsl:if>
                }
                else if (key == 28 || key == 31 || key == 12) {
                  <xsl:if test="position()!=1">
                    location.href="onscreen<xsl:number value="position()-1" format="01"/>.html"
                  </xsl:if>
                  <xsl:if test="position()=1">
                    location.href="index.html"
                  </xsl:if>
                }
                else if (key == 1) {
                  location.href="index.html";
                }
              } // <xsl:text disable-output-escaping="yes"> --&gt;</xsl:text>             
           </script> 
         </head>
         <body>           
             <xsl:apply-templates/>
           <hr/>                  
           <!-- Need to treat first and last slide specially --> 
           <xsl:choose>
             <xsl:when test="position()=1">
               <div align="center">
                 <A HREF="onscreen{format-number(position()+1,'00')}.html">Next</A> | <A HREF="index.html">Top</A> | <A HREF="/xml/">Cafe con Leche</A>
               </div>
             </xsl:when>
             <xsl:when test="position()=last()">
               <div align="center">
                 <A HREF="onscreen01.html">Start</A> | <A HREF="onscreen{format-number(position()-1,'00')}.html">Previous</A> | <A HREF="/xml/">Cafe con Leche</A>
               </div>
             </xsl:when>
             <xsl:otherwise>
               <div align="center">
                 <A HREF="onscreen{format-number(position()-1,'00')}.html">Previous</A> | <A HREF="onscreen{format-number(position()+1,'00')}.html">Next</A> | 
                 <A HREF="index.html">Top</A> | <A HREF="/xml/">Cafe con Leche</A>
               </div>
             </xsl:otherwise>
           </xsl:choose>

           <hr/>
           <div style="font-size: x-small">
              Copyright 1999 
              <a href="http://www.macfaq.com/personal.html">Elliotte Rusty Harold</a><br/>       
              <a href="mailto:elharo@metalab.unc.edu">elharo@metalab.unc.edu</a><br/>
              Last Modified 
              <xsl:choose>
                <xsl:when test="last_modified">
                  <xsl:value-of select="last_modified" mode="lm"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="/presentation/default_last_modified"/>
                </xsl:otherwise>
              </xsl:choose>
           </div>
         </body>     
       </html>
     </xt:document>   
       
  </xsl:template>
    
  <xsl:template match="title">  
    <h1 align="center"><xsl:value-of select="."/></h1>
  </xsl:template>  
  
  <xsl:template match="last_modified"/>    

  <xsl:template match="last_modified" mode="lm">  
    <xsl:value-of select="."/>
  </xsl:template>  
  
  <xsl:template match="default_last_modified">  
    <xsl:value-of select="."/>
  </xsl:template>  
  
  <xsl:template match="li">  
    <li><p><xsl:apply-templates/></p></li>
  </xsl:template>  
  
  <!-- Ignore contents of notes when printing slides -->    
  <xsl:template match="note"/>  

  <!-- pass HTML along unchanged -->
  <xsl:template match="*|@*">
    <xsl:copy>
      <xsl:apply-templates select="*|@*|text()"/>
    </xsl:copy>
  </xsl:template>    
  
</xsl:stylesheet>
