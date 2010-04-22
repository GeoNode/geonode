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
	
	<xsl:template match="ADO:DP_Metadata">
		<xsl:copy>
		 	<xsl:copy-of select="@*"/>
			<xsl:apply-templates select="gmd:fileIdentifier"/>
			<xsl:apply-templates select="gmd:language"/>
			<xsl:apply-templates select="gmd:characterSet"/>
			<xsl:apply-templates select="gmd:parentIdentifier"/>
			<xsl:apply-templates select="gmd:hierarchyLevel"/>
			<xsl:apply-templates select="gmd:hierarchyLevelName"/>
			<xsl:apply-templates select="gmd:contact"/>
			<xsl:apply-templates select="gmd:dateStamp"/>
			<xsl:apply-templates select="gmd:metadataStandardName"/>
			<xsl:apply-templates select="gmd:metadataStandardVersion"/>
			<xsl:apply-templates select="gmd:dataSetURI"/>
			<xsl:apply-templates select="gmd:locale"/>
			<xsl:apply-templates select="gmd:spatialRepresentationInfo"/>
			<xsl:apply-templates select="gmd:referenceSystemInfo"/>
			<xsl:apply-templates select="gmd:metadataExtensionInfo"/>

			<xsl:choose>
				<xsl:when test="not(gmd:identificationInfo)">
		 			<gmd:identificationInfo>
						<ADO:DP_DataIdentification gco:isoType="gmd:MD_DataIdentification">
							<xsl:call-template name="fill"/>
						</ADO:DP_DataIdentification>
					</gmd:identificationInfo>
				</xsl:when>
				
				<xsl:otherwise>
					<xsl:apply-templates select="gmd:identificationInfo"/>
				</xsl:otherwise>
			</xsl:choose>
			
			<xsl:apply-templates select="gmd:contentInfo"/>
			<xsl:apply-templates select="gmd:distributionInfo"/>
			<xsl:apply-templates select="gmd:dataQualityInfo"/>
			<xsl:apply-templates select="gmd:portrayalCatalogueInfo"/>
			<xsl:apply-templates select="gmd:metadataConstraints"/>
			<xsl:apply-templates select="gmd:applicationSchemaInfo"/>
			<xsl:apply-templates select="gmd:metadataMaintenance"/>
			<xsl:apply-templates select="gmd:series"/>
			<xsl:apply-templates select="gmd:describes"/>
			<xsl:apply-templates select="gmd:propertyType"/>
			<xsl:apply-templates select="gmd:featureType"/>
			<xsl:apply-templates select="gmd:featureAttribute"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template match="ADO:DP_DataIdentification">
		<xsl:copy>
		 	<xsl:copy-of select="@*"/>
			<xsl:apply-templates select="gmd:citation"/>
			<xsl:apply-templates select="gmd:abstract"/>
			<xsl:apply-templates select="gmd:purpose"/>
			<xsl:apply-templates select="gmd:credit"/>
			<xsl:apply-templates select="gmd:status"/>
			<xsl:apply-templates select="gmd:pointOfContact"/>
			<xsl:apply-templates select="gmd:resourceMaintenance"/>
			<xsl:apply-templates select="gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileDescription/gco:CharacterString != /root/env/type]"/>
		 	
			<xsl:call-template name="fill"/>
		
			<xsl:apply-templates select="gmd:resourceFormat"/>
			<xsl:apply-templates select="gmd:descriptiveKeywords"/>
			<xsl:apply-templates select="gmd:resourceConstraints"/>
			<xsl:apply-templates select="gmd:resourceSpecificUsage"/>
			<xsl:apply-templates select="gmd:aggregationInfo"/>
			<xsl:apply-templates select="gmd:spatialRepresentationType"/>
			<xsl:apply-templates select="gmd:spatialResolution"/>
			<xsl:apply-templates select="gmd:language"/>
			<xsl:apply-templates select="gmd:characterSet"/>
			<xsl:apply-templates select="gmd:topicCategory"/>
			<xsl:apply-templates select="gmd:environmentDescription"/>
			<xsl:apply-templates select="gmd:extent"/>
			<xsl:apply-templates select="gmd:supplementalInformation"/>
			<xsl:apply-templates select="ADO:resourceConstraints"/>
			<xsl:apply-templates select="ADO:defencePurpose"/>
			<xsl:apply-templates select="ADO:productNumber"/>
			<xsl:apply-templates select="ADO:stockNumber"/>
			<xsl:apply-templates select="ADO:mapsheetNumber"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	
	<xsl:template name="fill">
		<gmd:graphicOverview>
			<gmd:MD_BrowseGraphic>
				<gmd:fileName>
					<gco:CharacterString><xsl:value-of select="/root/env/file"/></gco:CharacterString>
				</gmd:fileName>
				<gmd:fileDescription>
					<gco:CharacterString><xsl:value-of select="/root/env/type"/></gco:CharacterString>
				</gmd:fileDescription>
				<gmd:fileType>
					<gco:CharacterString><xsl:value-of select="/root/env/ext"/></gco:CharacterString>
				</gmd:fileType>
			</gmd:MD_BrowseGraphic>
		</gmd:graphicOverview>
	</xsl:template>
	
	<!-- ================================================================= -->

	<xsl:template match="@*|node()">
		 <xsl:copy>
			  <xsl:apply-templates select="@*|node()"/>
		 </xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	
</xsl:stylesheet>
