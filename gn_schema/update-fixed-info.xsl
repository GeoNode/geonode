<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet   xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
						xmlns:gml="http://www.opengis.net/gml"
						xmlns:srv="http://www.isotc211.org/2005/srv"
						xmlns:gco="http://www.isotc211.org/2005/gco"
						xmlns:gmx="http://www.isotc211.org/2005/gmx"
						xmlns:ADO="http://www.defence.gov.au/ADO_DM_MDP"
						xmlns:gmd="http://www.isotc211.org/2005/gmd" exclude-result-prefixes="gmd">

	<xsl:include href="../iso19139/convert/functions.xsl"/>

	<!-- ================================================================= -->
	
	<xsl:template match="/root">
		 <xsl:apply-templates select="ADO:DP_Metadata"/>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template match="ADO:DP_Metadata">
		 <xsl:copy>
		 		<xsl:copy-of select="@*"/>
		 		<xsl:if test="not(gmd:fileIdentifier)">
		 			<gmd:fileIdentifier>
						<gco:CharacterString><xsl:value-of select="/root/env/uuid"/></gco:CharacterString>
					</gmd:fileIdentifier>
				</xsl:if>
			  <xsl:apply-templates select="node()"/>
		 </xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template match="gmd:fileIdentifier" priority="10">
		<xsl:copy>
			<gco:CharacterString><xsl:value-of select="/root/env/uuid"/></gco:CharacterString>
		</xsl:copy>
	</xsl:template>
	
	<!-- ================================================================= -->
	
	<xsl:template match="gmd:metadataStandardName" priority="10">
		<xsl:copy>
			<gco:CharacterString>AS/NZS 19115 Geographic Metadata - ADO_DM_MDP Profile</gco:CharacterString>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template match="gmd:metadataStandardVersion" priority="10">
		<xsl:copy>
			<gco:CharacterString>1.0.3</gco:CharacterString>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->

	<xsl:template match="gmd:dateStamp">
		<xsl:choose>
			<xsl:when test="/root/env/updateDateStamp='yes'">
				<gmd:dateStamp>
					<gco:DateTime><xsl:value-of select="/root/env/changeDate"/></gco:DateTime>
				</gmd:dateStamp>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy-of select="."/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- ================================================================= -->

	<xsl:template match="@gml:id">
		<xsl:choose>
			<xsl:when test="normalize-space(.)=''">
				<xsl:attribute name="gml:id">
					<xsl:value-of select="generate-id(.)"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy-of select="."/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- ================================================================= -->
	<!-- Fix srsName attribute and generate epsg:4326 entry by default -->

	<xsl:template match="@srsName">
		<xsl:choose>
			<xsl:when test="normalize-space(.)=''">
				<xsl:attribute name="srsName">
					<xsl:text>urn:x-ogc:def:crs:EPSG:6.6:4326</xsl:text>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy-of select="."/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<!-- ================================================================= -->
	
	<xsl:template match="*[gco:CharacterString]">
		<xsl:copy>
			<xsl:copy-of select="@*[not(name()='gco:nilReason')]"/>
			<xsl:if test="normalize-space(gco:CharacterString)=''">
				<xsl:attribute name="gco:nilReason">
					<xsl:value-of select="'missing'"/>
				</xsl:attribute>
			</xsl:if>
			<xsl:apply-templates select="gco:CharacterString"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	<!-- codelists: set @codeList path -->
	<!-- ================================================================= -->
	
	<xsl:template match="gmd:*[@codeListValue]">
		<xsl:copy>
			<xsl:apply-templates select="@*"/>
			<xsl:attribute name="codeList">
				<xsl:value-of select="concat('http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#',local-name(.))"/>
			</xsl:attribute>
			<xsl:value-of select="@codeListValue"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="ADO:*[@codeListValue]">
		<xsl:copy>
			<xsl:apply-templates select="@*"/>
			<xsl:attribute name="codeList">
				<xsl:value-of select="concat('http://www.defence.gov.au/ADO_DM_MDP ../gmd/ADO_Codelists.xml#',local-name(.))"/>
			</xsl:attribute>
			<xsl:value-of select="@codeListValue"/>
		</xsl:copy>
	</xsl:template>

	<!-- can't find the location of the 19119 codelists - so we make one up -->

	<xsl:template match="srv:*[@codeListValue]">
		<xsl:copy>
			<xsl:apply-templates select="@*"/>
			<xsl:attribute name="codeList">
				<xsl:value-of select="concat('http://www.isotc211.org/2005/iso19119/resources/Codelist/gmxCodelists.xml#',local-name(.))"/>
			</xsl:attribute>
			<xsl:value-of select="@codeListValue"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	<!-- online resources: download -->
	<!-- ================================================================= -->

	<xsl:template match="gmd:CI_OnlineResource[starts-with(gmd:protocol/gco:CharacterString,'WWW:DOWNLOAD-') and contains(gmd:protocol/gco:CharacterString,'http--download') and gmd:name]">
		<xsl:variable name="fname" select="gmd:name/gco:CharacterString|gmd:name/gmx:MimeFileType"/>
		<xsl:variable name="mimeType">
			<xsl:call-template name="getMimeTypeFile">
				<xsl:with-param name="datadir" select="/root/env/datadir"/>
				<xsl:with-param name="fname" select="$fname"/>
			</xsl:call-template>
		</xsl:variable>

		<xsl:copy>
			<xsl:copy-of select="@*"/>
			<gmd:linkage>
				<gmd:URL>
					<xsl:value-of select="concat(/root/env/siteURL,'/file.disclaimer?id=',/root/env/id,'&amp;fname=',$fname,'&amp;access=private')"/>
				</gmd:URL>
			</gmd:linkage>
			<xsl:copy-of select="gmd:protocol"/>
			<xsl:copy-of select="gmd:applicationProfile"/>
			<gmd:name>
				<gmx:MimeFileType type="{$mimeType}">
					<xsl:value-of select="$fname"/>
				</gmx:MimeFileType>
			</gmd:name>
			<xsl:copy-of select="gmd:description"/>
			<xsl:copy-of select="gmd:function"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	<!-- online resources: link-to-downloadable data etc -->
	<!-- ================================================================= -->

	<xsl:template match="gmd:CI_OnlineResource[starts-with(gmd:protocol/gco:CharacterString,'WWW:LINK-') and contains(gmd:protocol/gco:CharacterString,'http--download')]">
		<xsl:variable name="mimeType">
			<xsl:call-template name="getMimeTypeUrl">
				<xsl:with-param name="linkage" select="gmd:linkage/gmd:URL"/>
			</xsl:call-template>
		</xsl:variable>

		<xsl:copy>
			<xsl:copy-of select="@*"/>
			<xsl:copy-of select="gmd:linkage"/>
			<xsl:copy-of select="gmd:protocol"/>
			<xsl:copy-of select="gmd:applicationProfile"/>
			<gmd:name>
				<gmx:MimeFileType type="{$mimeType}"/>
			</gmd:name>
			<xsl:copy-of select="gmd:description"/>
			<xsl:copy-of select="gmd:function"/>
		</xsl:copy>
	</xsl:template>

	<!-- =================================================================-->
	
	<xsl:template match="gmx:FileName">
		<xsl:copy>
			<xsl:attribute name="src">
				<xsl:value-of select="concat(/root/env/siteURL,'/resources.get?id=',/root/env/id,'&amp;fname=',.,'&amp;access=private')"/>
			</xsl:attribute>
			<xsl:value-of select="."/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template match="@*|node()">
		 <xsl:copy>
			  <xsl:apply-templates select="@*|node()"/>
		 </xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->

</xsl:stylesheet>
