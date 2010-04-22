<xsl:stylesheet 
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >

<xsl:output method="html" indent="yes"/>

<xsl:template match="/">
<pre>
<xsl:apply-templates mode="verb"/>
</pre>
</xsl:template>

<!-- 
Copyright 1999 David Carlisle NAG Ltd
               davidc@nag.co.uk
	Free use granted under GPL or MPL.

     Render XML in an HTML pre element.


     USAGE
     =====

     include this stylesheet into your main stylesheet via

     <xsl:import href="verb.xsl"/>

     Then a typical usage might be to render an <example> element twice,
     first as literal XML, then secondly styled as normal.

     One would use, in your main stylesheet:

     <xsl:template  match="example">
     <pre>
     <xsl:apply-templates mode="verb"/>
     </pre>
     <xsl:apply-templates/>
     </xsl:template>

     This would put the contents of the example element (but not `<example>')
     in the HTML pre element. If you want the verbatim mode to include the
     current, `example' element, modify the above to say
     <xsl:apply-templates mode="verb" select="."/>

-->

<!--   verb mode -->

<!-- Does not really give verbatim copy of the file as that
     information not present in the parsed document, but should
     give something that renders in HTML as a well formed XML
     document that would parse to give same XML tree as the original
-->

<!-- non empty elements and other nodes. -->
<xsl:template mode="verb" match="*[*]|*[text()]|*[comment()]|*[processing-instruction()]">
  <a name="{generate-id(.)}"/>
  <xsl:value-of select="concat('&lt;',name(.))"/>
  <xsl:apply-templates mode="verb" select="@*"/>
  <xsl:text>&gt;</xsl:text>
  <xsl:apply-templates mode="verb"/>
  <xsl:value-of select="concat('&lt;/',name(.),'&gt;')"/>
</xsl:template>

<!-- empty elements -->
<xsl:template mode="verb" match="*">
  <a name="{generate-id(.)}"/>
  <xsl:value-of select="concat('&lt;',name(.))"/>
  <xsl:apply-templates mode="verb" select="@*"/>
  <xsl:text>/&gt;</xsl:text>
</xsl:template>

<!-- attributes
     Output always surrounds attribute value by "
     so we need to make sure no literal " appear in the value  -->
<xsl:template mode="verb" match="@*">
  <a name="{generate-id(.)}"/>
  <xsl:value-of select="concat(' ',name(.),'=')"/>
  <xsl:text>"</xsl:text>
  <xsl:call-template name="string-replace">
    <xsl:with-param name="from" select="'&quot;'"/>
    <xsl:with-param name="to" select="'&amp;quot;'"/> 
    <xsl:with-param name="string" select="."/>
  </xsl:call-template>
  <xsl:text>"</xsl:text>
</xsl:template>

<!-- pis -->
<xsl:template mode="verb" match="processing-instruction()">
  <a name="{generate-id(.)}"/>
  <xsl:value-of select="concat('&lt;?',name(.),' ',.,'?&gt;')"/>
</xsl:template>

<!-- only works if parser passes on comment nodes -->
<xsl:template mode="verb" match="comment()">
  <a name="{generate-id(.)}"/>
  <xsl:value-of select="concat('&lt;!--',.,'--&gt;')"/>
</xsl:template>

<!-- text elements
     need to replace & and < by entity references
     do > as well,  just for balance -->
<xsl:template mode="verb" match="text()">
  <a name="{generate-id(.)}"/>
  <xsl:call-template name="string-replace">
    <xsl:with-param name="to" select="'&amp;gt;'"/>
    <xsl:with-param name="from" select="'&gt;'"/> 
    <xsl:with-param name="string">
      <xsl:call-template name="string-replace">
        <xsl:with-param name="to" select="'&amp;lt;'"/>
        <xsl:with-param name="from" select="'&lt;'"/> 
        <xsl:with-param name="string">
          <xsl:call-template name="string-replace">
            <xsl:with-param name="to" select="'&amp;amp;'"/>
            <xsl:with-param name="from" select="'&amp;'"/> 
            <xsl:with-param name="string" select="."/>
          </xsl:call-template>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<!-- end  verb mode -->

<!-- replace all occurences of the character(s) `from'
     by the string `to' in the string `string'.-->
<xsl:template name="string-replace" >
  <xsl:param name="string"/>
  <xsl:param name="from"/>
  <xsl:param name="to"/>
  <xsl:choose>
    <xsl:when test="contains($string,$from)">
      <xsl:value-of select="substring-before($string,$from)"/>
      <xsl:value-of select="$to"/>
      <xsl:call-template name="string-replace">
      <xsl:with-param name="string" select="substring-after($string,$from)"/>
      <xsl:with-param name="from" select="$from"/>
      <xsl:with-param name="to" select="$to"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$string"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>

