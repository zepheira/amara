<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:import href="sdocbook_html.xslt"/>

  <xsl:param name="css-file" select="'docbook_html.css'"/>

  <!-- ================================================================== -->
  <!-- BLOCK ELEMENTS -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- Admonitions -->
  <!-- ================================================================== -->

  <xsl:template name="admonition">
    <xsl:param name="title"/>

    <div class="{local-name()}">
      <xsl:apply-templates select="@*"/>
      <xsl:if test="not(title)">
        <span class="label"><xsl:value-of select="$title"/></span>
      </xsl:if>
      <xsl:apply-templates select="*"/>
    </div>
  </xsl:template>

  <xsl:template match="caution/title
                       | important/title
                       | tip/title
                       | warning/title">
    <span class="label">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     caution ::=
     (title?,
      (calloutlist|glosslist|bibliolist|itemizedlist|orderedlist|
       segmentedlist|simplelist|variablelist|literallayout|
       programlisting|programlistingco|screen|screenco|screenshot|
       synopsis|cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
       constructorsynopsis|destructorsynopsis|methodsynopsis|
       formalpara|para|simpara|address|blockquote|graphic|graphicco|
       mediaobject|mediaobjectco|informalequation|informalexample|
       informalfigure|informaltable|equation|example|figure|table|
       procedure|sidebar|anchor|bridgehead|remark|indexterm|beginpage)+)
  -->

  <xsl:template match="caution">
    <xsl:call-template name="admonition">
      <xsl:with-param name="title" select="'Caution'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     important ::=
     (title?,
      (calloutlist|glosslist|bibliolist|itemizedlist|orderedlist|
       segmentedlist|simplelist|variablelist|literallayout|
       programlisting|programlistingco|screen|screenco|screenshot|
       synopsis|cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
       constructorsynopsis|destructorsynopsis|methodsynopsis|
       formalpara|para|simpara|address|blockquote|graphic|graphicco|
       mediaobject|mediaobjectco|informalequation|informalexample|
       informalfigure|informaltable|equation|example|figure|table|
       procedure|sidebar|anchor|bridgehead|remark|indexterm|beginpage)+)
  -->

  <xsl:template match="important">
    <xsl:call-template name="admonition">
      <xsl:with-param name="title" select="'Important'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     tip ::=
     (title?,
      (calloutlist|glosslist|bibliolist|itemizedlist|orderedlist|
       segmentedlist|simplelist|variablelist|literallayout|
       programlisting|programlistingco|screen|screenco|screenshot|
       synopsis|cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
       constructorsynopsis|destructorsynopsis|methodsynopsis|
       formalpara|para|simpara|address|blockquote|graphic|graphicco|
       mediaobject|mediaobjectco|informalequation|informalexample|
       informalfigure|informaltable|equation|example|figure|table|
       procedure|sidebar|anchor|bridgehead|remark|indexterm|beginpage)+)
  -->

  <xsl:template match="tip">
    <xsl:call-template name="admonition">
      <xsl:with-param name="title" select="'Tip'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     warning ::=
     (title?,
      (calloutlist|glosslist|bibliolist|itemizedlist|orderedlist|
       segmentedlist|simplelist|variablelist|literallayout|
       programlisting|programlistingco|screen|screenco|screenshot|
       synopsis|cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
       constructorsynopsis|destructorsynopsis|methodsynopsis|
       formalpara|para|simpara|address|blockquote|graphic|graphicco|
       mediaobject|mediaobjectco|informalequation|informalexample|
       informalfigure|informaltable|equation|example|figure|table|
       procedure|sidebar|anchor|bridgehead|remark|indexterm|beginpage)+)
  -->

  <xsl:template match="warning">
    <xsl:call-template name="admonition">
      <xsl:with-param name="title" select="'Warning'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Line-specific layouts -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
     screen ::=
     (#PCDATA|footnoteref|xref|biblioref|abbrev|acronym|citation|
      citerefentry|citetitle|emphasis|firstterm|foreignphrase|
      glossterm|footnote|phrase|orgname|quote|trademark|wordasword|
      personname|link|olink|ulink|action|application|classname|
      methodname|interfacename|exceptionname|ooclass|oointerface|
      ooexception|package|command|computeroutput|database|email|envar|
      errorcode|errorname|errortype|errortext|filename|function|
      guibutton|guiicon|guilabel|guimenu|guimenuitem|guisubmenu|
      hardware|interface|keycap|keycode|keycombo|keysym|literal|code|
      constant|markup|medialabel|menuchoice|mousebutton|option|
      optional|parameter|prompt|property|replaceable|returnvalue|
      sgmltag|structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|author|authorinitials|
      corpauthor|corpcredit|modespec|othercredit|productname|
      productnumber|revhistory|remark|subscript|superscript|
      inlinegraphic|inlinemediaobject|inlineequation|synopsis|
      cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
      constructorsynopsis|destructorsynopsis|methodsynopsis|indexterm|
      beginpage|co|coref|textobject|lineannotation)*

      attributes: linenumbering=numbered|unnumbered
                  width=CDATA
  -->
  <xsl:template match="screen">
    <div class="screen">
      <xsl:apply-templates select="@*"/>
      <!-- pre necessary because CSS1's white-space:pre can be ignored -->
      <pre>
        <xsl:apply-templates/>
      </pre>
    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     synopsis ::=
     (#PCDATA|footnoteref|xref|biblioref|abbrev|acronym|citation|
      citerefentry|citetitle|emphasis|firstterm|foreignphrase|
      glossterm|footnote|phrase|orgname|quote|trademark|wordasword|
      personname|link|olink|ulink|action|application|classname|
      methodname|interfacename|exceptionname|ooclass|oointerface|
      ooexception|package|command|computeroutput|database|email|envar|
      errorcode|errorname|errortype|errortext|filename|function|
      guibutton|guiicon|guilabel|guimenu|guimenuitem|guisubmenu|
      hardware|interface|keycap|keycode|keycombo|keysym|literal|code|
      constant|markup|medialabel|menuchoice|mousebutton|option|
      optional|parameter|prompt|property|replaceable|returnvalue|
      sgmltag|structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|author|authorinitials|
      corpauthor|corpcredit|modespec|othercredit|productname|
      productnumber|revhistory|remark|subscript|superscript|
      inlinegraphic|inlinemediaobject|inlineequation|synopsis|
      cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
      constructorsynopsis|destructorsynopsis|methodsynopsis|indexterm|
      beginpage|co|coref|textobject|lineannotation)*

      attributes: format=linespecific
                  linenumbering=numbered|unnumbered
                  label=CDATA
  -->
  <xsl:template match="synopsis">
    <div class="synopsis">
      <xsl:apply-templates select="@*"/>
      <!-- pre necessary because CSS1's white-space:pre can be ignored -->
      <pre>
        <xsl:apply-templates/>
      </pre>
    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Programming languages and constructs -->
  <!-- ================================================================== -->

  <xsl:template match="classsynopsis
                       | fieldsynopsis
                       | methodsynopsis
                       | constructorsynopsis
                       | destructorsynopsis">
    <xsl:param name="language">
      <xsl:choose>
        <xsl:when test="@language">
          <xsl:value-of select="@language"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>python</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:param>
    <xsl:choose>
      <xsl:when test="$language = 'python'">
        <xsl:apply-templates select="." mode="python"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:message>
          <xsl:text>Unrecognized language '</xsl:text>
          <xsl:value-of select="$language"/>
          <xsl:text>' on '</xsl:text>
          <xsl:value-of select="local-name()"/>
          <xsl:text>' element. </xsl:text>
        </xsl:message>
        <xsl:apply-templates select="." mode="python"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     constructorsynopsis ::=
     (modifier*,methodname?,
      (methodparam+|void?),
      exceptionname*)

     destructorsynopsis ::=
     (modifier*,methodname?,
      (methodparam+|void?),
      exceptionname*)

       attributes: language=CDATA
  -->

  <!-- ================================================================== -->
  <!--
     methodsynopsis ::=
     (modifier*,
      (type|void)?,
      methodname,
      (methodparam+|void?),
      exceptionname*,modifier*)

       attributes: language=CDATA
  -->

  <xsl:template match="methodsynopsis" mode="python">
    <code class="methodsynopsis">
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates select="methodname" mode="python"/>
      <xsl:text>(</xsl:text>
      <xsl:apply-templates select="methodparam" mode="python"/>
      <xsl:text>)</xsl:text>
    </code>
  </xsl:template>

  <xsl:template match="methodname" mode="python">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <xsl:template match="methodparam" mode="python">
    <xsl:if test="position() &gt; 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <span class="methodparam">
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates select="*" mode="python"/>
    </span>
  </xsl:template>

  <xsl:template match="parameter" mode="python">
    <var class="parameter">
      <xsl:apply-templates select="@*|node()"/>
    </var>
  </xsl:template>

  <xsl:template match="initializer" mode="python">
    <xsl:text>=</xsl:text>
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <xsl:template match="*" mode="python">
    <!-- switch to 'normal' mode to catch any unimplemented elements -->
    <xsl:apply-templates select="."/>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Miscellaneous -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
     XXX - implement
     cmdsynopsis ::=
     ((command|arg|group|sbr)+,
      synopfragment*)

       attributes: sepchar=CDATA (default: " ")
                   cmdlength=CDATA
                   label=CDATA
  -->

  <!-- ================================================================== -->
  <!--
     funcsynopsis ::=
     ((funcsynopsisinfo|funcprototype)+)

       attributes: label=CDATA
  -->

  <xsl:template match="funcsynopsis">
    <xsl:call-template name="block-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     funcprototype ::=
     (modifier*,funcdef,
      (void|varargs|
       (paramdef+,varargs?)),
      modifier*)
    -->

  <xsl:template match="funcdef" mode="VALIDATE">
    <xsl:if test="not(function)">
      <xsl:message>
        <xsl:text>WARNING: 'funcdef' element without function name</xsl:text>
        <xsl:text> (missing 'function' element).</xsl:text>
      </xsl:message>
    </xsl:if>
  </xsl:template>

  <xsl:template match="paramdef" mode="VALIDATE">
    <xsl:if test="not(parameter)">
      <xsl:message>
        <xsl:text>WARNING: 'paramdef' element without parameter name</xsl:text>
        <xsl:text> (missing 'parameter' element).</xsl:text>
      </xsl:message>
    </xsl:if>
  </xsl:template>

  <xsl:template match="funcprototype">
    <code class="funcprototype">
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates select="funcdef" mode="function"/>
      <xsl:text>(</xsl:text>
      <xsl:apply-templates select="void|varargs|paramdef" mode="function"/>
      <xsl:text>)</xsl:text>
    </code>
  </xsl:template>

  <xsl:template match="funcdef" mode="function">
    <span class="funcdef">
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates mode="function"/>
    </span>
  </xsl:template>

  <xsl:template match="function" mode="function">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'bold'"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="void" mode="function"/>

  <xsl:template match="varargs" mode="function">
    <xsl:if test="position() &gt; 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:text><!--horizontal ellipsis-->&#x2026;</xsl:text>
  </xsl:template>

  <xsl:template match="paramdef" mode="function">
    <xsl:if test="position() &gt; 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <span class="paramdef">
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates mode="function"/>
    </span>
  </xsl:template>

  <xsl:template match="parameter" mode="function">
    <var class="parameter">
      <xsl:apply-templates select="@*|node()"/>
    </var>
  </xsl:template>

  <xsl:template match="initializer" mode="function">
    <xsl:text>=</xsl:text>
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <xsl:template match="*" mode="function">
    <!-- switch to 'normal' mode to catch any unimplemented elements -->
    <xsl:apply-templates select="."/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     highlights ::=
     ((calloutlist|glosslist|bibliolist|itemizedlist|orderedlist|
       segmentedlist|simplelist|variablelist|caution|important|note|
       tip|warning|formalpara|para|simpara|indexterm)+)
  -->

  <xsl:template match="highlights">
    <xsl:call-template name="block-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     XXX - implement
     msgset ::=
     (blockinfo?,
      (title,titleabbrev?)?,
      (msgentry+|simplemsgentry+))
  -->

  <!-- ================================================================== -->
  <!--
     XXX - implement
     procedure ::=
     (blockinfo?,
      (title,titleabbrev?)?,
      (calloutlist|glosslist|bibliolist|itemizedlist|orderedlist|
       segmentedlist|simplelist|variablelist|caution|important|note|
       tip|warning|literallayout|programlisting|programlistingco|
       screen|screenco|screenshot|synopsis|cmdsynopsis|funcsynopsis|
       classsynopsis|fieldsynopsis|constructorsynopsis|
       destructorsynopsis|methodsynopsis|formalpara|para|simpara|
       address|blockquote|graphic|graphicco|mediaobject|mediaobjectco|
       informalequation|informalexample|informalfigure|informaltable|
       equation|example|figure|table|msgset|procedure|sidebar|qandaset|
       task|productionset|constraintdef|anchor|bridgehead|remark|
       highlights|abstract|authorblurb|epigraph|indexterm|beginpage)*,
      step+)
  -->

  <!-- ================================================================== -->
  <!-- INLINE DISPLAY ELEMENTS -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- Markup -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
     markup ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="markup">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     sgmltag ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="sgmltag">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
      <xsl:with-param name="content">
        <xsl:choose>
          <xsl:when test="@class = 'attribute'">
            <xsl:apply-templates/>
          </xsl:when>
          <xsl:when test="@class = 'attvalue'">
            <xsl:apply-templates/>
          </xsl:when>
          <xsl:when test="@class = 'element'">
            <xsl:apply-templates/>
          </xsl:when>
          <xsl:when test="@class = 'emptytag'">
            <xsl:text>&lt;</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>/&gt;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'endtag'">
            <xsl:text>&lt;/</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>&gt;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'genentity'">
            <xsl:text>&amp;</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'numcharref'">
            <xsl:text>&amp;#</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'paramentity'">
            <xsl:text>%</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'pi'">
            <xsl:text>&lt;?</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>&gt;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'sgmlcomment'">
            <xsl:text>&lt;!--</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>--&gt;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'starttag'">
            <xsl:text>&lt;</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>&gt;</xsl:text>
          </xsl:when>
          <xsl:when test="@class = 'xmlpi'">
            <xsl:text>&lt;?</xsl:text>
            <xsl:apply-templates/>
            <xsl:text>?&gt;</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Programming languages and constructs -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
     classname ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="classname">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     code ::=
     (#PCDATA|link|olink|ulink|action|application|classname|methodname|
      interfacename|exceptionname|ooclass|oointerface|ooexception|
      package|command|computeroutput|database|email|envar|errorcode|
      errorname|errortype|errortext|filename|function|guibutton|
      guiicon|guilabel|guimenu|guimenuitem|guisubmenu|hardware|
      interface|keycap|keycode|keycombo|keysym|literal|code|constant|
      markup|medialabel|menuchoice|mousebutton|option|optional|
      parameter|prompt|property|replaceable|returnvalue|sgmltag|
      structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|remark|subscript|
      superscript|inlinegraphic|inlinemediaobject|indexterm|beginpage)*
  -->

  <xsl:template match="code">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     exceptionname ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="exceptionname">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     interfacename ::=
     (#PCDATA|link|olink|ulink|action|application|classname|methodname|
      interfacename|exceptionname|ooclass|oointerface|ooexception|
      package|command|computeroutput|database|email|envar|errorcode|
      errorname|errortype|errortext|filename|function|guibutton|
      guiicon|guilabel|guimenu|guimenuitem|guisubmenu|hardware|
      interface|keycap|keycode|keycombo|keysym|literal|code|constant|
      markup|medialabel|menuchoice|mousebutton|option|optional|
      parameter|prompt|property|replaceable|returnvalue|sgmltag|
      structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|remark|subscript|
      superscript|inlinegraphic|inlinemediaobject|indexterm|beginpage)*
  -->

  <xsl:template match="interfacename">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     methodname ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="methodname">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     constant ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="constant">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     errorcode ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="errorcode">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     errorname ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="errorname">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     errortype ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="errortype">
    <xsl:call-template name="inline-element"/>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     function ::=
     (#PCDATA|link|olink|ulink|action|application|classname|methodname|
      interfacename|exceptionname|ooclass|oointerface|ooexception|
      package|command|computeroutput|database|email|envar|errorcode|
      errorname|errortype|errortext|filename|function|guibutton|
      guiicon|guilabel|guimenu|guimenuitem|guisubmenu|hardware|
      interface|keycap|keycode|keycombo|keysym|literal|code|constant|
      markup|medialabel|menuchoice|mousebutton|option|optional|
      parameter|prompt|property|replaceable|returnvalue|sgmltag|
      structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|remark|subscript|
      superscript|inlinegraphic|inlinemediaobject|indexterm|beginpage)*
  -->

  <xsl:template match="function">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     parameter ::=
     (#PCDATA|link|olink|ulink|action|application|classname|methodname|
      interfacename|exceptionname|ooclass|oointerface|ooexception|
      package|command|computeroutput|database|email|envar|errorcode|
      errorname|errortype|errortext|filename|function|guibutton|
      guiicon|guilabel|guimenu|guimenuitem|guisubmenu|hardware|
      interface|keycap|keycode|keycombo|keysym|literal|code|constant|
      markup|medialabel|menuchoice|mousebutton|option|optional|
      parameter|prompt|property|replaceable|returnvalue|sgmltag|
      structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|remark|subscript|
      superscript|inlinegraphic|inlinemediaobject|indexterm|beginpage)*
  -->

  <xsl:template match="parameter">
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
     property ::=
     (#PCDATA|link|olink|ulink|action|application|classname|methodname|
      interfacename|exceptionname|ooclass|oointerface|ooexception|
      package|command|computeroutput|database|email|envar|errorcode|
      errorname|errortype|errortext|filename|function|guibutton|
      guiicon|guilabel|guimenu|guimenuitem|guisubmenu|hardware|
      interface|keycap|keycode|keycombo|keysym|literal|code|constant|
      markup|medialabel|menuchoice|mousebutton|option|optional|
      parameter|prompt|property|replaceable|returnvalue|sgmltag|
      structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|remark|subscript|
      superscript|inlinegraphic|inlinemediaobject|indexterm|beginpage)*
  -->

  <xsl:template match="property">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
     varname ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="varname">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- General -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
     uri ::=
     (#PCDATA|replaceable|inlinegraphic|inlinemediaobject|indexterm|
      beginpage)*
  -->

  <xsl:template match="uri">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'monospace'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- Miscellaneous -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!--
     remark ::=
     (#PCDATA|link|olink|ulink|action|application|classname|methodname|
      interfacename|exceptionname|ooclass|oointerface|ooexception|
      package|command|computeroutput|database|email|envar|errorcode|
      errorname|errortype|errortext|filename|function|guibutton|
      guiicon|guilabel|guimenu|guimenuitem|guisubmenu|hardware|
      interface|keycap|keycode|keycombo|keysym|literal|code|constant|
      markup|medialabel|menuchoice|mousebutton|option|optional|
      parameter|prompt|property|replaceable|returnvalue|sgmltag|
      structfield|structname|symbol|systemitem|uri|token|type|
      userinput|varname|nonterminal|anchor|remark|subscript|
      superscript|inlinegraphic|inlinemediaobject|indexterm|beginpage)*
  -->
  <xsl:template match="firstterm|remark">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'italic'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ================================================================== -->
  <!--
      firstterm ::=
      (#PCDATA|footnoteref|xref|biblioref|abbrev|acronym|citation|
       citerefentry|citetitle|citebiblioid|emphasis|firstterm|
       foreignphrase|glossterm|termdef|footnote|phrase|orgname|quote|
       trademark|wordasword|personname|link|olink|ulink|action|
       application|classname|methodname|interfacename|exceptionname|
       ooclass|oointerface|ooexception|package|command|computeroutput|
       database|email|envar|errorcode|errorname|errortype|errortext|
       filename|function|guibutton|guiicon|guilabel|guimenu|guimenuitem|
       guisubmenu|hardware|interface|keycap|keycode|keycombo|keysym|
       literal|code|constant|markup|medialabel|menuchoice|mousebutton|
       option|optional|parameter|prompt|property|replaceable|
       returnvalue|sgmltag|structfield|structname|symbol|systemitem|uri|
       token|type|userinput|varname|nonterminal|anchor|author|
       authorinitials|corpauthor|corpcredit|modespec|othercredit|
       productname|productnumber|revhistory|remark|subscript|
       superscript|inlinegraphic|inlinemediaobject|inlineequation|
       synopsis|cmdsynopsis|funcsynopsis|classsynopsis|fieldsynopsis|
       constructorsynopsis|destructorsynopsis|methodsynopsis|indexterm|
       beginpage)*

      attributes: linkend=IDREF (optional; points to a glossterm 'id' attr)
                  baseform=CDATA (optional; the glossterm, if different
                  from the firstterm, like when the firstterm is the plural
                  form)
      FIXME: support these attributes.
  -->
  <xsl:template match="firstterm">
    <xsl:call-template name="inline-element">
      <xsl:with-param name="display" select="'italic'"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
