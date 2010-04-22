<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet   xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" 
						xmlns:gco="http://www.isotc211.org/2005/gco"
						xmlns:geonode="http://geonode.org/0.1"
						xmlns:gmd="http://www.isotc211.org/2005/gmd">

	<xsl:template match="geonode:MD_Metadata">
		 <uuid><xsl:value-of select="gmd:fileIdentifier/gco:CharacterString"/></uuid>
	</xsl:template>

</xsl:stylesheet>
