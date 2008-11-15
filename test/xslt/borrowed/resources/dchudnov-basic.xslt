<?xml version="1.0"?>
<!-- Identify transformation -->
<xsl:stylesheet version="1.1"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="titlerecord">
    <xsl:variable name="refid" select="database/@jakeid"/>
    <xsl:text>
      </xsl:text>
    <xsl:comment> begin jakeid=<xsl:value-of select="$refid"/>
      </xsl:comment>
    <xsl:text>
      </xsl:text>
    <table border="0" width="100%" cellspacing="0" cellpadding="1" bgcolor="dddddd">
      <tr><td>
        <table border="0" width="100%" cellspacing="0" cellpadding="5" bgcolor="eeeeee">
          <tr><td>
            <b><xsl:value-of select="database/preferredtitle"/></b>
            <li type="circle">
              <font size="-1">jake id -
                <xsl:if test="titleinfo/@issn != ''">
                  , issn <b><xsl:value-of select="titleinfo/@issn"/></b>
                </xsl:if>
              </font>
            </li>
            <li type="circle">
              <font size="-1">referenced from:
                <a href="{$searchurl}?jakeid={$refid}&amp;searchurl={$searchurl}"><xsl:value-of select="database/title"/></a></font>
            </li>
          </td></tr>
        </table>
      </td></tr>
    </table>
    <xsl:text>
      </xsl:text>
    <xsl:comment> end jakeid=<xsl:value-of select="$refid"/>
      </xsl:comment>
  </xsl:template>


  <xsl:template match="authrecord">
    <table border="0" width="100%" cellspacing="0" cellpadding="1" bgcolor="dddddd">
      <tr><td>
        <table border="0" width="100%" cellspacing="0" cellpadding="5" bgcolor="eeeeee">
          <tr><td>
            <xsl:apply-templates select="title"/>
            <xsl:apply-templates select="id"/>
            <xsl:apply-templates select="serialinfo"/>
            <xsl:apply-templates select="databaseinfo"/>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </xsl:template>


  <xsl:template match="authrecord/title">
    <b><xsl:apply-templates/></b>
  </xsl:template>
 

  <xsl:template match="id">
    <li type="circle">
      <font size="-1">
        <xsl:text>jake id </xsl:text>
        <xsl:variable name="jakeid" select="@jakeid"/>
        <b><xsl:value-of select="$jakeid"/></b>
        <xsl:text>, type </xsl:text>
        <b><xsl:value-of select="@type"/></b>
        <xsl:if test="@type='serial'">
          <xsl:text>, issn </xsl:text>
          <b><xsl:value-of select="../serialinfo/@issn"/></b>
        </xsl:if>
      </font>
    </li>
  </xsl:template>


  <xsl:template match="databaseinfo">
    <xsl:variable name="jakeid" select="../id/@jakeid"/>
    <xsl:variable name="dbtitle" select="../title"/>
    <xsl:variable name="dbtitleencoded" select="translate( $dbtitle, ' ', '+' )"/>
    <li type="circle">
      <font size="-1">
        <xsl:text>titles: </xsl:text>
        <a href="http://jake.med.yale.edu/list.php3?type=xref&amp;jakeid={$jakeid}&amp;title={$dbtitleencoded}"><xsl:value-of select="titles/@xrefs"/></a>
        <xsl:text> of </xsl:text>
        <a href="http://jake.med.yale.edu/list.php3?type=list&amp;jakeid={$jakeid}&amp;title={$dbtitleencoded}"><xsl:value-of select="titles/@count"/></a>
        <xsl:text> (</xsl:text>
        <xsl:value-of select="round( 100 * ( titles/@xrefs div titles/@count ) )"/>
        <xsl:text>%) </xsl:text>
        <xsl:text> x-ref'd - click for lists</xsl:text>
      </font>
    </li>
    <xsl:if test="cites/@count>0">
      <li type="circle">
        <font size="-1">
          <xsl:text>titles w/citations: </xsl:text>
          <xsl:value-of select="cites/@count"/>
        </font>
      </li>
    </xsl:if>
    <xsl:if test="fulltext/@count>0">
      <li type="circle">
        <font size="-1">
          <xsl:text>titles w/fulltext: </xsl:text>
          <xsl:value-of select="fulltext/@count"/>
        </font>
      </li>
    </xsl:if>
    <xsl:if test="providers/@count>0">
      <li type="circle">
        <font size="-1">
          <xsl:text>provider: </xsl:text>
          <xsl:value-of select="providers/title"/>
        </font>
      </li>
    </xsl:if>
    <li type="circle">
      <font size="-1">
        <a href="http://hermes.lib.sfu.ca/cgi-bin/ejournals/jake/jake2marc.pl?jakeid={$jakeid}&amp;dbname={$dbtitleencoded}">download as MARC</a>
      </font>
    </li>

  </xsl:template>




  <xsl:template match="serialinfo">
    <xsl:variable name="citecount" select="count(../*/cites)"/>
    <xsl:variable name="ftcount" select="count(../*/fulltext)"/>
    <xsl:variable name="jakeid" select="../id/@jakeid"/>
    <xsl:variable name="title" select="translate( //request/terms, ' ', '+' )"/>
    <xsl:variable name="volume" select="//request/volume"/>
    <xsl:variable name="issue" select="//request/issue"/>
    <xsl:variable name="page" select="//request/page"/>
    <xsl:variable name="year" select="//request/year"/>
    <xsl:variable name="count" select="count( //results/authrecord ) + count( //results/titlerecord )"/>
    <font size="-1">
      <li type="circle"> indexed by <xsl:value-of select="$citecount"/> databases</li>
      <li type="circle"> fulltext in <xsl:value-of select="$ftcount"/> databases</li>
    </font>
    <xsl:choose>
      <xsl:when test="(/search/request/@type='jakeid') or ($count=1)">
        <xsl:apply-templates select="../subjects"/>
        <table border="0" width="100%" cellspacing="0" cellpadding="1" bgcolor="dddddd">
          <tr>
            <th width='20%' align='center'>links</th>
            <th width='35%' align='left'>resource</th>
            <th width='10%' align='left'>provider</th>
            <th align='left'>citations</th>
            <th align='left'>fulltext</th>
          </tr>
          <xsl:apply-templates select="../database"/>
        </table>
      </xsl:when>
      <xsl:otherwise>
        <font size="-1">
          <li type="circle">
            <xsl:choose>
              <xsl:when test="contains( $searchurl, '?' )">
                <a href="{$searchurl}&amp;jakeid={$jakeid}&amp;volume={$volume}&amp;issue={$issue}&amp;page={$page}&amp;year={$year}&amp;title={$title}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}">complete details</a>
              </xsl:when>
              <xsl:otherwise>
                <a href="{$searchurl}?jakeid={$jakeid}&amp;volume={$volume}&amp;issue={$issue}&amp;page={$page}&amp;year={$year}&amp;title={$title}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}">complete details</a>
              </xsl:otherwise>
            </xsl:choose>
          </li>
        </font>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="subjects">
    <font size="-1">
      <li type="circle">
        <xsl:text> subject/class.: </xsl:text>
        <ul>
          <xsl:apply-templates select="subject"/>
        </ul>
      </li>
    </font>
  </xsl:template>

  <xsl:template match="subject">
    <xsl:variable name="value" select="."/>
    <xsl:if test="@classtype='dewey'">
      <font size="-1">
        <li><a href="{$searchurl}?type=subject&amp;classtype=dewey&amp;value={$value}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}"><xsl:value-of select="$value"/></a> (dewey)</li>
      </font>
    </xsl:if>
    <xsl:if test="@classtype='lc'">
      <font size="-1">
        <li><a href="{$searchurl}?type=subject&amp;classtype=lc&amp;value={$value}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}"><xsl:value-of select="$value"/></a> (lc)</li>
      </font>
    </xsl:if>
    <xsl:if test="@classtype='lcsh'">
      <xsl:variable name="encodedvalue" select="translate( $value, ' ', '+' )"/>
      <font size="-1">
        <li><a href="{$searchurl}?type=subject&amp;classtype=lcsh&amp;value={$encodedvalue}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}"><xsl:value-of select="$value"/></a> (lcsh)</li>
      </font>
    </xsl:if>
  </xsl:template>


  <xsl:template match="database">
    <xsl:variable name="thisjakeid" select="@jakeid"/>
    <xsl:variable name="provid" select="providername/@jakeid"/>
    <xsl:text>
      </xsl:text>
    <xsl:comment> begin jakeid=<xsl:value-of select="$thisjakeid"/> 
      </xsl:comment>
    <xsl:text>
      </xsl:text>
        <tr>
          <td align="center">
            <font size="-1">
              <xsl:apply-templates select="fulltext/article"/>
            <xsl:text> . </xsl:text>
              <xsl:apply-templates select="fulltext/issuelist"/> 
            <xsl:text> . </xsl:text>
              <xsl:apply-templates select="fulltext/toc"/>
            <xsl:text> . </xsl:text>
              <xsl:apply-templates select="fulltext/currentissue"/>
            </font>
          </td>
          <td><font size="-1">
            <xsl:choose>
              <xsl:when test="contains( $searchurl, '?' )">
                <a href="{$searchurl}&amp;jakeid={$thisjakeid}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}"><xsl:value-of select="title"/></a>
              </xsl:when>
              <xsl:otherwise>
                <a href="{$searchurl}?jakeid={$thisjakeid}&amp;searchurl={$searchurl}&amp;dataurl={$dataurl}"><xsl:value-of select="title"/></a>
              </xsl:otherwise> 
            </xsl:choose>
          </font></td>
          <td><font size="-1">
              <a href="{$searchurl}?jakeid={$provid}&amp;searchurl={$searchurl}"><xsl:value-of select="providername"/></a>
              </font></td>
          <td>
            <font size="-1">
                <xsl:choose>
                <xsl:when test="boolean( cites )">
                        <xsl:choose>
                                <xsl:when test="( cites/start/@date != '' ) or
                                                ( cites/end/@date != '' )">
                                  <xsl:value-of select="cites/start/@date"/> -
                                  <xsl:value-of select="cites/end/@date"/>
                                </xsl:when>
                                <xsl:otherwise>
                                        <xsl:text>+</xsl:text>
                                </xsl:otherwise>
                        </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                        <xsl:text>-</xsl:text>
                </xsl:otherwise>
                </xsl:choose>
             </font>
          </td>
          <td>
            <font size="-1">
                <xsl:choose>
                <xsl:when test="boolean( fulltext )">
                        <xsl:choose>
                                <xsl:when test="( fulltext/start/@date != '' ) or
                                                ( fulltext/end/@date != '' )">  
                                  <xsl:value-of select="fulltext/start/@date"/> -
                                  <xsl:value-of select="fulltext/end/@date"/>
                                </xsl:when>
                                <xsl:otherwise>
                                        <xsl:text>+</xsl:text>
                                </xsl:otherwise>
                        </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                        <xsl:text>-</xsl:text>
                </xsl:otherwise>
                </xsl:choose>
            </font>
          </td>
        </tr>
    <xsl:text>
      </xsl:text>
    <xsl:comment> end jakeid=<xsl:value-of select="$thisjakeid"/>
      </xsl:comment>
  </xsl:template>

  <xsl:template match="article">
    <xsl:choose>
      <xsl:when test="boolean( urlpattern )">
        <xsl:apply-templates select="urlpattern">
          <xsl:with-param name="context" select="'article'"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="url" select="."/>
        <a href="{$url}">article</a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="issuelist">
    <xsl:choose>
      <xsl:when test="boolean( urlpattern )">
        <xsl:apply-templates select="urlpattern">
          <xsl:with-param name="context" select="'issuelist'"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="url" select="."/>
        <a href="{$url}">issuelist</a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="toc">
    <xsl:choose>
      <xsl:when test="boolean( urlpattern )">
        <xsl:apply-templates select="urlpattern">
          <xsl:with-param name="context" select="'toc'"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="url" select="."/>
        <a href="{$url}">toc</a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="currentissue">
    <xsl:choose>
      <xsl:when test="boolean( urlpattern )">
        <xsl:apply-templates select="urlpattern">
          <xsl:with-param name="context" select="'current'"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="url" select="."/>
        <a href="{$url}">current</a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>



</xsl:stylesheet>
