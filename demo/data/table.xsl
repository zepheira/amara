<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:stbl="http://nwalsh.com/xslt/ext/com.nwalsh.saxon.Table"
                xmlns:xtbl="com.nwalsh.xalan.Table"
                xmlns:ptbl="http://nwalsh.com/xslt/ext/xsltproc/python/Table"
                exclude-result-prefixes="stbl xtbl ptbl"
                version='1.0'>

<!-- ********************************************************************

     This file is part of the XSL DocBook Stylesheet distribution.
     See ../README or http://nwalsh.com/docbook/xsl/ for copyright
     and other information.

     ******************************************************************** -->

<!-- ********************************************************************
     Modifications from original DocBook Stylesheet distribution:
     - combined html/table.xsl and common/table.xsl
     - removed the elements not defined in Simplified DocBook
     - removed support for dbhtml PIs
     - changed footnote template from apply-templates with mode to a
       call-template from the 4Suite Simplified DocBook stylesheet.
     ******************************************************************** -->
    
<xsl:param name="use.extensions" select="0"/>
<xsl:param name="tablecolumns.extension" select="0"/>
<xsl:param name="entry.propagates.style" select="1"/>
<xsl:param name="show.revisionflag" select="0"/>
<xsl:param name="table.borders.with.css" select="1"/>
<xsl:param name="table.cell.border.color" select="''"/>
<xsl:param name="table.cell.border.style" select="'solid'"/>
<xsl:param name="table.cell.border.thickness" select="'0.5pt'"/>
<xsl:param name="table.frame.border.color" select="''"/>
<xsl:param name="table.frame.border.style" select="'solid'"/>
<xsl:param name="table.frame.border.thickness" select="'0.5pt'"/>

<!-- ********************************************************************
     html/html.xsl
     ******************************************************************** -->

<xsl:template name="anchor">
  <xsl:param name="node" select="."/>
  <xsl:if test="$node/@id">
    <a name="{@id}"/>
  </xsl:if>
</xsl:template>

<!-- ********************************************************************
     common/table.xsl
     ******************************************************************** -->

<xsl:template name="blank.spans">
  <xsl:param name="cols" select="1"/>
  <xsl:if test="$cols &gt; 0">
    <xsl:text>0:</xsl:text>
    <xsl:call-template name="blank.spans">
      <xsl:with-param name="cols" select="$cols - 1"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template name="calculate.following.spans">
  <xsl:param name="colspan" select="1"/>
  <xsl:param name="spans" select="''"/>

  <xsl:choose>
    <xsl:when test="$colspan &gt; 0">
      <xsl:call-template name="calculate.following.spans">
        <xsl:with-param name="colspan" select="$colspan - 1"/>
        <xsl:with-param name="spans" select="substring-after($spans,':')"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$spans"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="finaltd">
  <xsl:param name="spans"/>
  <xsl:param name="col" select="0"/>

  <xsl:if test="$spans != ''">
    <xsl:choose>
      <xsl:when test="starts-with($spans,'0:')">
        <xsl:call-template name="empty.table.cell">
          <xsl:with-param name="colnum" select="$col"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise></xsl:otherwise>
    </xsl:choose>

    <xsl:call-template name="finaltd">
      <xsl:with-param name="spans" select="substring-after($spans,':')"/>
      <xsl:with-param name="col" select="$col+1"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template name="sfinaltd">
  <xsl:param name="spans"/>

  <xsl:if test="$spans != ''">
    <xsl:choose>
      <xsl:when test="starts-with($spans,'0:')">0:</xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="substring-before($spans,':')-1"/>
        <xsl:text>:</xsl:text>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:call-template name="sfinaltd">
      <xsl:with-param name="spans" select="substring-after($spans,':')"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template name="entry.colnum">
  <xsl:param name="entry" select="."/>

  <xsl:choose>
    <xsl:when test="$entry/@spanname">
      <xsl:variable name="spanname" select="$entry/@spanname"/>
      <xsl:variable name="spanspec"
                    select="$entry/ancestor::tgroup/spanspec[@spanname=$spanname]"/>
      <xsl:variable name="colspec"
                    select="$entry/ancestor::tgroup/colspec[@colname=$spanspec/@namest]"/>
      <xsl:call-template name="colspec.colnum">
        <xsl:with-param name="colspec" select="$colspec"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$entry/@colname">
      <xsl:variable name="colname" select="$entry/@colname"/>
      <xsl:variable name="colspec"
                    select="$entry/ancestor::tgroup/colspec[@colname=$colname]"/>
      <xsl:call-template name="colspec.colnum">
        <xsl:with-param name="colspec" select="$colspec"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$entry/@namest">
      <xsl:variable name="namest" select="$entry/@namest"/>
      <xsl:variable name="colspec"
                    select="$entry/ancestor::tgroup/colspec[@colname=$namest]"/>
      <xsl:call-template name="colspec.colnum">
        <xsl:with-param name="colspec" select="$colspec"/>
      </xsl:call-template>
    </xsl:when>
    <!-- no idea, return 0 -->
    <xsl:otherwise>0</xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="colspec.colnum">
  <xsl:param name="colspec" select="."/>
  <xsl:choose>
    <xsl:when test="$colspec/@colnum">
      <xsl:value-of select="$colspec/@colnum"/>
    </xsl:when>
    <xsl:when test="$colspec/preceding-sibling::colspec">
      <xsl:variable name="prec.colspec.colnum">
        <xsl:call-template name="colspec.colnum">
          <xsl:with-param name="colspec"
                          select="$colspec/preceding-sibling::colspec[1]"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:value-of select="$prec.colspec.colnum + 1"/>
    </xsl:when>
    <xsl:otherwise>1</xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="calculate.colspan">
  <xsl:param name="entry" select="."/>
  <xsl:variable name="spanname" select="$entry/@spanname"/>
  <xsl:variable name="spanspec"
                select="$entry/ancestor::tgroup/spanspec[@spanname=$spanname]"/>

  <xsl:variable name="namest">
    <xsl:choose>
      <xsl:when test="@spanname">
        <xsl:value-of select="$spanspec/@namest"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$entry/@namest"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="nameend">
    <xsl:choose>
      <xsl:when test="@spanname">
        <xsl:value-of select="$spanspec/@nameend"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$entry/@nameend"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="scol">
    <xsl:call-template name="colspec.colnum">
      <xsl:with-param name="colspec"
                      select="$entry/ancestor::tgroup/colspec[@colname=$namest]"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="ecol">
    <xsl:call-template name="colspec.colnum">
      <xsl:with-param name="colspec"
                      select="$entry/ancestor::tgroup/colspec[@colname=$nameend]"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:choose>
    <xsl:when test="$namest != '' and $nameend != ''">
      <xsl:choose>
        <xsl:when test="$ecol &gt;= $scol">
          <xsl:value-of select="$ecol - $scol + 1"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$scol - $ecol + 1"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>1</xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="calculate.rowsep">
  <xsl:param name="entry" select="."/>
  <xsl:param name="colnum" select="0"/>

  <xsl:call-template name="inherited.table.attribute">
    <xsl:with-param name="entry" select="$entry"/>
    <xsl:with-param name="colnum" select="$colnum"/>
    <xsl:with-param name="attribute" select="'rowsep'"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="calculate.colsep">
  <xsl:param name="entry" select="."/>
  <xsl:param name="colnum" select="0"/>

  <xsl:call-template name="inherited.table.attribute">
    <xsl:with-param name="entry" select="$entry"/>
    <xsl:with-param name="colnum" select="$colnum"/>
    <xsl:with-param name="attribute" select="'colsep'"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="inherited.table.attribute">
  <xsl:param name="entry" select="."/>
  <xsl:param name="row" select="$entry/ancestor-or-self::row[1]"/>
  <xsl:param name="colnum" select="0"/>
  <xsl:param name="attribute" select="'colsep'"/>

  <xsl:variable name="tgroup" select="$row/ancestor::tgroup[1]"/>

  <xsl:variable name="table" select="($tgroup/ancestor::table
                                     |$tgroup/ancestor::informaltable)[1]"/>

  <xsl:variable name="entry.value">
    <xsl:call-template name="get-attribute">
      <xsl:with-param name="element" select="$entry"/>
      <xsl:with-param name="attribute" select="$attribute"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="row.value">
    <xsl:call-template name="get-attribute">
      <xsl:with-param name="element" select="$row"/>
      <xsl:with-param name="attribute" select="$attribute"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="span.value">
    <xsl:if test="$entry/@spanname">
      <xsl:variable name="spanname" select="$entry/@spanname"/>
      <xsl:variable name="spanspec"
                    select="$tgroup/spanspec[@spanname=$spanname]"/>
      <xsl:variable name="span.colspec"
                    select="$tgroup/colspec[@colname=$spanspec/@namest]"/>

      <xsl:variable name="spanspec.value">
        <xsl:call-template name="get-attribute">
          <xsl:with-param name="element" select="$spanspec"/>
          <xsl:with-param name="attribute" select="$attribute"/>
        </xsl:call-template>
      </xsl:variable>

      <xsl:variable name="scolspec.value">
        <xsl:call-template name="get-attribute">
          <xsl:with-param name="element" select="$span.colspec"/>
          <xsl:with-param name="attribute" select="$attribute"/>
        </xsl:call-template>
      </xsl:variable>

      <xsl:choose>
        <xsl:when test="$spanspec.value != ''">
          <xsl:value-of select="$spanspec.value"/>
        </xsl:when>
        <xsl:when test="$scolspec.value != ''">
          <xsl:value-of select="$scolspec.value"/>
        </xsl:when>
        <xsl:otherwise></xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:variable>

  <xsl:variable name="namest.value">
    <xsl:if test="$entry/@namest">
      <xsl:variable name="namest" select="$entry/@namest"/>
      <xsl:variable name="colspec"
                    select="$tgroup/colspec[@colname=$namest]"/>

      <xsl:variable name="inner.namest.value">
        <xsl:call-template name="get-attribute">
          <xsl:with-param name="element" select="$colspec"/>
          <xsl:with-param name="attribute" select="$attribute"/>
        </xsl:call-template>
      </xsl:variable>

      <xsl:choose>
        <xsl:when test="$inner.namest.value">
          <xsl:value-of select="$inner.namest.value"/>
        </xsl:when>
        <xsl:otherwise></xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:variable>

  <xsl:variable name="tgroup.value">
    <xsl:call-template name="get-attribute">
      <xsl:with-param name="element" select="$tgroup"/>
      <xsl:with-param name="attribute" select="$attribute"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="table.value">
    <xsl:call-template name="get-attribute">
      <xsl:with-param name="element" select="$table"/>
      <xsl:with-param name="attribute" select="$attribute"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="default.value">
    <!-- This section used to say that rowsep and colsep have defaults based -->
    <!-- on the frame setting. Further reflection and closer examination of the -->
    <!-- CALS spec reveals I was mistaken. The default is "1" for rowsep and colsep. -->
    <!-- For everything else, the default is the tgroup value -->
    <xsl:choose>
      <xsl:when test="$tgroup.value != ''">
        <xsl:value-of select="$tgroup.value"/>
      </xsl:when>
      <xsl:when test="$attribute = 'rowsep'">1</xsl:when>
      <xsl:when test="$attribute = 'colsep'">1</xsl:when>
      <xsl:otherwise><!-- empty --></xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:choose>
    <xsl:when test="$entry.value != ''">
      <xsl:value-of select="$entry.value"/>
    </xsl:when>
    <xsl:when test="$row.value != ''">
      <xsl:value-of select="$row.value"/>
    </xsl:when>
    <xsl:when test="$tgroup.value != ''">
      <xsl:value-of select="$tgroup.value"/>
    </xsl:when>
    <xsl:when test="$table.value != ''">
      <xsl:value-of select="$table.value"/>
    </xsl:when>
    <xsl:when test="$span.value != ''">
      <xsl:value-of select="$span.value"/>
    </xsl:when>
    <xsl:when test="$namest.value != ''">
      <xsl:value-of select="$namest.value"/>
    </xsl:when>
    <xsl:when test="$colnum &gt; 0">
      <xsl:variable name="calc.colvalue">
        <xsl:call-template name="colnum.colspec">
          <xsl:with-param name="colnum" select="$colnum"/>
          <xsl:with-param name="attribute" select="$attribute"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$calc.colvalue != ''">
          <xsl:value-of select="$calc.colvalue"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$default.value"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$default.value"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="colnum.colspec">
  <xsl:param name="colnum" select="0"/>
  <xsl:param name="attribute" select="'colname'"/>
  <xsl:param name="colspecs" select="ancestor::tgroup/colspec"/>
  <xsl:param name="count" select="1"/>

  <xsl:choose>
    <xsl:when test="not($colspecs) or $count &gt; $colnum">
      <!-- nop -->
    </xsl:when>
    <xsl:when test="$colspecs[1]/@colnum">
      <xsl:choose>
        <xsl:when test="$colspecs[1]/@colnum = $colnum">
          <xsl:call-template name="get-attribute">
            <xsl:with-param name="element" select="$colspecs[1]"/>
            <xsl:with-param name="attribute" select="$attribute"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="colnum.colspec">
            <xsl:with-param name="colnum" select="$colnum"/>
            <xsl:with-param name="attribute" select="$attribute"/>
            <xsl:with-param name="colspecs"
                            select="$colspecs[position()&gt;1]"/>
            <xsl:with-param name="count"
                            select="$colspecs[1]/@colnum+1"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:choose>
        <xsl:when test="$count = $colnum">
          <xsl:call-template name="get-attribute">
            <xsl:with-param name="element" select="$colspecs[1]"/>
            <xsl:with-param name="attribute" select="$attribute"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="colnum.colspec">
            <xsl:with-param name="colnum" select="$colnum"/>
            <xsl:with-param name="attribute" select="$attribute"/>
            <xsl:with-param name="colspecs"
                            select="$colspecs[position()&gt;1]"/>
            <xsl:with-param name="count" select="$count+1"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="get-attribute">
  <xsl:param name="element" select="."/>
  <xsl:param name="attribute" select="''"/>

  <xsl:for-each select="$element/@*">
    <xsl:if test="local-name(.) = $attribute">
      <xsl:value-of select="."/>
    </xsl:if>
  </xsl:for-each>
</xsl:template>

<!-- ********************************************************************
     html/table.xsl
     ******************************************************************** -->

<xsl:template name="empty.table.cell">
  <xsl:param name="colnum" select="0"/>

  <xsl:variable name="rowsep">
    <xsl:choose>
      <!-- If this is the last row, rowsep never applies. -->
      <xsl:when test="not(ancestor-or-self::row[1]/following-sibling::row
                          or ancestor-or-self::thead/following-sibling::tbody
                          or ancestor-or-self::tbody/preceding-sibling::tfoot)">
        <xsl:value-of select="0"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inherited.table.attribute">
          <xsl:with-param name="entry" select="NOT-AN-ELEMENT-NAME"/>
          <xsl:with-param name="row" select="ancestor-or-self::row[1]"/>
          <xsl:with-param name="colnum" select="$colnum"/>
          <xsl:with-param name="attribute" select="'rowsep'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="colsep">
    <xsl:choose>
      <!-- If this is the last column, colsep never applies. -->
      <xsl:when test="$colnum &gt;= ancestor::tgroup/@cols">0</xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inherited.table.attribute">
          <xsl:with-param name="entry" select="NOT-AN-ELEMENT-NAME"/>
          <xsl:with-param name="row" select="ancestor-or-self::row[1]"/>
          <xsl:with-param name="colnum" select="$colnum"/>
          <xsl:with-param name="attribute" select="'colsep'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <td class="auto-generated">
    <xsl:if test="$table.borders.with.css != 0">
      <xsl:attribute name="style">
        <xsl:if test="$colsep &gt; 0">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'right'"/>
          </xsl:call-template>
        </xsl:if>
        <xsl:if test="$rowsep &gt; 0">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'bottom'"/>
          </xsl:call-template>
        </xsl:if>
      </xsl:attribute>
    </xsl:if>
    <xsl:text>&#160;</xsl:text>
  </td>
</xsl:template>

<!-- ==================================================================== -->

<xsl:template name="border">
  <xsl:param name="side" select="'left'"/>
  <xsl:param name="padding" select="0"/>
  <xsl:param name="style" select="$table.cell.border.style"/>
  <xsl:param name="color" select="$table.cell.border.color"/>
  <xsl:param name="thickness" select="$table.cell.border.thickness"/>

  <!-- Note: Some browsers (mozilla) require at least a width and style. -->

  <xsl:choose>
    <xsl:when test="($thickness != ''
                     and $style != ''
                     and $color != '')
                    or ($thickness != ''
                        and $style != '')
                    or ($thickness != '')">
      <!-- use the compound property if we can: -->
      <!-- it saves space and probably works more reliably -->
      <xsl:text>border-</xsl:text>
      <xsl:value-of select="$side"/>
      <xsl:text>: </xsl:text>
      <xsl:value-of select="$thickness"/>
      <xsl:text> </xsl:text>
      <xsl:value-of select="$style"/>
      <xsl:text> </xsl:text>
      <xsl:value-of select="$color"/>
      <xsl:text>; </xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <!-- we need to specify the styles individually -->
      <xsl:if test="$thickness != ''">
        <xsl:text>border-</xsl:text>
        <xsl:value-of select="$side"/>
        <xsl:text>-width: </xsl:text>
        <xsl:value-of select="$thickness"/>
        <xsl:text>; </xsl:text>
      </xsl:if>

      <xsl:if test="$style != ''">
        <xsl:text>border-</xsl:text>
        <xsl:value-of select="$side"/>
        <xsl:text>-style: </xsl:text>
        <xsl:value-of select="$style"/>
        <xsl:text>; </xsl:text>
      </xsl:if>

      <xsl:if test="$color != ''">
        <xsl:text>border-</xsl:text>
        <xsl:value-of select="$side"/>
        <xsl:text>-color: </xsl:text>
        <xsl:value-of select="$color"/>
        <xsl:text>; </xsl:text>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- ==================================================================== -->

<xsl:template match="tgroup" name="tgroup">
  <xsl:if test="not(@cols)">
    <xsl:message terminate="yes">
      <xsl:text>Error: CALS tables must specify the number of columns.</xsl:text>
    </xsl:message>
  </xsl:if>

  <table>
    <xsl:choose>
      <!-- If there's a textobject/phrase for the table summary, use it -->
      <xsl:when test="../textobject/phrase">
        <xsl:attribute name="summary">
          <xsl:value-of select="../textobject/phrase"/>
        </xsl:attribute>
      </xsl:when>

      <!-- Otherwise, if there's a title, use that -->
      <xsl:when test="../title">
        <xsl:attribute name="summary">
          <xsl:value-of select="string(../title)"/>
        </xsl:attribute>
      </xsl:when>

      <!-- Otherwise, forget the whole idea -->
      <xsl:otherwise><!-- nevermind --></xsl:otherwise>
    </xsl:choose>

    <xsl:if test="../@pgwide=1 or local-name(.) = 'entrytbl'">
      <xsl:attribute name="width">100%</xsl:attribute>
    </xsl:if>

    <xsl:choose>
      <xsl:when test="$table.borders.with.css != 0">
        <xsl:attribute name="border">0</xsl:attribute>
        <xsl:choose>
          <xsl:when test="../@frame='all'">
            <xsl:attribute name="style">
              <xsl:text>border-collapse: collapse;</xsl:text>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'top'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'bottom'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'left'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'right'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
            </xsl:attribute>
          </xsl:when>
          <xsl:when test="../@frame='topbot'">
            <xsl:attribute name="style">
              <xsl:text>border-collapse: collapse;</xsl:text>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'top'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'bottom'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
            </xsl:attribute>
          </xsl:when>
          <xsl:when test="../@frame='top'">
            <xsl:attribute name="style">
              <xsl:text>border-collapse: collapse;</xsl:text>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'top'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
            </xsl:attribute>
          </xsl:when>
          <xsl:when test="../@frame='bottom'">
            <xsl:attribute name="style">
              <xsl:text>border-collapse: collapse;</xsl:text>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'bottom'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
            </xsl:attribute>
          </xsl:when>
          <xsl:when test="../@frame='sides'">
            <xsl:attribute name="style">
              <xsl:text>border-collapse: collapse;</xsl:text>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'left'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'right'"/>
                <xsl:with-param name="style" select="$table.frame.border.style"/>
                <xsl:with-param name="color" select="$table.frame.border.color"/>
                <xsl:with-param name="thickness" select="$table.frame.border.thickness"/>
              </xsl:call-template>
            </xsl:attribute>
          </xsl:when>
          <xsl:otherwise>
            <xsl:attribute name="style">
              <xsl:text>border-collapse: collapse;</xsl:text>
            </xsl:attribute>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="../@frame='none' or local-name(.) = 'entrytbl'">
        <xsl:attribute name="border">0</xsl:attribute>
      </xsl:when>
      <xsl:otherwise>
        <xsl:attribute name="border">1</xsl:attribute>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:variable name="colgroup">
      <colgroup>
        <xsl:call-template name="generate.colgroup">
          <xsl:with-param name="cols" select="@cols"/>
        </xsl:call-template>
      </colgroup>
    </xsl:variable>

    <xsl:choose>
      <xsl:when test="$use.extensions != 0
                      and $tablecolumns.extension != 0">
        <xsl:choose>
          <xsl:when test="function-available('stbl:adjustColumnWidths')">
            <xsl:copy-of select="stbl:adjustColumnWidths($colgroup)"/>
          </xsl:when>
          <xsl:when test="function-available('xtbl:adjustColumnWidths')">
            <xsl:copy-of select="xtbl:adjustColumnWidths($colgroup)"/>
          </xsl:when>
          <xsl:when test="function-available('ptbl:adjustColumnWidths')">
            <xsl:copy-of select="ptbl:adjustColumnWidths($colgroup)"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:message terminate="yes">
              <xsl:text>No adjustColumnWidths function available.</xsl:text>
            </xsl:message>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:copy-of select="$colgroup"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:apply-templates select="thead"/>
    <xsl:apply-templates select="tfoot"/>
    <xsl:apply-templates select="tbody"/>

    <xsl:if test=".//footnote">
      <tbody class="footnotes">
        <tr>
          <td colspan="{@cols}">
            <xsl:call-template name="display.footnotes"/>
          </td>
        </tr>
      </tbody>
    </xsl:if>
  </table>
</xsl:template>

<xsl:template match="colspec"></xsl:template>

<xsl:template match="spanspec"></xsl:template>

<xsl:template match="thead|tfoot">
  <xsl:element name="{name(.)}">
    <xsl:if test="@align">
      <xsl:attribute name="align">
        <xsl:value-of select="@align"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@char">
      <xsl:attribute name="char">
        <xsl:value-of select="@char"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@charoff">
      <xsl:attribute name="charoff">
        <xsl:value-of select="@charoff"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@valign">
      <xsl:attribute name="valign">
        <xsl:value-of select="@valign"/>
      </xsl:attribute>
    </xsl:if>

    <xsl:apply-templates select="row[1]">
      <xsl:with-param name="spans">
        <xsl:call-template name="blank.spans">
          <xsl:with-param name="cols" select="../@cols"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>

  </xsl:element>
</xsl:template>

<xsl:template match="tbody">
  <tbody>
    <xsl:if test="@align">
      <xsl:attribute name="align">
        <xsl:value-of select="@align"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@char">
      <xsl:attribute name="char">
        <xsl:value-of select="@char"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@charoff">
      <xsl:attribute name="charoff">
        <xsl:value-of select="@charoff"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@valign">
      <xsl:attribute name="valign">
        <xsl:value-of select="@valign"/>
      </xsl:attribute>
    </xsl:if>

    <xsl:apply-templates select="row[1]">
      <xsl:with-param name="spans">
        <xsl:call-template name="blank.spans">
          <xsl:with-param name="cols" select="../@cols"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>

  </tbody>
</xsl:template>

<xsl:template match="row">
  <xsl:param name="spans"/>

  <tr>
    <xsl:call-template name="tr.attributes">
      <xsl:with-param name="rownum">
        <xsl:number from="tgroup" count="row"/>
      </xsl:with-param>
    </xsl:call-template>

    <xsl:if test="$table.borders.with.css != 0">
      <xsl:if test="@rowsep = 1 and following-sibling::row">
        <xsl:attribute name="style">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'bottom'"/>
          </xsl:call-template>
        </xsl:attribute>
      </xsl:if>
    </xsl:if>

    <xsl:if test="@align">
      <xsl:attribute name="align">
        <xsl:value-of select="@align"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@char">
      <xsl:attribute name="char">
        <xsl:value-of select="@char"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@charoff">
      <xsl:attribute name="charoff">
        <xsl:value-of select="@charoff"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@valign">
      <xsl:attribute name="valign">
        <xsl:value-of select="@valign"/>
      </xsl:attribute>
    </xsl:if>

    <xsl:apply-templates select="(entry|entrytbl)[1]">
      <xsl:with-param name="spans" select="$spans"/>
    </xsl:apply-templates>
  </tr>

  <xsl:if test="following-sibling::row">
    <xsl:variable name="nextspans">
      <xsl:apply-templates select="(entry|entrytbl)[1]" mode="span">
        <xsl:with-param name="spans" select="$spans"/>
      </xsl:apply-templates>
    </xsl:variable>

    <xsl:apply-templates select="following-sibling::row[1]">
      <xsl:with-param name="spans" select="$nextspans"/>
    </xsl:apply-templates>
  </xsl:if>
</xsl:template>

<xsl:template match="entry|entrytbl" name="entry">
  <xsl:param name="col" select="1"/>
  <xsl:param name="spans"/>

  <xsl:variable name="cellgi">
    <xsl:choose>
      <xsl:when test="ancestor::thead">th</xsl:when>
      <xsl:when test="ancestor::tfoot">th</xsl:when>
      <xsl:otherwise>td</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="empty.cell" select="count(node()) = 0"/>

  <xsl:variable name="named.colnum">
    <xsl:call-template name="entry.colnum"/>
  </xsl:variable>

  <xsl:variable name="entry.colnum">
    <xsl:choose>
      <xsl:when test="$named.colnum &gt; 0">
        <xsl:value-of select="$named.colnum"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$col"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="entry.colspan">
    <xsl:choose>
      <xsl:when test="@spanname or @namest">
        <xsl:call-template name="calculate.colspan"/>
      </xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="following.spans">
    <xsl:call-template name="calculate.following.spans">
      <xsl:with-param name="colspan" select="$entry.colspan"/>
      <xsl:with-param name="spans" select="$spans"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="rowsep">
    <xsl:choose>
      <!-- If this is the last row, rowsep never applies. -->
      <xsl:when test="ancestor::entrytbl
                      and not (ancestor-or-self::row[1]/following-sibling::row)">
        <xsl:value-of select="0"/>
      </xsl:when>
      <xsl:when test="not(ancestor-or-self::row[1]/following-sibling::row
                          or ancestor-or-self::thead/following-sibling::tbody
                          or ancestor-or-self::tbody/preceding-sibling::tfoot)">
        <xsl:value-of select="0"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inherited.table.attribute">
          <xsl:with-param name="entry" select="."/>
          <xsl:with-param name="colnum" select="$entry.colnum"/>
          <xsl:with-param name="attribute" select="'rowsep'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="colsep">
    <xsl:choose>
      <!-- If this is the last column, colsep never applies. -->
      <xsl:when test="$following.spans = ''">0</xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inherited.table.attribute">
          <xsl:with-param name="entry" select="."/>
          <xsl:with-param name="colnum" select="$entry.colnum"/>
          <xsl:with-param name="attribute" select="'colsep'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="valign">
    <xsl:call-template name="inherited.table.attribute">
      <xsl:with-param name="entry" select="."/>
      <xsl:with-param name="colnum" select="$entry.colnum"/>
      <xsl:with-param name="attribute" select="'valign'"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="align">
    <xsl:call-template name="inherited.table.attribute">
      <xsl:with-param name="entry" select="."/>
      <xsl:with-param name="colnum" select="$entry.colnum"/>
      <xsl:with-param name="attribute" select="'align'"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="char">
    <xsl:call-template name="inherited.table.attribute">
      <xsl:with-param name="entry" select="."/>
      <xsl:with-param name="colnum" select="$entry.colnum"/>
      <xsl:with-param name="attribute" select="'char'"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="charoff">
    <xsl:call-template name="inherited.table.attribute">
      <xsl:with-param name="entry" select="."/>
      <xsl:with-param name="colnum" select="$entry.colnum"/>
      <xsl:with-param name="attribute" select="'charoff'"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:choose>
    <xsl:when test="$spans != '' and not(starts-with($spans,'0:'))">
      <xsl:call-template name="entry">
        <xsl:with-param name="col" select="$col+1"/>
        <xsl:with-param name="spans" select="substring-after($spans,':')"/>
      </xsl:call-template>
    </xsl:when>

    <xsl:when test="$entry.colnum &gt; $col">
      <xsl:call-template name="empty.table.cell"/>
      <xsl:call-template name="entry">
        <xsl:with-param name="col" select="$col+1"/>
        <xsl:with-param name="spans" select="substring-after($spans,':')"/>
      </xsl:call-template>
    </xsl:when>

    <xsl:otherwise>
      <xsl:element name="{$cellgi}">
        <xsl:if test="$entry.propagates.style != 0 and @role">
          <xsl:attribute name="class">
            <xsl:value-of select="@role"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$show.revisionflag and @revisionflag">
          <xsl:attribute name="class">
            <xsl:value-of select="@revisionflag"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$table.borders.with.css != 0">
          <xsl:attribute name="style">
            <xsl:if test="$colsep &gt; 0">
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'right'"/>
              </xsl:call-template>
            </xsl:if>
            <xsl:if test="$rowsep &gt; 0">
              <xsl:call-template name="border">
                <xsl:with-param name="side" select="'bottom'"/>
              </xsl:call-template>
            </xsl:if>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="@morerows &gt; 0">
          <xsl:attribute name="rowspan">
            <xsl:value-of select="1+@morerows"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$entry.colspan &gt; 1">
          <xsl:attribute name="colspan">
            <xsl:value-of select="$entry.colspan"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$align != ''">
          <xsl:attribute name="align">
            <xsl:value-of select="$align"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$valign != ''">
          <xsl:attribute name="valign">
            <xsl:value-of select="$valign"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$char != ''">
          <xsl:attribute name="char">
            <xsl:value-of select="$char"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$charoff != ''">
          <xsl:attribute name="charoff">
            <xsl:value-of select="$charoff"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="not(preceding-sibling::*) and ancestor::row/@id">
          <xsl:call-template name="anchor">
            <xsl:with-param name="node" select="ancestor::row[1]"/>
          </xsl:call-template>
        </xsl:if>

        <xsl:call-template name="anchor"/>

        <xsl:choose>
          <xsl:when test="$empty.cell">
            <xsl:text>&#160;</xsl:text>
          </xsl:when>
          <xsl:when test="self::entrytbl">
            <xsl:call-template name="tgroup"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:element>

      <xsl:choose>
        <xsl:when test="following-sibling::entry|following-sibling::entrytbl">
          <xsl:apply-templates select="(following-sibling::entry
                                       |following-sibling::entrytbl)[1]">
            <xsl:with-param name="col" select="$col+$entry.colspan"/>
            <xsl:with-param name="spans" select="$following.spans"/>
          </xsl:apply-templates>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="finaltd">
            <xsl:with-param name="spans" select="$following.spans"/>
            <xsl:with-param name="col" select="$col+$entry.colspan"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template match="entry|entrytbl" name="sentry" mode="span">
  <xsl:param name="col" select="1"/>
  <xsl:param name="spans"/>

  <xsl:variable name="entry.colnum">
    <xsl:call-template name="entry.colnum"/>
  </xsl:variable>

  <xsl:variable name="entry.colspan">
    <xsl:choose>
      <xsl:when test="@spanname or @namest">
        <xsl:call-template name="calculate.colspan"/>
      </xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="following.spans">
    <xsl:call-template name="calculate.following.spans">
      <xsl:with-param name="colspan" select="$entry.colspan"/>
      <xsl:with-param name="spans" select="$spans"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:choose>
    <xsl:when test="$spans != '' and not(starts-with($spans,'0:'))">
      <xsl:value-of select="substring-before($spans,':')-1"/>
      <xsl:text>:</xsl:text>
      <xsl:call-template name="sentry">
        <xsl:with-param name="col" select="$col+1"/>
        <xsl:with-param name="spans" select="substring-after($spans,':')"/>
      </xsl:call-template>
    </xsl:when>

    <xsl:when test="$entry.colnum &gt; $col">
      <xsl:text>0:</xsl:text>
      <xsl:call-template name="sentry">
        <xsl:with-param name="col" select="$col+$entry.colspan"/>
        <xsl:with-param name="spans" select="$following.spans"/>
      </xsl:call-template>
    </xsl:when>

    <xsl:otherwise>
      <xsl:call-template name="copy-string">
        <xsl:with-param name="count" select="$entry.colspan"/>
        <xsl:with-param name="string">
          <xsl:choose>
            <xsl:when test="@morerows">
              <xsl:value-of select="@morerows"/>
            </xsl:when>
            <xsl:otherwise>0</xsl:otherwise>
          </xsl:choose>
          <xsl:text>:</xsl:text>
        </xsl:with-param>
      </xsl:call-template>

      <xsl:choose>
        <xsl:when test="following-sibling::entry|following-sibling::entrytbl">
          <xsl:apply-templates select="(following-sibling::entry
                                        |following-sibling::entrytbl)[1]"
                               mode="span">
            <xsl:with-param name="col" select="$col+$entry.colspan"/>
            <xsl:with-param name="spans" select="$following.spans"/>
          </xsl:apply-templates>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="sfinaltd">
            <xsl:with-param name="spans" select="$following.spans"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="generate.colgroup">
  <xsl:param name="cols" select="1"/>
  <xsl:param name="count" select="1"/>
  <xsl:choose>
    <xsl:when test="$count &gt; $cols"></xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="generate.col">
        <xsl:with-param name="countcol" select="$count"/>
      </xsl:call-template>
      <xsl:call-template name="generate.colgroup">
        <xsl:with-param name="cols" select="$cols"/>
        <xsl:with-param name="count" select="$count+1"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="generate.col">
  <xsl:param name="countcol">1</xsl:param>
  <xsl:param name="colspecs" select="./colspec"/>
  <xsl:param name="count">1</xsl:param>
  <xsl:param name="colnum">1</xsl:param>

  <xsl:choose>
    <xsl:when test="$count>count($colspecs)">
      <col/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:variable name="colspec" select="$colspecs[$count=position()]"/>
      <xsl:variable name="colspec.colnum">
        <xsl:choose>
          <xsl:when test="$colspec/@colnum">
            <xsl:value-of select="$colspec/@colnum"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$colnum"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <xsl:choose>
        <xsl:when test="$colspec.colnum=$countcol">
          <col>
            <xsl:if test="$colspec/@colwidth
                          and $use.extensions != 0
                          and $tablecolumns.extension != 0">
              <xsl:attribute name="width">
	        <xsl:choose>
		  <xsl:when test="normalize-space($colspec/@colwidth) = '*'">
                    <xsl:value-of select="'1*'"/>
		  </xsl:when>
		  <xsl:otherwise>
                    <xsl:value-of select="$colspec/@colwidth"/>
		  </xsl:otherwise>
		</xsl:choose>
              </xsl:attribute>
            </xsl:if>

            <xsl:choose>
              <xsl:when test="$colspec/@align">
                <xsl:attribute name="align">
                  <xsl:value-of select="$colspec/@align"/>
                </xsl:attribute>
              </xsl:when>
              <!-- Suggested by Pavel ZAMPACH <zampach@nemcb.cz> -->
              <xsl:when test="$colspecs/ancestor::tgroup/@align">
                <xsl:attribute name="align">
                  <xsl:value-of select="$colspecs/ancestor::tgroup/@align"/>
                </xsl:attribute>
              </xsl:when>
            </xsl:choose>

            <xsl:if test="$colspec/@char">
              <xsl:attribute name="char">
                <xsl:value-of select="$colspec/@char"/>
              </xsl:attribute>
            </xsl:if>
            <xsl:if test="$colspec/@charoff">
              <xsl:attribute name="charoff">
                <xsl:value-of select="$colspec/@charoff"/>
              </xsl:attribute>
            </xsl:if>
          </col>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="generate.col">
            <xsl:with-param name="countcol" select="$countcol"/>
            <xsl:with-param name="colspecs" select="$colspecs"/>
            <xsl:with-param name="count" select="$count+1"/>
            <xsl:with-param name="colnum">
              <xsl:choose>
                <xsl:when test="$colspec/@colnum">
                  <xsl:value-of select="$colspec/@colnum + 1"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="$colnum + 1"/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:with-param>
           </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="colspec.colwidth">
  <!-- when this macro is called, the current context must be an entry -->
  <xsl:param name="colname"></xsl:param>
  <!-- .. = row, ../.. = thead|tbody, ../../.. = tgroup -->
  <xsl:param name="colspecs" select="../../../../tgroup/colspec"/>
  <xsl:param name="count">1</xsl:param>
  <xsl:choose>
    <xsl:when test="$count>count($colspecs)"></xsl:when>
    <xsl:otherwise>
      <xsl:variable name="colspec" select="$colspecs[$count=position()]"/>
      <xsl:choose>
        <xsl:when test="$colspec/@colname=$colname">
          <xsl:value-of select="$colspec/@colwidth"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="colspec.colwidth">
            <xsl:with-param name="colname" select="$colname"/>
            <xsl:with-param name="colspecs" select="$colspecs"/>
            <xsl:with-param name="count" select="$count+1"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- ====================================================================== -->

</xsl:stylesheet>
