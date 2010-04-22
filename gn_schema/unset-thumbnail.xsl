<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet   xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" 
						xmlns:gco="http://www.isotc211.org/2005/gco"
						xmlns:ADO="http://www.defence.gov.au/ADO_DM_MDP"
						xmlns:gmd="http://www.isotc211.org/2005/gmd">


	<!-- ================================================================= -->
	
	<xsl:template match="/root">
		 <xsl:apply-templates select="ADO:DP_Metadata"/>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template match="gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileDescription/gco:CharacterString = /root/env/type]"/>

	<!-- ================================================================= -->

	<xsl:template match="@*|node()">
		 <xsl:copy>
			  <xsl:apply-templates select="@*|node()"/>
		 </xsl:copy>
	</xsl:template>
	
	<!-- ================================================================= -->
	
</xsl:stylesheet>
