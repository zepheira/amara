<?xml version="1.0"?>

<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:f="http://xmlns.4suite.org/ext"
  exclude-result-prefixes="f"
  version="1.0"
>
  <xsl:output method="text" encoding="us-ascii"/>

  <!-- generate table of contents -->
  <xsl:param name="generate.toc" select="false()"/>

  <!-- max width to wrap to -->
  <xsl:param name="maxwidth" select="78"/>

  <!-- flag to suppress whitespace around all para elements -->
  <xsl:param name="para.leading.newline" select="false()"/>

  <xsl:variable name="whitespace" select="'                                                                               '"/>
  <xsl:variable name="doubleline" select="'==============================================================================='"/>
  <xsl:variable name="singleline" select="'-------------------------------------------------------------------------------'"/>

  <xsl:template match="/">
    <!-- build up the output doc with no width restrictions -->
    <xsl:variable name="output-buffer">
     <xsl:apply-templates/>
    </xsl:variable>
    <xsl:value-of select="f:wrap($output-buffer, $maxwidth)"/>
  </xsl:template>

  <xsl:template match="*">
    <xsl:comment>
      <xsl:text>Unknown element '</xsl:text>
      <xsl:value-of select="name()"/>
      <xsl:text>'</xsl:text>
      <xsl:if test="namespace-uri()">
        <xsl:value-of select="concat(' (namespace: ',namespace-uri(),')')"/>
      </xsl:if>
    </xsl:comment>
    <xsl:message terminate="no">
      <xsl:text>Unknown element '</xsl:text>
      <xsl:value-of select="name()"/>
      <xsl:text>'</xsl:text>
      <xsl:if test="namespace-uri()">
        <xsl:value-of select="concat(' (namespace: ',namespace-uri(),')')"/>
      </xsl:if>
      <xsl:text> - Please add a template for it to the stylesheet!</xsl:text>
    </xsl:message>
    <xsl:apply-templates select="*"/>
  </xsl:template>

  <!-- abort if it doesn't look like Simplified DocBook -->
  <xsl:template match="/*[name()!='article']">
    <xsl:message terminate="yes">The source tree does not appear to be a Simplified DocBook document.&#10;'article' (in no namespace) must be the document element.&#10;</xsl:message>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     article ::=
     ((title,subtitle?,titleabbrev?)?,articleinfo?,
      (((itemizedlist|orderedlist|variablelist|note|literallayout|
         programlisting|para|blockquote|mediaobject|informaltable|example|
         figure|table|sidebar|abstract|authorblurb|epigraph)+,section*)|
       section+),
      ((appendix)|bibliography)*)

     attributes:
       class :: = faq|journalarticle|productsheet|
               specification|techreport|whitepaper
       status :: = CDATA (e.g., draft|final)
   -->
  <xsl:template match="article">
    <xsl:choose>
      <xsl:when test="title">
        <xsl:apply-templates select="title" mode="HEADING">
          <xsl:with-param name="underline" select="$doubleline"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:when test="articleinfo/title">
        <xsl:apply-templates select="articleinfo/title" mode="HEADING">
          <xsl:with-param name="underline" select="$doubleline"/>
        </xsl:apply-templates>
      </xsl:when>
    </xsl:choose>
    <xsl:if test="section and $generate.toc">
      <xsl:apply-templates select="." mode="TOC"/>
      <xsl:value-of select="$singleline"/>
    </xsl:if>
    <xsl:apply-templates select="*[name()!='title'][name()!='articleinfo']"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    title ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|author|corpauthor|othercredit|revhistory|
     inlinemediaobject)*

    ...but we will assume the text content of the element is all we need.

    These elements contain title:
    abstract, appendix, article, articleinfo, authorblurb, bibliodiv,
    bibliography, bibliomixed, bibliomset, blockquote, example, figure,
    itemizedlist, legalnotice, note, objectinfo, orderedlist, section,
    sectioninfo, sidebar, table, variablelist.

  -->

  <!-- ignore titles unless explicited wanted via mode -->
  <xsl:template match="title"/>

  <xsl:template match="title" mode="HEADING">
    <xsl:param name="underline" select="$singleline"/>
    <xsl:variable name="title" select="normalize-space(.)"/>
    <xsl:if test="$title">
      <xsl:value-of select="$title"/>
      <xsl:text>&#10;</xsl:text>
      <xsl:value-of select="substring($underline, 1, string-length($title))"/>
      <xsl:text>&#10;&#10;</xsl:text>
    </xsl:if>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    author ::= ((honorific|firstname|surname|lineage|othername|
                 affiliation|authorblurb)+)
    othercredit ::= ((honorific|firstname|surname|lineage|othername|
                      affiliation|authorblurb)+)
  -->

  <xsl:template match="author|othercredit" mode="HEAD">
    <xsl:param name="include-orgname"/>
    <xsl:call-template name="list-authors">
      <xsl:with-param name="include-orgname" select="$include-orgname"/>
      <xsl:with-param name="separator" select="', '"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="author|othercredit">
    <xsl:param name="include-orgname"/>
    <xsl:call-template name="list-authors">
      <xsl:with-param name="include-orgname" select="$include-orgname"/>
      <xsl:with-param name="separator"/>
    </xsl:call-template>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template name="list-authors">
    <xsl:param name="include-orgname"/>
    <xsl:param name="separator" select="'; '"/>
    <xsl:param name="wrapper"/>
    <xsl:if test="normalize-space(honorific)">
      <xsl:value-of select="concat(honorific,' ')"/>
    </xsl:if>
    <xsl:if test="normalize-space(firstname)">
      <xsl:value-of select="concat(firstname,' ')"/>
    </xsl:if>
    <xsl:if test="normalize-space(othername[@role='middle'])">
      <xsl:value-of select="concat(othername[@role='middle'],' ')"/>
    </xsl:if>
    <xsl:value-of select="surname"/>
    <xsl:if test="normalize-space(lineage)">
      <xsl:value-of select="concat(' ',lineage)"/>
    </xsl:if>
    <xsl:if test="$include-orgname and normalize-space(affiliation/orgname)">
      <xsl:value-of select="concat(' (',affiliation/orgname,')')"/>
    </xsl:if>
    <xsl:if test="position() != last()">
      <xsl:copy-of select="$separator"/>
    </xsl:if>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    section ::=
    (sectioninfo?,
     (title,subtitle?,titleabbrev?),
     (((itemizedlist|orderedlist|variablelist|note|literallayout|
        programlisting|para|blockquote|mediaobject|informaltable|
        example|figure|table|sidebar|abstract|authorblurb|epigraph)+,
       section*)|
      section+))

    appendix ::=
    ((title,subtitle?,titleabbrev?),
     (((itemizedlist|orderedlist|variablelist|note|literallayout|
        programlisting|para|blockquote|mediaobject|informaltable|
        example|figure|table|sidebar|abstract|authorblurb|epigraph)+,
       section*)|
      section+))

    attributes: status=CDATA (e.g., draft|final)
                label=CDATA (identifier string if auto-generated one not OK)
  -->

  <xsl:template match="section">
    <xsl:apply-templates select="title" mode="HEADING">
      <xsl:with-param name="underline" select="$singleline"/>
    </xsl:apply-templates>
    <xsl:apply-templates select="*"/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <!-- easier than excluding these from the apply-templates above -->
  <xsl:template match="section/title
                       |section/subtitle
                       |appendix/title
                       |appendix/subtitle"/>
  <xsl:template match="titleabbrev"/>
  <xsl:template match="sectioninfo"/>

  <!-- ================================================================== -->
  <!--
    itemizedlist ::= ((title,titleabbrev?)?,listitem+)
      attributes: mark=CDATA (keyword for item marker type, e.g., bullet)
                  spacing=compact|normal (vertical spacing)
  -->
  <xsl:template match="itemizedlist">
    <xsl:apply-templates select="listitem">
      <xsl:with-param name="numeration" select="'none'"/>
    </xsl:apply-templates>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    orderedlist ::= ((title,titleabbrev?)?,listitem+)
      attributes: spacing=compact|normal (vertical spacing)
                  continuation=continues|restarts (default: restarts)
                  numeration=arabic|loweralpha|lowerroman|upperalpha|
                             upperroman (arabic assumed but no default)
                  inheritnum=ignore|inherit (default: ignore)
  -->
  <xsl:template match="orderedlist">
    <xsl:apply-templates select="listitem">
      <xsl:with-param name="numeration" select="@numeration"/>
    </xsl:apply-templates>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    listitem ::=
    ((itemizedlist|orderedlist|variablelist|note|literallayout|
      programlisting|para|blockquote|mediaobject|informaltable|
      example|figure|table|sidebar|abstract|authorblurb|epigraph)+)
  -->
  <xsl:template match="listitem">
    <xsl:param name="numeration"/>
    <xsl:text>&#10;</xsl:text>
    <xsl:choose>
      <xsl:when test="$numeration = 'none'"> <!-- itemizedlist -->
        <xsl:text>   *  </xsl:text>
      </xsl:when>
      <xsl:when test="$numeration = 'loweralpha'">
        <xsl:number level="any" format="  a. "/>
      </xsl:when>
      <xsl:when test="$numeration = 'upperalpha'">
        <xsl:number level="any" format="  A. "/>
      </xsl:when>
      <xsl:when test="$numeration = 'lowerroman'">
        <xsl:number level="any" format="  i. "/>
      </xsl:when>
      <xsl:when test="$numeration = 'upperroman'">
        <xsl:number level="any" format="  I. "/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:number level="any" format="  1. "/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    para ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*
  -->
  <xsl:template match="para">
    <xsl:if test="preceding-sibling::*[1][name() = 'para']">
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    emphasis ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*
  -->
  <xsl:template match="emphasis">
    <xsl:choose>
      <xsl:when test="@role='bold' or @role='strong'">
        <xsl:text>*</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>*</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>/</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>/</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    programlisting ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject|lineannotation)*
      attributes: linenumbering=numbered|unnumbered
                  width=CDATA
  -->
  <xsl:template match="programlisting">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    computeroutput ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*
      attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="computeroutput">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    userinput ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*
     attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="userinput">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    literal ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*
     attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="literal">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    legalnotice ::=
    (title?,
     (itemizedlist|orderedlist|variablelist|note|literallayout|
      programlisting|para|blockquote)+)
  -->
  <xsl:template match="legalnotice">
    <xsl:apply-templates select="*[local-name() != 'title']"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    figure ::=
    ((title,titleabbrev?),
     (literallayout|programlisting|blockquote|mediaobject|
      informaltable|link|ulink)+)
      attributes: float (default: "0")
                  pgwide
                  label
  -->
  <xsl:template match="figure">
    <xsl:text>[ Figure </xsl:text>
    <xsl:number level="any" format="1.1 "/>
    <xsl:text> - </xsl:text>
    <xsl:value-of select="title"/>
    <xsl:text> ]</xsl:text>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    mediaobject ::=
    (objectinfo?,
     (videoobject|audioobject|imageobject),
     (videoobject|audioobject|imageobject|textobject)*,
     caption?)
    "If possible, the processing system should use the content of the
    first object within the MediaObject. If the first object cannot be
    used, the remaining objects should be considered in the order that
    they occur."
  -->
  <xsl:template match="mediaobject"/>

  <!-- ================================================================== -->
  <!--
    link ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*

    attributes: linkend=IDREF (required; points to some 'id' attr)
                endterm=IDREF (points to 'id' attr of element with text
                to use for link text, if no content provided in this one)
                type=CDATA (app-specific customization)
  -->
  <xsl:template match="link">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    ulink ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*

    attributes: url=CDATA; type=CDATA
  -->
  <xsl:template match="ulink[@url]">
    <xsl:apply-templates/>
    <xsl:value-of select="concat(' &lt;',@url,'&gt;')"/>
  </xsl:template>

</xsl:stylesheet>
