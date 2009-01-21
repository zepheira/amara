<?xml version="1.0" encoding="utf-8"?>
<!--

 File Name:            sdocbook_html.xslt

 Simplified DocBook Stylesheet
 (for Simplified DocBook V1.0CR2)

 Copyright 2006 Fourthought Inc, USA.
 See  http://4suite.org/COPYRIGHT  for license and copyright information

 Simplified DocBook: The Definitive Guide
 http://www.docbook.org/tdg/simple/en/html/sdocbook.html

 TODO:
  - Support all of Simplified DocBook, not just the parts we use.
  - Maybe turn this into a proper customization layer for the
    official DocBook XSLT stylesheets

 DESIGN NOTES:
  - TEST ALL CHANGES in multiple browsers (e.g. IE and Mozilla).
  - Don't rely on the DTD to provide default attributes; chances
      are the source doc isn't referencing a DTD at all.
  - Do as much natural traversal down the source tree as possible.
  - Special traversal modes:
      VALIDATE
         ensure the content model is followed
      HTMLHEAD
         use to generate HTML <head> contents
      HEADER
         use to generate document header (title, abstract, authors, ...)
      TOC
         for table of contents
      TEXT
         for text-only representation of multi-purpose elements
      MARKUP
         for HTML representation of multi-purpose elements
  - Default traversal will visit all elements, doing nothing.
      To generate output, you need a template that matches one
      of these elements. The template can use apply-templates
      or can pick-and-choose from its contents. Don't forget to
      use apply-templates to continue on, unless you want the
      branch to be a dead end (which is sometimes desirable).
  - Rely on CSS for as much formatting as possible, except:
      block-level monospace type w/literal whitespace: use <pre>
      inline monospace type w/literal whitespace: use <tt>
      required bold: use <strong>
      required italics: use <em>
    Default CSS stylesheet URI = 'sdocbook_html.css';
    Default 'draft' watermark image URI = 'draft.gif';
  - Create <div>s with appropriate CSS classes for all block-level
      elements where it makes sense. Be careful when traversing
      onward from one of these elements that you apply-templates
      to attributes as well as children (e.g. select="@*|node()")
      so that ids will be copied through.
  - If an element's content model does not include #PCDATA,
      don't apply-templates to all its children. Just do elements,
      or both elements and attributes if block-level. This is in
      part because (for now) we are letting the built-in template
      for text nodes handle text, copying it through.
-->
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  exclude-result-prefixes="dc"
  version="1.0">

  <!-- CALS table support from DocBook Stylesheet distribution -->
  <xsl:include href="table.xsl"/>

  <!-- metadata -->
  <dc:Creator>Fourthought, Inc</dc:Creator>
  <dc:Title>Simplified DocBook Stylesheet</dc:Title>

  <!-- used to determine the footnote that is referenced by a footnoteref -->
  <xsl:key name="footnotes" match="footnote" use="@id"/>

  <!-- generate full HTML doc with table of contents? -->
  <xsl:param name="top-level-html" select="true()"/>

  <!-- if generating full HTML doc, URI of CSS file to link to -->
  <xsl:param name="css-file" select="'sdocbook_html.css'"/>

  <!-- watermark image for article[@status='draft'] -->
  <xsl:param name="draft-watermark-image" select="'draft.gif'"/>

  <!-- show revision history? -->
  <xsl:param name="show-rev-history" select="false()"/>

  <!-- show revision remarks? -->
  <xsl:param name="show-rev-remarks" select="false()"/>

  <!-- number each <section>? -->
  <xsl:param name="number-sections" select="true()"/>

  <!-- max depth of table of contents -->
  <xsl:param name="toc-depth" select="3"/>

  <!-- namespaces which do NOT emit a warning for no implementation -->
  <xsl:param name="ignore-namespaces"
             select="processing-instruction('ftdb-ignore-namespace')"/>

  <!-- a DOCTYPE with a system ID puts browsers in standards-compliance mode -->
  <xsl:output method="html" encoding="iso-8859-1" indent="yes"
    doctype-system="http://www.w3.org/TR/html4/loose.dtd"
    doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"/>

  <!-- ================================================================== -->

  <xsl:template match="/">
    <xsl:apply-templates select="*" mode="VALIDATE"/>
    <xsl:choose>
      <xsl:when test="$top-level-html">
        <html>
          <head>
            <xsl:apply-templates select="*" mode="HTMLHEAD"/>
            <xsl:if test="$css-file != ''">
              <link rel='stylesheet' href='{$css-file}' type='text/css'/>
            </xsl:if>
          </head>
          <body>
            <xsl:apply-templates select="*"/>
          </body>
        </html>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="*"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- default behavior for all modes: traverse elements only -->
  <xsl:template match="*" mode="HTMLHEAD">
    <xsl:apply-templates select="*" mode="HTMLHEAD"/>
  </xsl:template>

  <xsl:template match="*" mode="HEADER">
    <xsl:apply-templates select="*" mode="HEADER"/>
  </xsl:template>

  <xsl:template match="*" mode="TOC">
    <xsl:apply-templates select="*" mode="TOC"/>
  </xsl:template>

  <xsl:template match="*" mode="VALIDATE">
    <xsl:apply-templates select="*" mode="VALIDATE"/>
  </xsl:template>

  <xsl:template match="*">
    <xsl:if test="not(namespace-uri() = $ignore-namespaces)">
      <xsl:variable name="text">
        <xsl:text>Unknown element '</xsl:text>
        <xsl:value-of select="name()"/>
        <xsl:text>'</xsl:text>
        <xsl:if test="namespace-uri()">
          <xsl:value-of select="concat(' (namespace: ',namespace-uri(),')')"/>
        </xsl:if>
      </xsl:variable>
      <!-- notify the user -->
      <xsl:message terminate="no">
        <xsl:copy-of select="$text"/>
        <xsl:text> - Please add a template for it to the stylesheet!</xsl:text>
      </xsl:message>
      <!-- add a comment to the result document -->
      <xsl:comment>
        <xsl:copy-of select="$text"/>
      </xsl:comment>
    </xsl:if>
    <xsl:apply-templates select="*"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- UTILITY TEMPLATES -->
  <!-- ================================================================== -->

  <!-- used by table.xsl -->
  <xsl:template name="copy-string">
    <!-- returns 'count' copies of 'string' -->
    <xsl:param name="string"/>
    <xsl:param name="count" select="0"/>
    <xsl:param name="result"/>

    <xsl:choose>
      <xsl:when test="$count&gt;0">
        <xsl:call-template name="copy-string">
          <xsl:with-param name="string" select="$string"/>
          <xsl:with-param name="count" select="$count - 1"/>
          <xsl:with-param name="result">
            <xsl:value-of select="$result"/>
            <xsl:value-of select="$string"/>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$result"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="block-element">
    <div class="{local-name()}">
      <xsl:if test="@id">
        <a name="{@id}" id="{@id}"/>
      </xsl:if>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template name="inline-element">
    <xsl:param name="display" select="'none'"/>
    <xsl:param name="element">
      <xsl:choose>
        <xsl:when test="$display = 'italic'">i</xsl:when>
        <xsl:when test="$display = 'bold'">b</xsl:when>
        <xsl:when test="$display = 'monospace'">tt</xsl:when>
        <xsl:otherwise>span</xsl:otherwise>
      </xsl:choose>
    </xsl:param>
    <xsl:param name="class" select="local-name()"/>
    <xsl:param name="prefix"/>
    <xsl:param name="content">
      <xsl:call-template name="inline-content"/>
    </xsl:param>
    <xsl:param name="suffix"/>

    <xsl:element name="{$element}">
      <xsl:apply-templates select="@*"/>

      <xsl:attribute name="class">
        <xsl:value-of select="$class"/>
      </xsl:attribute>

      <xsl:copy-of select="$prefix"/>
      <xsl:copy-of select="$content"/>
      <xsl:copy-of select="$suffix"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="inline-content">
    <xsl:choose>
      <xsl:when test="@revisionflag = 'added'">
        <ins><xsl:apply-templates/></ins>
      </xsl:when>
      <xsl:when test="@revisionflag = 'removed'">
        <del><xsl:apply-templates/></del>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- COMMON ATTRIBUTES -->
  <!-- ================================================================== -->

  <!-- copy id attribute as-is -->
  <xsl:template match="@id">
    <xsl:copy/>
  </xsl:template>

  <!-- copy lang attribute as-is -->
  <xsl:template match="@lang">
    <xsl:copy/>
  </xsl:template>

  <!-- ignore other attributes -->
  <xsl:template match="@*" priority="-1"/>

  <!-- ================================================================== -->
  <!-- COMPONENTS -->
  <!-- ================================================================== -->

  <!-- only "article" is allowed as the root in Simplified DocBook -->
  <xsl:template match="/*" mode="VALIDATE" priority="-1">
    <!-- abort if not valid Simplified DocBook -->
    <xsl:message terminate="yes">
      <xsl:text>Simplified DocBook documents must have 'article' </xsl:text>
      <xsl:text>(null namespace) as the document element, not '</xsl:text>
      <xsl:value-of select="name()"/>
      <xsl:text>'</xsl:text>
      <xsl:choose>
        <xsl:when test="namespace-uri()">
          <xsl:text> (namespace: </xsl:text>
          <xsl:value-of select="namespace-uri()"/>
          <xsl:text>)</xsl:text>
        </xsl:when>
        <xsl:otherwise> (null namespace)</xsl:otherwise>
      </xsl:choose>
    </xsl:message>
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
  <xsl:template match="article" mode="VALIDATE">
    <xsl:if test="articleinfo/title and title and articleinfo/title != title">
      <xsl:message terminate="yes">
        <xsl:text>ERROR: article/title and articleinfo/title</xsl:text>
        <xsl:text> MUST be the same.</xsl:text>
      </xsl:message>
    </xsl:if>
    <xsl:apply-templates select="*" mode="VALIDATE"/>
  </xsl:template>

  <xsl:template match="article" mode="HTMLHEAD">
    <title>
      <xsl:apply-templates select="(articleinfo/title|title)[1]" mode="TEXT"/>
    </title>
    <xsl:apply-templates select="*" mode="HTMLHEAD"/>
  </xsl:template>

  <xsl:template match="article">
    <div class="article">
      <xsl:if test="@status = 'draft' and $draft-watermark-image != ''">
        <xsl:attribute name="style">
          <xsl:text>background-image: url("</xsl:text>
          <xsl:value-of select="$draft-watermark-image"/>
          <xsl:text>");</xsl:text>
        </xsl:attribute>
      </xsl:if>

      <xsl:variable name="title" select="(articleinfo/title|title)[1]"/>
      <xsl:if test="$title">
        <div class="article-title">
          <h1 class="title">
            <xsl:apply-templates select="$title" mode="MARKUP"/>
            <xsl:variable name="subtitle" select="(articleinfo/subtitle
                                                  |subtitle)[1]"/>
            <xsl:if test="$subtitle">
              <br/>
              <span class="subtitle">
                <xsl:apply-templates select="$subtitle" mode="MARKUP"/>
              </span>
            </xsl:if>
          </h1>
        </div>
      </xsl:if>

      <xsl:variable name="header">
        <xsl:apply-templates select="articleinfo" mode="HEADER"/>
      </xsl:variable>
      <xsl:if test="string($header)">
        <div class="header">
          <xsl:copy-of select="$header"/>
        </div>
        <hr/>
      </xsl:if>

      <xsl:if test="section|appendix">
        <div class="toc">
          <h2>Table Of Contents</h2>
          <xsl:apply-templates select="section" mode="TOC"/>

          <xsl:variable name="appendices" select="appendix"/>
          <xsl:if test="$appendices">
            <h3>
              <xsl:choose>
                <xsl:when test="$appendices[2]">Appendices</xsl:when>
                <xsl:otherwise>Appendix</xsl:otherwise>
              </xsl:choose>
            </h3>
            <xsl:apply-templates select="$appendices" mode="TOC"/>
          </xsl:if>
        </div>
        <hr/>
      </xsl:if>

      <div class="body">
        <xsl:apply-templates select="@*|*"/>
      </div>

      <xsl:variable name="footnotes"
        select=".//footnote[not(ancestor::table|ancestor::informaltable)]"/>
      <xsl:if test="$footnotes">
        <hr/>
        <div class="footer">
          <xsl:call-template name="display.footnotes">
            <xsl:with-param name="footnotes" select="$footnotes"/>
          </xsl:call-template>
        </div>
      </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="article/articleinfo"/>

  <!-- ================================================================== -->
  <!-- SECTIONS -->
  <!-- ================================================================== -->

  <xsl:template name="section-number">
    <xsl:choose>
      <xsl:when test="ancestor-or-self::appendix">
        <xsl:number level="multiple"
                    count="appendix|appendix//section"
                    format="A.1 "/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:number level="multiple"
                    count="section"
                    format="1.1 "/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="section-id">
    <xsl:choose>
      <xsl:when test="@id">
        <xsl:value-of select="@id"/>
      </xsl:when>
      <xsl:when test="normalize-space(@label)">
        <xsl:value-of select="translate(normalize-space(@label),' ','-')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="generate-id()"/>
      </xsl:otherwise>
    </xsl:choose>
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

    attributes: status=CDATA (e.g., draft|final)
                label=CDATA (identifier string if auto-generated one not OK)

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
  <xsl:template match="section|appendix" mode="VALIDATE">
    <xsl:choose>
      <xsl:when test="not(title)">
        <xsl:message terminate="yes">
          <xsl:text>ERROR: '</xsl:text>
          <xsl:value-of select="local-name()"/>
          <xsl:text>' element missing required 'title' element</xsl:text>
        </xsl:message>
      </xsl:when>
      <xsl:when test="sectioninfo/title and title != sectioninfo/title">
        <xsl:message terminate="yes">
          <xsl:text>ERROR: section/title and sectioninfo/title</xsl:text>
          <xsl:text> MUST be the same.</xsl:text>
        </xsl:message>
      </xsl:when>
    </xsl:choose>
    <xsl:apply-templates select="*" mode="VALIDATE"/>
  </xsl:template>

  <xsl:template match="section|appendix" mode="TOC">
    <xsl:param name="depth" select="1"/>
    <xsl:if test="$depth &lt;= $toc-depth">
      <p style="display: inline; padding-left: {$depth}em">
        <xsl:if test="$number-sections">
          <xsl:call-template name="section-number"/>
        </xsl:if>
        <a>
          <xsl:attribute name="href">
            <xsl:text>#</xsl:text>
            <xsl:call-template name="section-id"/>
          </xsl:attribute>

          <!-- if present, the 'label' is normative for the TOC -->
          <xsl:choose>
            <xsl:when test="@label">
              <xsl:value-of select="@label"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="title"/>
            </xsl:otherwise>
          </xsl:choose>
        </a>
        <br/>
      </p>
      <xsl:apply-templates select="section" mode="TOC">
        <xsl:with-param name="depth" select="$depth + 1"/>
      </xsl:apply-templates>
    </xsl:if>
  </xsl:template>

  <xsl:template match="section|appendix">
    <div class="{local-name()}">
      <xsl:if test="@status = 'draft'">
        <xsl:attribute name="style">
          <xsl:text>background-image: url("</xsl:text>
          <xsl:value-of select="$draft-watermark-image"/>
          <xsl:text>");</xsl:text>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="@*"/>

      <xsl:variable name="depth" select="count(ancestor::*)"/>
      <xsl:variable name="heading-level">
        <xsl:choose>
          <xsl:when test="$depth &gt; 6">6</xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$depth"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <!--
        A named anchor must be provided for browsers that don't support
        URL fragments referencing div IDs.  In HTML, anchor names share the same
        value space as element IDs in HTML, and must be unique across that space.
        This makes it impossible to validly provide both an anchor and a div with
        the same identifier. However, since the uniqueness of IDs can be (and is,
        on the W3C's validation service) validated with a DTD, while uniqueness
        the whole value space cannot, we'll punt: the div gets an 'id' and the
        anchor gets a 'name' with the same value, even though that's improper.
      -->
      <xsl:variable name="section-id">
        <xsl:call-template name="section-id"/>
      </xsl:variable>
      <a name="{$section-id}"/>

      <div>
        <xsl:if test="parent::article">
          <xsl:attribute name="class">section-title</xsl:attribute>
        </xsl:if>

        <xsl:element name="h{$heading-level}">
          <xsl:attribute name="class">title</xsl:attribute>
          <xsl:if test="$number-sections">
            <span class="section-number">
              <xsl:call-template name="section-number"/>
            </span>
          </xsl:if>

          <xsl:apply-templates select="title" mode="MARKUP"/>

          <xsl:if test="subtitle">
            <br/>
            <span class="subtitle">
              <xsl:apply-templates select="subtitle" mode="MARKUP"/>
            </span>
          </xsl:if>
        </xsl:element>
      </div>

      <xsl:apply-templates select="*"/>

    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- META-INFORMATION -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    articleinfo ::=
    ((mediaobject|legalnotice|subjectset|keywordset|abbrev|abstract|
      author|authorgroup|bibliomisc|copyright|corpauthor|date|edition|
      editor|issuenum|othercredit|pubdate|publishername|releaseinfo|
      revhistory|subtitle|title|titleabbrev|volumenum|citetitle|
      honorific|firstname|surname|lineage|othername|affiliation|
      authorblurb)+)
  -->
  <xsl:template match="articleinfo" mode="HTMLHEAD">
    <xsl:variable name="authors" select="author|authorgroup/author"/>
    <xsl:if test="$authors">
      <meta name="author">
        <xsl:attribute name="content">
          <xsl:apply-templates select="$authors" mode="TEXT"/>
        </xsl:attribute>
      </meta>
    </xsl:if>
    <xsl:apply-templates select="*" mode="HTMLHEAD"/>
  </xsl:template>

  <xsl:template match="articleinfo/author" mode="HTMLHEAD"/>
  <xsl:template match="articleinfo/authorgroup" mode="HTMLHEAD"/>

  <xsl:template match="articleinfo" mode="HEADER">
    <xsl:variable name="history" select="revhistory"/>
    <xsl:variable name="authors" select="corpauthor
                                         |author
                                         |authorgroup/author"/>
    <xsl:variable name="others" select="othercredit
                                        |authorgroup/othercredit
                                        |revhistory/revision/author"/>
    <xsl:if test="$history or $authors or $others">
      <dl>
        <xsl:apply-templates select="$history" mode="HEADER"/>
        <xsl:if test="$authors">
          <dt>
            <xsl:text>Principal author</xsl:text>
            <xsl:if test="$authors[2]">s</xsl:if>
            <xsl:text>: </xsl:text>
          </dt>
          <xsl:apply-templates select="$authors" mode="HEADER"/>
        </xsl:if>
        <xsl:if test="$others">
          <dt>
            <xsl:choose>
              <xsl:when test="$authors">Additional contributor</xsl:when>
              <xsl:otherwise>Contributor</xsl:otherwise>
            </xsl:choose>
            <xsl:if test="$others[2]">s</xsl:if>
            <xsl:text>: </xsl:text>
          </dt>
          <xsl:for-each select="$others">
            <xsl:variable name="current" select="position()"/>
            <xsl:if test="not(. = $others[position() &lt; $current])
                          and not(. = $authors)">
              <xsl:apply-templates select="." mode="HEADER"/>
            </xsl:if>
          </xsl:for-each>
        </xsl:if>
      </dl>
    </xsl:if>
    <xsl:apply-templates select="legalnotice" mode="HEADER"/>
    <xsl:apply-templates select="abstract" mode="HEADER"/>
  </xsl:template>

  <xsl:template match="articleinfo"/>

  <!-- ================================================================== -->
  <!--
    sectioninfo ::=
    ((mediaobject|legalnotice|keywordset|subjectset|abbrev|abstract|
      author|authorgroup|bibliomisc|copyright|corpauthor|date|edition|
      editor|issuenum|othercredit|pubdate|publishername|releaseinfo|
      revhistory|subtitle|title|titleabbrev|volumenum|citetitle|
      honorific|firstname|surname|lineage|othername|affiliation|
      authorblurb)+)
  -->
  <xsl:template match="sectioninfo"/>

  <!-- ================================================================== -->
  <!--
    objectinfo ::=
    ((mediaobject|legalnotice|keywordset|subjectset|abbrev|abstract|
      author|authorgroup|bibliomisc|copyright|corpauthor|date|edition|
      editor|issuenum|othercredit|pubdate|publishername|releaseinfo|
      revhistory|subtitle|title|titleabbrev|volumenum|citetitle|
      honorific|firstname|surname|lineage|othername|affiliation|
      authorblurb)+)
  -->
  <xsl:template match="objectinfo"/>

  <!-- ================================================================== -->
  <!--
    title ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|author|corpauthor|othercredit|revhistory|
     inlinemediaobject)*
  -->
  <xsl:template match="title" mode="TEXT">
    <xsl:variable name="title">
      <xsl:apply-templates/>
    </xsl:variable>
    <xsl:value-of select="$title"/>
  </xsl:template>

  <xsl:template match="title" mode="MARKUP">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="title"/>

  <!--
    subtitle ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|author|corpauthor|othercredit|revhistory|
     inlinemediaobject)*
  -->
  <xsl:template match="subtitle" mode="MARKUP">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="subtitle"/>

  <!--
    titleabbrev ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|author|corpauthor|othercredit|revhistory|
     inlinemediaobject)*
  -->
  <xsl:template match="titleabbrev"/>

  <!-- ================================================================== -->
  <!--
    legalnotice ::=
    (title?,
     (itemizedlist|orderedlist|variablelist|note|literallayout|
      programlisting|para|blockquote)+)
  -->
  <xsl:template match="legalnotice" mode="HEADER">
    <div class="legalnotice">
      <xsl:apply-templates select="@*"/>
      <h2 class="title">
        <xsl:choose>
          <xsl:when test="title">
            <xsl:apply-templates select="title" mode="MARKUP"/>
          </xsl:when>
          <xsl:otherwise>Legal Notice</xsl:otherwise>
        </xsl:choose>
      </h2>
      <xsl:apply-templates select="*"/>
    </div>
  </xsl:template>

  <xsl:template match="legalnotice"/>

  <!-- ================================================================== -->
  <!--
    keywordset ::= (keyword+)
    keyword ::= (#PCDATA)
  -->
  <xsl:template match="keywordset" mode="HTMLHEAD">
    <meta name="keywords">
      <xsl:attribute name="content">
        <xsl:for-each select="keyword">
          <xsl:if test="position() > 1">, </xsl:if>
          <xsl:value-of select="translate(normalize-space(), ',', ';')"/>
        </xsl:for-each>
      </xsl:attribute>
    </meta>
  </xsl:template>

  <xsl:template match="keywordset"/>

  <!-- ================================================================== -->
  <!--
    subjectset ::= (subject+)
       attributes: scheme=NMTOKEN

    subject ::= (subjectterm+)
       attributes: weight=CDATA

    subjectterm ::= (#PCDATA)
  -->
  <xsl:template match="subjectset"/>

  <!-- ================================================================== -->
  <!--
    revhistory ::= (revision+)
    revision ::=
    (revnumber,date,authorinitials*,
     (revremark|revdescription)?)
  -->
  <xsl:template match="revhistory" mode="HEADER">
    <dt>This version:</dt>
    <xsl:apply-templates select="revision">
      <xsl:sort select="date" order="descending"/>
      <xsl:with-param name="from" select="1"/>
      <xsl:with-param name="to" select="1"/>
    </xsl:apply-templates>
    <xsl:if test="$show-rev-history and revision[2]">
      <dt>Previous versions:</dt>
      <xsl:apply-templates select="revision">
        <xsl:sort select="date" order="descending"/>
        <xsl:with-param name="from" select="2"/>
      </xsl:apply-templates>
    </xsl:if>
  </xsl:template>

  <xsl:template match="revhistory"/>

  <!-- ================================================================== -->
  <!--
    revision ::=
    (revnumber,date,authorinitials*,(revremark|revdescription)?)
  -->
  <xsl:template match="revision">
    <xsl:param name="from" select="1"/>
    <xsl:param name="to" select="position()"/>
    <xsl:if test="position() &gt;= $from and position() &lt;= $to">
      <xsl:variable name="revnumber" select="normalize-space(revnumber)"/>
      <xsl:variable name="date" select="normalize-space(date)"/>
      <dd>
        <xsl:choose>
          <xsl:when test="$revnumber">
            <xsl:text>Revision </xsl:text>
            <xsl:value-of select="$revnumber"/>
            <xsl:if test="$date">
              <xsl:text> (</xsl:text>
              <xsl:value-of select="$date"/>
              <xsl:text>)</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:when test="$date">
            <xsl:value-of select="$date"/>
            <xsl:text> Revision</xsl:text>
            <xsl:variable name="multiples" select="../revision[date=$date]"/>
            <xsl:if test="$multiples">
              <xsl:text> (Update #</xsl:text>
              <xsl:value-of select="count($multiples)"/>
              <xsl:text>)</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:otherwise>Unknown revision number</xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$show-rev-remarks and normalize-space(revremark)">
          <xsl:text>: </xsl:text>
          <xsl:apply-templates select="revremark"/>
        </xsl:if>
      </dd>
    </xsl:if>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    revremark ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*
  -->
  <xsl:template match="revremark">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    corpauthor ::=
    (#PCDATA|link|olink|ulink|emphasis|trademark|replaceable|remark|
     subscript|superscript|inlinegraphic|inlinemediaobject|indexterm)*
  -->

  <xsl:template match="corpauthor" mode="TEXT">
    <xsl:value-of select="."/>
    <xsl:if test="position() != last()">, </xsl:if>
  </xsl:template>

  <xsl:template match="corpauthor" mode="HEADER">
    <dd>
      <xsl:apply-templates select="."/>
    </dd>
  </xsl:template>

  <xsl:template match="corpauthor">
    <span class="corpauthor">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    author ::= ((honorific|firstname|surname|lineage|othername|
                 affiliation|authorblurb)+)
    othercredit ::= ((honorific|firstname|surname|lineage|othername|
                      affiliation|authorblurb)+)
  -->
  <xsl:template name="entity-name">
    <xsl:if test="honorific">
      <xsl:apply-templates select="honorific"/>
    </xsl:if>
    <xsl:if test="firstname">
      <xsl:if test="honorific">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="firstname"/>
    </xsl:if>
    <xsl:if test="othername">
      <xsl:if test="honorific or firstname">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="othername"/>
    </xsl:if>
    <xsl:if test="surname">
      <xsl:if test="honorific or firstname or othername">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="surname"/>
    </xsl:if>
    <xsl:if test="lineage">
      <xsl:if test="honorific or firstname or othername or surname">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="lineage"/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="author|othercredit" mode="TEXT">
    <xsl:variable name="entity-name">
      <xsl:call-template name="entity-name"/>
    </xsl:variable>
    <xsl:value-of select="$entity-name"/>
    <xsl:if test="position() != last()">, </xsl:if>
  </xsl:template>

  <xsl:template match="author|othercredit" mode="HEADER">
    <dd>
      <xsl:apply-templates select="."/>
    </dd>
  </xsl:template>

  <xsl:template match="author|othercredit">
    <span class="{local-name()}">
      <xsl:call-template name="entity-name"/>
      <xsl:if test="affiliation/orgname">
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="affiliation/orgname"/>
      </xsl:if>
      <xsl:if test="email">
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="email"/>
      </xsl:if>
    </span>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    honorific ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*

    firstname ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*

    surname ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*

    othername ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*

    lineage ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*
  -->
  <xsl:template match="honorific|firstname|surname|othername|lineage">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    orgname ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|
     inlinemediaobject)*
  -->
  <xsl:template match="orgname">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="prefix" select="'('"/>
      <xsl:with-param name="suffix" select="')'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    abstract ::= (title?,(para)+)
  -->
  <xsl:template match="articleinfo/abstract" mode="HTMLHEAD">
    <meta name="description">
      <xsl:attribute name="content">
        <xsl:for-each select="para">
          <xsl:if test="position() > 1"> </xsl:if>
          <xsl:value-of select="normalize-space()"/>
        </xsl:for-each>
      </xsl:attribute>
    </meta>
  </xsl:template>

  <xsl:template match="abstract" mode="HEADER">
    <div class="abstract">
      <xsl:apply-templates select="@*"/>
      <h2>
        <xsl:choose>
          <xsl:when test="title">
            <xsl:apply-templates select="title" mode="MARKUP"/>
          </xsl:when>
          <xsl:otherwise>Abstract</xsl:otherwise>
        </xsl:choose>
      </h2>
      <xsl:apply-templates select="para"/>
    </div>
  </xsl:template>

  <xsl:template match="abstract"/>

  <!-- ================================================================== -->
  <!-- BLOCK ELEMENTS -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- Lists -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    itemizedlist ::= ((title,titleabbrev?)?,listitem+)
      attributes: mark=CDATA (keyword for item marker type, e.g., bullet)
                  spacing=compact|normal (vertical spacing)
  -->
  <xsl:template match="itemizedlist">
    <ul>
      <xsl:apply-templates select="@*"/>
      <xsl:if test="@spacing='compact'">
        <xsl:attribute name="class">compact</xsl:attribute>
      </xsl:if>
      <xsl:attribute name="style">
        <xsl:text>list-style-type: </xsl:text>
        <xsl:choose>
          <xsl:when test="@mark">
            <xsl:value-of select="@mark"/>
          </xsl:when>
          <xsl:otherwise>disc</xsl:otherwise>
        </xsl:choose>
        <xsl:text>; list-style-position: </xsl:text>
        <xsl:choose>
          <xsl:when test="@spacing='compact'">inside</xsl:when>
          <xsl:otherwise>outside</xsl:otherwise>
        </xsl:choose>
        <xsl:text>;</xsl:text>
      </xsl:attribute>
      <xsl:apply-templates select="listitem"/>
    </ul>
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
    <ol>
      <xsl:apply-templates select="@*"/>
      <xsl:if test="@spacing='compact'">
        <xsl:attribute name="class">compact</xsl:attribute>
      </xsl:if>
      <xsl:attribute name="style">
        <xsl:text>list-style-type: </xsl:text>
        <xsl:choose>
          <xsl:when test="@numeration='loweralpha'">lower-alpha</xsl:when>
          <xsl:when test="@numeration='upperalpha'">upper-alpha</xsl:when>
          <xsl:when test="@numeration='lowerroman'">lower-roman</xsl:when>
          <xsl:when test="@numeration='upperroman'">upper-roman</xsl:when>
          <xsl:otherwise>decimal</xsl:otherwise>
        </xsl:choose>
        <xsl:text>; list-style-position: </xsl:text>
        <xsl:choose>
          <xsl:when test="@spacing='compact'">inside</xsl:when>
          <xsl:otherwise>outside</xsl:otherwise>
        </xsl:choose>
        <xsl:text>;</xsl:text>
      </xsl:attribute>
      <xsl:apply-templates select="listitem"/>
    </ol>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    listitem ::=
    ((itemizedlist|orderedlist|variablelist|note|literallayout|
      programlisting|para|blockquote|mediaobject|informaltable|
      example|figure|table|sidebar|abstract|authorblurb|epigraph)+)
  -->
  <xsl:template match="listitem" mode="VALIDATE">
    <xsl:variable name="content">
      <xsl:for-each select="text()">
        <xsl:value-of select="normalize-space()"/>
      </xsl:for-each>
    </xsl:variable>
    <xsl:if test="string($content)">
      <xsl:message terminate="yes">
        <xsl:text>ERROR: #PCDATA within 'listitem'&#10;</xsl:text>
        <xsl:copy-of select="."/>
      </xsl:message>
    </xsl:if>
  </xsl:template>

  <xsl:template match="listitem">
    <li>
      <xsl:if test="parent::*/@spacing='compact'">
        <xsl:attribute name="style">margin-top: 0; margin-bottom: 0</xsl:attribute>
      </xsl:if>
      <!-- to support orderedlist with continuation='continues', figure
           out a way here to create a 'value' attribute on the first
           listitem, with the right number to start on. -->
      <xsl:apply-templates select="@*|*"/>
    </li>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    variablelist ::= ((title,titleabbrev?)?, varlistentry+)
  -->
  <xsl:template match="variablelist">
    <div class="variablelist">
      <xsl:apply-templates select="@*"/>
      <xsl:if test="title">
        <p class="title">
          <b><xsl:value-of select="title"/></b>
        </p>
      </xsl:if>
      <dl>
        <xsl:apply-templates select="varlistentry"/>
      </dl>
    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    varlistentry ::= (term+,listitem)
  -->
  <xsl:template match="varlistentry">
    <dt>
      <xsl:for-each select="term">
        <xsl:if test="position() > 1">
          <br/>
        </xsl:if>
        <xsl:apply-templates/>
      </xsl:for-each>
    </dt>
    <dd>
      <xsl:apply-templates select="listitem/*"/>
    </dd>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Admonitions -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    note ::=
    (title?,
     (itemizedlist|orderedlist|variablelist|note|literallayout|
      programlisting|para|blockquote|mediaobject|informaltable|
      example|figure|table)+)
  -->
  <xsl:template match="note">
    <div class="note">
      <xsl:apply-templates select="@*"/>
      <xsl:if test="not(title)">
        <span class="label">Note</span>
      </xsl:if>
      <xsl:apply-templates select="*"/>
    </div>
  </xsl:template>

  <xsl:template match="note/title">
    <span class="label">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Line-specific Environments -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    literallayout ::=
       (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
       footnote|phrase|quote|trademark|link|ulink|command|
       computeroutput|email|filename|literal|option|replaceable|
       systemitem|userinput|inlinemediaobject|lineannotation)*

    attributes: width=CDATA
                format=linespecific (default: linespecific)
                linenumbering=numbered|unnumbered
                class=monospaced|normal (default: normal)
  -->
  <xsl:template match="literallayout">
    <!-- FIXME: support linenumbering -->
    <xsl:choose>
      <xsl:when test="@class = 'monospaced'">
        <div class="literallayout">
          <pre>
            <xsl:apply-templates select="@*|node()"/>
          </pre>
        </div>
      </xsl:when>
      <xsl:otherwise>
        <div class="literallayout" style="white-space: pre">
          <xsl:apply-templates select="@*|node()"/>
        </div>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- make.verbatim.mode replaces spaces and newlines -->
  <xsl:template match="*" mode="make.verbatim.mode">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates mode="make.verbatim.mode"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="processing-instruction()|comment()"
                mode="make.verbatim.mode">
    <xsl:copy/>
  </xsl:template>

  <xsl:template match="text()" mode="make.verbatim.mode" name="make.verbatim">
    <xsl:param name="text" select="translate(., ' ', '&#160;')"/>

    <xsl:choose>
      <xsl:when test="not(contains($text, '&#xA;'))">
        <xsl:value-of select="$text"/>
      </xsl:when>

      <xsl:otherwise>
        <xsl:variable name="len" select="string-length($text)"/>

        <xsl:choose>
          <xsl:when test="$len = 1">
            <br/><xsl:text>&#xA;</xsl:text>
          </xsl:when>

          <xsl:otherwise>
            <xsl:variable name="half" select="$len div 2"/>
            <xsl:call-template name="make.verbatim">
              <xsl:with-param name="text" select="substring($text, 1, $half)"/>
            </xsl:call-template>
            <xsl:call-template name="make.verbatim">
              <xsl:with-param name="text"
                              select="substring($text, ($half + 1), $len)"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
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
    <div>
      <xsl:apply-templates select="@*"/>
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="@role='sample.IO'">screen</xsl:when>
          <xsl:otherwise>programlisting</xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <!-- pre necessary because CSS1's white-space:pre can be ignored -->
      <pre>
        <xsl:apply-templates/>
      </pre>
    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Examples, Figures and Tables -->
  <!-- ================================================================== -->

  <xsl:template name="formal-block">
    <xsl:param name="caption-type"/>
    <xsl:param name="caption-side" select="'top'"/>
    <xsl:param name="class" select="local-name()"/>
    <xsl:param name="style"/>

    <xsl:if test="not(title)">
      <xsl:message terminate="yes">
        <xsl:text>ERROR: Formal element '</xsl:text>
        <xsl:value-of select="local-name()"/>
        <xsl:text>' missing required 'title' element.</xsl:text>
      </xsl:message>
    </xsl:if>

    <div class="${class}">
      <xsl:apply-templates select="@*"/>
      <xsl:if test="normalize-space($style)">
        <xsl:attribute name="style">
          <xsl:value-of select="normalize-space($style)"/>
        </xsl:attribute>
      </xsl:if>
      <a>
        <xsl:attribute name="name">
          <xsl:choose>
            <xsl:when test="normalize-space(@label)">
              <xsl:value-of select="translate(@label,' ','-')"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="generate-id()"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </a>
      <xsl:choose>
        <xsl:when test="@caption-side = 'top'">
          <xsl:call-template name="formal-block-caption">
            <xsl:with-param name="caption-type" select="$caption-type"/>
          </xsl:call-template>
          <xsl:apply-templates select="*"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="*"/>
          <xsl:call-template name="formal-block-caption">
            <xsl:with-param name="caption-type" select="$caption-type"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template name="formal-block-caption">
    <xsl:param name="caption-type"/>
    <p class="caption">
      <b>
        <xsl:value-of select="$caption-type"/>
        <xsl:text>&#160;</xsl:text>
        <xsl:number level="any" format="1.1"/>
        <xsl:text> &#8212; </xsl:text>
        <xsl:apply-templates select="title" mode="MARKUP"/>
      </b>
    </p>
  </xsl:template>

  <xsl:template name="informal-block">
    <xsl:param name="class" select="local-name()"/>
    <xsl:param name="style"/>

    <div class="${class}">
      <xsl:apply-templates select="@*"/>
      <xsl:if test="normalize-space($style)">
        <xsl:attribute name="style">
          <xsl:value-of select="normalize-space($style)"/>
        </xsl:attribute>
      </xsl:if>
      <a>
        <xsl:attribute name="name">
          <xsl:choose>
            <xsl:when test="normalize-space(@label)">
              <xsl:value-of select="translate(@label,' ','-')"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="generate-id()"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </a>
      <xsl:apply-templates select="*"/>
    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    example ::=
    ((title,titleabbrev?),
     (itemizedlist|orderedlist|variablelist|literallayout|
      programlisting|para|blockquote|mediaobject|informaltable)+)

    attributes: label=CDATA
                width=CDATA
  -->
  <xsl:template match="example">
    <xsl:call-template name="formal-block">
      <xsl:with-param name="caption-type">Example</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    figure ::=
    ((title,titleabbrev?),
     (literallayout|programlisting|blockquote|mediaobject|
      informaltable|link|ulink)+)

    attributes: float=0|1 (default: "0")
                pgwide=0|1
                label
  -->
  <xsl:template match="figure">
    <xsl:call-template name="formal-block">
      <xsl:with-param name="caption-type">Figure</xsl:with-param>
      <xsl:with-param name="style">
        <xsl:if test="@float != 0">float: left;</xsl:if>
        <xsl:if test="@pgwide != 0">width: 100%;</xsl:if>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    informaltable ::= (mediagroup+|tgroup+)

    attributes: tocentry=0|1 (default: 0)
                shortentry=0|1
                colsep=0|1
                tabstyle=CDATA
                frame=all|bottom|none|sides|top|topbot
                rowsep=0|1
                orient=land|port
                pgwide=0|1
                label=CDATA
  -->

  <xsl:template match="informaltable">
    <xsl:call-template name="informal-block">
      <xsl:with-param name="class">
        <xsl:choose>
          <xsl:when test="@tabstyle">
            <xsl:value-of select="@tabstyle"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="local-name(.)"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    table ::= (title,(mediagroup+|tgroup+))

    attributes: tocentry=0|1 (default: 0)
                shortentry=0|1
                colsep=0|1
                tabstyle=CDATA
                frame=all|bottom|none|sides|top|topbot
                rowsep=0|1
                orient=land|port
                pgwide=0|1
                label=CDATA
  -->

  <xsl:template match="table">
    <xsl:call-template name="formal-block">
      <xsl:with-param name="caption-type">Table</xsl:with-param>
      <xsl:with-param name="class">
        <xsl:choose>
          <xsl:when test="@tabstyle">
            <xsl:value-of select="@tabstyle"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="local-name(.)"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="table/title">
    <div class="title">
      <strong>
        <xsl:apply-templates/>
      </strong>
    </div>
  </xsl:template>

  <!-- DocBook customization template -->
  <xsl:template name="tr.attributes">
    <xsl:param name="row" select="."/>
    <xsl:param name="rownum" select="0"/>

    <xsl:if test="$row/@role">
      <xsl:attribute name="class">
        <xsl:value-of select="$row/@role"/>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Paragraphs -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    para ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*
  -->
  <xsl:template match="para">
    <p>
      <xsl:if test="@role">
        <xsl:attribute name="class">
          <xsl:value-of select="@role"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="@*|node()"/>
    </p>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Graphics -->
  <!-- ================================================================== -->

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
  <xsl:template match="mediaobject">
    <!-- for now we only support imageobject -->
    <xsl:apply-templates select="imageobject[1]"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    imageobject ::=
    (objectinfo?,imagedata)

    imagedata ::=
    EMPTY
    attributes: fileref
                width
                depth
                scale
                scalefit
                format=BMP|GIF|JPEG|PNG|etc. (see the docs)
                align=center|left|right
                entityref
                srccredit
  -->
  <xsl:template match="imageobject">
    <xsl:if test="imagedata/@fileref">
      <xsl:variable name="data" select="imagedata[1]"/>
      <xsl:if test="$data/@fileref">
        <xsl:choose>
          <xsl:when test="$data/@align='center'">
            <div style="text-align: center">
              <img src="{$data/@fileref}">
                <xsl:apply-templates select="@id"/> <!-- add ID, if any -->
                <xsl:apply-templates select="$data/@*"/>
              </img>
            </div>
          </xsl:when>
          <xsl:otherwise>
            <img src="{$data/@fileref}">
              <xsl:apply-templates select="@id"/>
              <xsl:apply-templates select="$data/@*"/>
            </img>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
    </xsl:if>
  </xsl:template>

  <xsl:template match="imagedata/@width">
    <xsl:attribute name="width">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="imagedata/@depth">
    <xsl:attribute name="height">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="imagedata/@align[.!='center']">
    <xsl:attribute name="align">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <!-- FIXME: support other attributes -->

  <!-- ================================================================== -->
  <!-- Miscellaneous -->
  <!-- ================================================================== -->

  <!--
    blockquote ::=
       (title?,attribution?,
        (itemizedlist|orderedlist|variablelist|note|literallayout|
         programlisting|para|blockquote|mediaobject|informaltable|
         example|figure|table|sidebar|abstract|authorblurb|epigraph)+)
  -->
  <xsl:template match="blockquote">
    <div class="blockquote">
      <xsl:apply-templates select="@*"/>
      <xsl:choose>
        <xsl:when test="attribution">
          <table border="0" width="100%" cellspacing="0" cellpadding="0"
                 class="blockquote" summary="Block quote">
            <tr>
              <td width="10%" valign="top">&#160;</td>
              <td width="80%" valign="top">
                <xsl:apply-templates select="*"/>
              </td>
              <td width="10%" valign="top">&#160;</td>
            </tr>
            <tr>
              <td width="10%" valign="top">&#160;</td>
              <td colspan="2" align="right" valign="top">
                <xsl:apply-templates select="attribution" mode="attribution"/>
              </td>
            </tr>
          </table>
        </xsl:when>
        <xsl:otherwise>
          <blockquote class="blockquote">
            <xsl:apply-templates select="*"/>
          </blockquote>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template match="blockquote/title">
    <div class="title">
      <b>
        <xsl:apply-templates/>
      </b>
    </div>
  </xsl:template>

  <!--
    epigraph ::= (attribution?, (para+))
  -->
  <xsl:template match="epigraph">
    <div class="epigraph">
      <xsl:apply-templates select="@*|*"/>
      <xsl:apply-templates select="attribution" mode="attribution"/>
    </div>
  </xsl:template>

  <!--
    attribution ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*
  -->
  <xsl:template match="attribution"/>

  <xsl:template match="attribution" mode="attribution">
    <span>
      <xsl:text>--</xsl:text>
      <span class="attribution">
        <xsl:apply-templates/>
      </span>
    </span>
  </xsl:template>

  <!--
    sidebar ::=
    ((title,titleabbrev?)?,
     (itemizedlist|orderedlist|variablelist|note|literallayout|
      programlisting|para|blockquote|mediaobject|informaltable|
      example|figure|table)+)
  -->
  <xsl:template match="sidebar">
    <div class="sidebar">
      <xsl:apply-templates select="@*|*"/>
    </div>
  </xsl:template>

  <xsl:template match="sidebar/title">
    <div class="title">
      <b>
        <xsl:apply-templates/>
      </b>
    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- INLINE DISPLAY ELEMENTS -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- Traditional Publishing Inlines -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    abbrev ::=
    (#PCDATA|acronym|emphasis|trademark|link|ulink|inlinemediaobject)*
  -->
  <xsl:template match="abbrev">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    acronym ::=
    (#PCDATA|acronym|emphasis|trademark|link|ulink|inlinemediaobject)*
  -->
  <xsl:template match="acronym">
    <xsl:call-template name="inline-element"/>
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
    <xsl:call-template name="inline-element">
      <xsl:with-param name="element">
        <xsl:choose>
          <xsl:when test="@role = 'strong' or @role = 'bold'">strong</xsl:when>
          <xsl:otherwise>em</xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    phrase ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*
  -->
  <xsl:template match="phrase">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="class">
        <xsl:choose>
          <xsl:when test="@role">
            <xsl:value-of select="@role"/>
          </xsl:when>
          <xsl:otherwise>phrase</xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    quote ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*
  -->
  <xsl:template match="quote">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="prefix">&#8220;</xsl:with-param>
      <xsl:with-param name="suffix">&#8221;</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    trademark ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject|
     emphasis)*

    attributes: class = (copyright|registered|service|trade); default: trade
  -->
  <xsl:template match="trademark">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="suffix">
        <sup class="trademark">
          <xsl:choose>
            <xsl:when test="@class='registered'">&#174;</xsl:when>
            <xsl:when test="@class='service'">&#8480;</xsl:when>
            <xsl:when test="@class='copyright'">&#169;</xsl:when>
            <xsl:otherwise>&#8482;</xsl:otherwise>
          </xsl:choose>
        </sup>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Cross References -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    anchor ::= EMPTY

       attributes: id=ID (required)
                   pagenum=CDATA
                   remap=CDATA
                   xreflabel=CDATA
                   revisionflag=(added|changed|deleted|off)
                   role=CDATA
  -->

  <xsl:template match="anchor">
    <xsl:if test="not(@id)">
      <xsl:message terminate="yes">
        <xsl:text>ERROR: 'anchor' element without id.</xsl:text>
      </xsl:message>
    </xsl:if>
    <a name="{@id}"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    citetitle ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*

       attributes: pubwork=(article|book|chapter|journal|manuscript|part|
                            refentry|section|series|set)
  -->
  <xsl:template match="citetitle">
    <!-- Often italicized for Books and quoted for Articles. -->
    <xsl:choose>
      <xsl:when test="@pubwork = 'article'">
        <xsl:call-template name="inline-element">
          <xsl:with-param name="prefix">&#8220;</xsl:with-param>
          <xsl:with-param name="suffix">&#8221;</xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inline-element">
          <xsl:with-param name="display" select="'italic'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

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

  <xsl:key name="element-by-id" match="*" use="@id"/>

  <xsl:template match="link">
    <xsl:variable name="targets" select="key('element-by-id', @linkend)"/>
    <xsl:variable name="linkend" select="$targets[1]"/>

    <xsl:choose>
      <xsl:when test="count($targets) = 0">
        <xsl:message terminate="yes">
          <xsl:text>ERROR: No ID for linkend '</xsl:text>
          <xsl:value-of select="@linkend"/>
          <xsl:text>'.</xsl:text>
        </xsl:message>
      </xsl:when>
      <xsl:when test="count($targets) &gt; 1">
        <xsl:message>
          <xsl:text>WARNING: Mulitple IDs for linkend '</xsl:text>
          <xsl:value-of select="@linkend"/>
          <xsl:text>'.</xsl:text>
        </xsl:message>
      </xsl:when>
      <xsl:otherwise>
        <a href="#{@linkend}">
          <xsl:if test="@id">
            <xsl:attribute name="name">
              <xsl:value-of select="@id"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="$linkend/title">
            <xsl:attribute name="title">
              <xsl:value-of select="$linkend/title"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:choose>
            <xsl:when test="node()">
              <xsl:apply-templates/>
            </xsl:when>
            <xsl:when test="@endterm">
              <xsl:variable name="endterm" select="key('element-by-id',
                                                       @endterm)"/>
              <xsl:choose>
                <xsl:when test="count($endterm) = 0">
                  <xsl:message terminate="yes">
                    <xsl:text>ERROR: No ID for endterm '</xsl:text>
                    <xsl:value-of select="@endterm"/>
                    <xsl:text>'.</xsl:text>
                  </xsl:message>
                </xsl:when>
                <xsl:when test="count($endterm) &gt; 1">
                  <xsl:message>
                    <xsl:text>WARNING: Mulitple IDs for endterm '</xsl:text>
                    <xsl:value-of select="@endterm"/>
                    <xsl:text>'.</xsl:text>
                  </xsl:message>
                </xsl:when>
              </xsl:choose>
              <xsl:apply-templates select="$endterm[1]"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:message>
                <xsl:text>WARNING: 'link' element without content or</xsl:text>
                <xsl:text> endterm.  Nothing to show for link to '</xsl:text>
                <xsl:value-of select="$linkend"/>
                <xsl:text>'.</xsl:text>
              </xsl:message>
              <xsl:text>[ link ]</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    ulink ::=
    (#PCDATA|footnoteref|xref|abbrev|acronym|citetitle|emphasis|
     footnote|phrase|quote|trademark|link|ulink|command|
     computeroutput|email|filename|literal|option|replaceable|
     systemitem|userinput|inlinemediaobject)*

    attributes: url=CDATA (required)
                type=CDATA
  -->
  <xsl:template match="ulink[not(@url)]" mode="VALIDATE">
    <xsl:message terminate="yes">
      <xsl:text>ERROR: '</xsl:text>
      <xsl:value-of select="local-name()"/>
      <xsl:text>' element missing required 'url' attribute.</xsl:text>
    </xsl:message>
    <xsl:apply-templates select="*" mode="VALIDATE"/>
  </xsl:template>

  <xsl:template match="ulink">
    <a href="{@url}">
      <xsl:if test="@id">
        <xsl:attribute name="name">
          <xsl:value-of select="@id"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="@*"/>
      <xsl:if test="@type='off-site'">
        <xsl:attribute name="target">_new</xsl:attribute>
      </xsl:if>
      <xsl:choose>
        <xsl:when test="normalize-space()">
          <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="style">font-family: "Andale Mono","Lucida Console",monospace</xsl:attribute>
          <xsl:value-of select="@url"/>
        </xsl:otherwise>
      </xsl:choose>
    </a>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    xref ::= EMPTY

    attributes: linkend=IDREF (required)
                endterm=IDREF
  -->
  <xsl:template match="xref">
    <xsl:variable name="targets" select="key('element-by-id', @linkend)"/>
    <xsl:variable name="linkend" select="$targets[1]"/>

    <xsl:choose>
      <xsl:when test="count($targets) = 0">
        <xsl:message terminate="yes">
          <xsl:text>ERROR: No ID for linkend '</xsl:text>
          <xsl:value-of select="@linkend"/>
          <xsl:text>'.</xsl:text>
        </xsl:message>
      </xsl:when>
      <xsl:when test="count($targets) &gt; 1">
        <xsl:message>
          <xsl:text>WARNING: Mulitple IDs for linkend '</xsl:text>
          <xsl:value-of select="@linkend"/>
          <xsl:text>'.</xsl:text>
        </xsl:message>
      </xsl:when>
      <xsl:otherwise>
        <a href="#{@linkend}">
          <xsl:if test="@id">
            <xsl:attribute name="name">
              <xsl:value-of select="@id"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="$linkend/title">
            <xsl:attribute name="title">
              <xsl:value-of select="$linkend/title"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:choose>
            <xsl:when test="@endterm">
              <xsl:variable name="endterm" select="key('element-by-id',
                                                       @endterm)"/>
              <xsl:choose>
                <xsl:when test="count($endterm) = 0">
                  <xsl:message terminate="yes">
                    <xsl:text>ERROR: No ID for endterm '</xsl:text>
                    <xsl:value-of select="@endterm"/>
                    <xsl:text>'.</xsl:text>
                  </xsl:message>
                </xsl:when>
                <xsl:when test="count($endterm) &gt; 1">
                  <xsl:message>
                    <xsl:text>WARNING: Mulitple IDs for endterm '</xsl:text>
                    <xsl:value-of select="@endterm"/>
                    <xsl:text>'.</xsl:text>
                  </xsl:message>
                </xsl:when>
              </xsl:choose>
              <xsl:apply-templates select="$endterm[1]"/>
            </xsl:when>
            <xsl:when test="normalize-space($linkend/@xreflabel)">
              <xsl:value-of select="normalize-space($linkend/@xreflabel)"/>
            </xsl:when>
            <xsl:when test="$linkend/title">
              <xsl:text>&#8220;</xsl:text>
              <xsl:apply-templates select="$linkend/title" mode="MARKUP"/>
              <xsl:text>&#8221;</xsl:text>
            </xsl:when>
            <xsl:when test="$linkend/self::biblioentry or
                            $linkend/self::bibliomixed">
              <xsl:text>[</xsl:text>
              <xsl:choose>
                <xsl:when test="$linkend/*/abbrev">
                  <xsl:apply-templates select="$linkend/*/abbrev"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="@linkend"/>
                </xsl:otherwise>
              </xsl:choose>
              <xsl:text>]</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <!-- If all else fails, we take the first 10 characters
                   of the text value of the target, then elide the rest. -->
              <xsl:text>&#8220;</xsl:text>
              <xsl:value-of select="substring($linkend, 1, 10)"/>
              <xsl:text> &#8230;&#8221;</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Markup -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    computeroutput ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*

       attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="computeroutput">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    literal ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*

     attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="literal">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    replaceable ::= (#PCDATA|link|ulink|inlinemediaobject)*

    attributes: class=command|function|option|parameter (default: none)
  -->
  <xsl:template match="replaceable">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'italic'"/>
      <xsl:with-param name="content">
        <tt>
          <xsl:call-template name="inline-content"/>
        </tt>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    userinput ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*

    attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="userinput">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Operating Systems -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    command ::=
    (#PCDATA|link|ulink|command|computeroutput|email|filename|literal|
     option|replaceable|systemitem|userinput|inlinemediaobject)*

    attributes: moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="command">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'bold'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    filename ::= (#PCDATA|replaceable|inlinemediaobject)*

    attributes: class=(devicefile|directory|headerfile|libraryfile|
                       symlink)
                moreinfo=(none|refentry) (default: none)
                path=CDATA
  -->
  <xsl:template match="filename">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    option ::= (#PCDATA|replaceable|inlinemediaobject)*
  -->
  <xsl:template match="option">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    systemitem ::= (#PCDATA|replaceable|inlinemediaobject|acronym)*

    attributes: class=(constant|groupname|library|macro|osname|resource|
                       systemname|username)
                moreinfo=none|refentry (default: none)
  -->
  <xsl:template match="systemitem">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- General -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
    email ::=
    (#PCDATA|link|ulink|emphasis|trademark|replaceable|inlinemediaobject)*
  -->
  <xsl:template match="email">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
      <xsl:with-param name="prefix" select="'&lt;'"/>
      <xsl:with-param name="content">
        <xsl:choose>
          <xsl:when test="contains(., '@')">
            <a href="mailto:{substring-before(.,'@')}%40{substring-after(.,'@')}">
              <xsl:call-template name="inline-content"/>
            </a>
          </xsl:when>
          <xsl:otherwise>
            <xsl:call-template name="inline-content"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
      <xsl:with-param name="suffix" select="'&gt;'"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="email//text()">
    <xsl:choose>
      <xsl:when test="contains(., '@')">
        <xsl:value-of select="substring-before(.,'@')"/>
        <xsl:text disable-output-escaping="yes">&amp;#64;</xsl:text>
        <xsl:value-of select="substring-after(.,'@')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="."/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
    footnote ::=
       ((itemizedlist|orderedlist|variablelist|literallayout|
         programlisting|para|blockquote|mediaobject|informaltable)+)

      attributes: label=CDATA

    footnoteref ::= EMPTY
      attributes: linkend=IDREF (required; points to some 'id' attr)
                  label=CDATA
  -->
  <xsl:template match="footnoteref" mode="VALIDATE">
    <xsl:if test="not(key('footnotes', @linkend))">
      <xsl:message terminate="yes">
        <xsl:text>ERROR: Footnote with ID '</xsl:text>
        <xsl:value-of select="@linkend"/>
        <xsl:text>' not found in document.</xsl:text>
      </xsl:message>
    </xsl:if>
  </xsl:template>

  <xsl:template match="footnote">
    <xsl:param name="linkend" select="true()"/>

    <xsl:variable name="name">
      <xsl:choose>
        <xsl:when test="@id">
          <xsl:value-of select="@id"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="generate-id()"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <sup class="footnotemark">
      <xsl:text>[</xsl:text>
      <a href="{concat('#ftn.', $name)}">
        <xsl:if test="$linkend">
          <xsl:attribute name="name">
            <xsl:value-of select="$name"/>
          </xsl:attribute>
        </xsl:if>
        <xsl:call-template name="footnote.number"/>
      </a>
      <xsl:text>]</xsl:text>
    </sup>
  </xsl:template>

  <xsl:template match="footnoteref">
    <xsl:apply-templates select="key('footnotes', @linkend)[1]">
      <xsl:with-param name="linkend" select="false()"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template name="display.footnotes">
    <xsl:param name="footnotes" select=".//footnote"/>

    <dl class="footnotes">
      <xsl:for-each select="$footnotes">
        <dt class="footnotemark">
          <xsl:text>[</xsl:text>
          <xsl:call-template name="footnote.number"/>
          <xsl:text>]</xsl:text>
        </dt>
        <dd class="footnote">
          <xsl:apply-templates select="*"/>
        </dd>
      </xsl:for-each>
    </dl>
  </xsl:template>

  <xsl:template name="footnote.number">
    <xsl:choose>
      <xsl:when test="string-length(@label)">
        <xsl:value-of select="@label"/>
      </xsl:when>
      <xsl:when test="ancestor::tgroup">
        <xsl:number
          level="any"
          from="tgroup"
          count="footnote[not(@label)]"
          format="a"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:number
          level="any"
          count="footnote[not(@label)][not(ancestor::tgroup)]"
          format="1"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->

</xsl:stylesheet>
