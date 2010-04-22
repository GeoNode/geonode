<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet   xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" 
						xmlns:gco="http://www.isotc211.org/2005/gco"
						xmlns:geonode="http://geonode.org/0.1"
						xmlns:gmd="http://www.isotc211.org/2005/gmd">

	<xsl:template match="geonode:MD_Metadata">
		<thumbnail>
			<xsl:for-each select="gmd:identificationInfo/geonode:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic">
				<xsl:choose>
					<xsl:when test="gmd:fileDescription/gco:CharacterString = 'large_thumbnail' and gmd:fileName/gco:CharacterString != ''">
						<large>
							<xsl:value-of select="gmd:fileName/gco:CharacterString" />
						</large>
					</xsl:when>
					<xsl:when test="gmd:fileDescription/gco:CharacterString = 'thumbnail' and gmd:fileName/gco:CharacterString != ''">
						<small>
							<xsl:value-of select="gmd:fileName/gco:CharacterString" />
						</small>
					</xsl:when>
				</xsl:choose>
			</xsl:for-each>
		</thumbnail>
	</xsl:template>

</xsl:stylesheet>
