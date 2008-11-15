<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html"/>

	<!-- Demo of Transformation of CDATA newlines to HTML <br> tags       -->
	<!-- Version: 1.1 (08 Nov 1999)                                       -->
	<!-- Author: mbrown@corp.webb.net (Mike J Brown)                      -->
	<!-- XSLT Version: 1.0 (08 Oct 1999 proposed recommendation)          -->
	<!-- License: none; no restrictions                                   -->
	<!-- -->
	<!-- Overview:                                                        -->
	<!--                                                                  -->
	<!-- When emitting HTML, one may wish to have a sequence of character -->
	<!-- data replaced with an element. A common example of this would be -->
	<!-- the translation of newline characters to <br> tags. This demo    -->
	<!-- shows a way to accomplish this transformation.                   -->
	<!--                                                                  -->
	<!-- It is important to realize that the initial CDATA is a string:   -->
	<!-- just a single text node. An element such as <br/> cannot be      -->
	<!-- inserted *into* a text node. Rather, the goal is to build up a   -->
	<!-- result tree fragment consisting of alternating text and element  -->
	<!-- nodes, based on the content of the original string.              -->
	<!--                                                                  -->
	<!-- It is also important to realize that if one attempts to treat    -->
	<!-- a result tree fragment as a string, it will be converted to just -->
	<!-- the concatenation of its text nodes; its element nodes will be   -->
	<!-- ignored.                                                         -->
	<!--                                                                  -->
	<!-- Input XML for this stylesheet is irrelevant.                     -->
	<!-- -->
	<!-- Requirements:                                                    -->
	<!--  James Clark's XT 19991105 (or comparable XSLT processor)        -->
	<!-- -->
	<!-- Change history:                                                  -->
	<!--    1.1: updated to current working draft syntax                  -->
	<!--    1.0: first public version                                     -->

	<!-- template that matches the root node -->
	<xsl:template match="/">
		<html>
			<head>
				<title>Newline to &lt;br&gt; Transformation Demo</title>
				<style type="text/css">
					<xsl:text>&#xA;.data { color: red; }&#xA;</xsl:text>
				</style>
			</head>
			<body>
				<xsl:variable name="StringIn">red&#xA;orange&#xA;yellow&#xA;green</xsl:variable>
				<h3>(view source to see the difference)</h3>
				<p>
					<xsl:text>&#xA;The input string is:&#xA;</xsl:text>
					<br/>
					<span class="data">
						<xsl:copy-of select="$StringIn"/>
					</span>
				</p>
				<xsl:variable name="ResultTreeFragmentOut">
					<xsl:call-template name="nl2br">
						<xsl:with-param name="StringToTransform" select="$StringIn"/>
					</xsl:call-template>
				</xsl:variable>
				<p>
					<xsl:text>&#xA;The output result tree fragment is:&#xA;</xsl:text>
					<br/>
					<span class="data">
						<xsl:copy-of select="$ResultTreeFragmentOut"/>
					</span>
				</p>
			</body>
		</html>
	</xsl:template>

	<!-- template that "translates newlines to <br/> tags" -->
	<xsl:template name="nl2br">
		<!-- import $StringToTransform -->
		<xsl:param name="StringToTransform"/>
		<xsl:choose>
			<!-- string contains newline -->
			<xsl:when test="contains($StringToTransform,'&#xA;')">
				<!-- output substring that comes before the first newline -->
				<!-- note: use of substring-before() function means       -->
				<!-- $StringToTransform will be treated as a string,      -->
				<!-- even if it is a node-set or result tree fragment.    -->
				<!-- So hopefully $StringToTransform is really a string!  -->
				<xsl:value-of select="substring-before($StringToTransform,'&#xA;')"/>
				<!-- output a <br> tag instead of newline -->
				<br/>
				<!-- repeat for the remainder of the original string -->
				<xsl:call-template name="nl2br">
					<xsl:with-param name="StringToTransform">
						<xsl:value-of select="substring-after($StringToTransform,'&#xA;')"/>
					</xsl:with-param>
				</xsl:call-template>
			</xsl:when>
			<!-- string does not contain newline, so just output it -->
			<xsl:otherwise>
				<xsl:value-of select="$StringToTransform"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

</xsl:stylesheet>
