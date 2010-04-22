<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet   xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" 
						xmlns:gco="http://www.isotc211.org/2005/gco"
						xmlns:ADO="http://www.defence.gov.au/ADO_DM_MDP"
						xmlns:gmd="http://www.isotc211.org/2005/gmd">

	<!-- ============================================================================================ -->

	<xsl:output indent="yes"/>
	
	<!-- ============================================================================================ -->
	
	<xsl:template match="ADO:DP_Metadata">
		<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
						xmlns:dc   ="http://purl.org/dc/elements/1.1/"
						xmlns:xsi  ="http://www.w3.org/2001/XMLSchema-instance"
						xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">

			<xsl:for-each select="gmd:fileIdentifier">
				<dc:identifier><xsl:value-of select="gco:CharacterString"/></dc:identifier>
			</xsl:for-each>

			<dc:date><xsl:value-of select="/root/env/changeDate"/></dc:date>
			
			<!-- DataIdentification - - - - - - - - - - - - - - - - - - - - - -->

			<xsl:for-each select="gmd:identificationInfo/ADO:DP_DataIdentification">

				<xsl:for-each select="gmd:citation/gmd:CI_Citation">	
					<xsl:for-each select="gmd:title/gco:CharacterString">
						<dc:title><xsl:value-of select="."/></dc:title>
					</xsl:for-each>

					<xsl:for-each select="gmd:citedResponsibleParty/ADO:DP_ResponsibleParty[gmd:role/gmd:CI_RoleCode/@codeListValue='originator']/gmd:organisationName/gco:CharacterString">
						<dc:creator><xsl:value-of select="."/></dc:creator>
					</xsl:for-each>

					<xsl:for-each select="gmd:citedResponsibleParty/ADO:DP_ResponsibleParty[gmd:role/gmd:CI_RoleCode/@codeListValue='publisher']/gmd:organisationName/gco:CharacterString">
						<dc:publisher><xsl:value-of select="."/></dc:publisher>
					</xsl:for-each>

					<xsl:for-each select="gmd:citedResponsibleParty/ADO:DP_ResponsibleParty[gmd:role/gmd:CI_RoleCode/@codeListValue='author']/gmd:organisationName/gco:CharacterString">
						<dc:contributor><xsl:value-of select="."/></dc:contributor>
					</xsl:for-each>
				</xsl:for-each>

				<!-- subject -->

				<xsl:for-each select="gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString">
					<dc:subject><xsl:value-of select="."/></dc:subject>
				</xsl:for-each>

				<!-- description -->

				<xsl:for-each select="gmd:abstract/gco:CharacterString">
					<dc:description><xsl:value-of select="."/></dc:description>
				</xsl:for-each>

				<!-- rights -->

				<xsl:for-each select="gmd:resourceConstraints/gmd:MD_LegalConstraints|gmd:resourceConstraints/ADO:DP_LegalConstraints">
					<xsl:for-each select="*/gmd:MD_RestrictionCode/@codeListValue">
						<dc:rights><xsl:value-of select="."/></dc:rights>
					</xsl:for-each>

					<xsl:for-each select="gmd:otherConstraints/gco:CharacterString">
						<dc:rights><xsl:value-of select="."/></dc:rights>
					</xsl:for-each>
				</xsl:for-each>

				<!-- language -->

				<xsl:for-each select="gmd:language/gco:CharacterString">
					<dc:language><xsl:value-of select="."/></dc:language>
				</xsl:for-each>

				<!-- bounding box -->

				<xsl:for-each select="gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox">	
					<dc:coverage>
						<xsl:value-of select="concat('North ', gmd:northBoundLatitude/gco:Decimal, ', ')"/>
						<xsl:value-of select="concat('South ', gmd:southBoundLatitude/gco:Decimal, ', ')"/>
						<xsl:value-of select="concat('East ' , gmd:eastBoundLongitude/gco:Decimal, ', ')"/>
						<xsl:value-of select="concat('West ' , gmd:westBoundLongitude/gco:Decimal, '.')"/>
					</dc:coverage>
				</xsl:for-each>
			</xsl:for-each>

			<!-- Type - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->

			<xsl:for-each select="gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue">
				<dc:type><xsl:value-of select="."/></dc:type>
			</xsl:for-each>

			<!-- Distribution - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->

			<xsl:for-each select="gmd:distributionInfo/gmd:MD_Distribution|gmd:distributionInfo/ADO:DP_Distribution">
				<xsl:for-each select="gmd:distributionFormat/gmd:MD_Format/gmd:name/gco:CharacterString">
					<dc:format><xsl:value-of select="."/></dc:format>
				</xsl:for-each>
			</xsl:for-each>

		</oai_dc:dc>
	</xsl:template>

	<!-- ============================================================================================ -->

	<xsl:template match="*">
		<xsl:apply-templates select="*"/>
	</xsl:template>
	
	<!-- ============================================================================================ -->

</xsl:stylesheet>
