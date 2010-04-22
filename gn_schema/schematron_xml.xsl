<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sch="http://www.ascc.net/xml/schematron"
                xmlns:gml="http://www.opengis.net/gml"
                xmlns:gmd="http://www.isotc211.org/2005/gmd"
                xmlns:gco="http://www.isotc211.org/2005/gco"
                xmlns:geonet="http://www.fao.org/geonetwork"
                xmlns:ADO="http://www.defence.gov.au/ADO_DM_MDP"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                version="1.0"
                gml:dummy-for-xmlns=""
                gmd:dummy-for-xmlns=""
                gco:dummy-for-xmlns=""
                geonet:dummy-for-xmlns=""
                ADO:dummy-for-xmlns=""
                xlink:dummy-for-xmlns="">
   <xsl:output method="xml"/>
   <xsl:template match="*|@*" mode="schematron-get-full-path">
      <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
      <xsl:text>/</xsl:text>
      <xsl:if test="count(. | ../@*) = count(../@*)">@</xsl:if>
      <xsl:value-of select="name()"/>
      <xsl:text>[</xsl:text>
      <xsl:value-of select="1+count(preceding-sibling::*[name()=name(current())])"/>
      <xsl:text>]</xsl:text>
   </xsl:template>
   <xsl:template match="/">
      <geonet:schematronerrors>
         <xsl:apply-templates select="/" mode="M7"/>
         <xsl:apply-templates select="/" mode="M8"/>
         <xsl:apply-templates select="/" mode="M9"/>
         <xsl:apply-templates select="/" mode="M10"/>
         <xsl:apply-templates select="/" mode="M11"/>
         <xsl:apply-templates select="/" mode="M12"/>
         <xsl:apply-templates select="/" mode="M13"/>
         <xsl:apply-templates select="/" mode="M14"/>
         <xsl:apply-templates select="/" mode="M15"/>
         <xsl:apply-templates select="/" mode="M16"/>
         <xsl:apply-templates select="/" mode="M17"/>
         <xsl:apply-templates select="/" mode="M18"/>
         <xsl:apply-templates select="/" mode="M19"/>
         <xsl:apply-templates select="/" mode="M20"/>
         <xsl:apply-templates select="/" mode="M21"/>
         <xsl:apply-templates select="/" mode="M22"/>
         <xsl:apply-templates select="/" mode="M23"/>
         <xsl:apply-templates select="/" mode="M24"/>
         <xsl:apply-templates select="/" mode="M25"/>
         <xsl:apply-templates select="/" mode="M26"/>
         <xsl:apply-templates select="/" mode="M27"/>
         <xsl:apply-templates select="/" mode="M28"/>
         <xsl:apply-templates select="/" mode="M29"/>
         <xsl:apply-templates select="/" mode="M30"/>
         <xsl:apply-templates select="/" mode="M31"/>
         <xsl:apply-templates select="/" mode="M32"/>
         <xsl:apply-templates select="/" mode="M33"/>
         <xsl:apply-templates select="/" mode="M34"/>
         <xsl:apply-templates select="/" mode="M35"/>
         <xsl:apply-templates select="/" mode="M36"/>
         <xsl:apply-templates select="/" mode="M37"/>
         <xsl:apply-templates select="/" mode="M38"/>
         <xsl:apply-templates select="/" mode="M39"/>
         <xsl:apply-templates select="/" mode="M40"/>
         <xsl:apply-templates select="/" mode="M41"/>
         <xsl:apply-templates select="/" mode="M42"/>
      </geonet:schematronerrors>
   </xsl:template>
   <xsl:template match="//gmd:MD_Metadata|//*[@gco:isoType='gmd:MD_Metadata']" priority="4000"
                 mode="M7">
      <xsl:choose>
         <xsl:when test="gmd:fileIdentifier and ((normalize-space(gmd:fileIdentifier) != '')  or (normalize-space(gmd:fileIdentifier/gco:CharacterString) != ''))"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>fileIdentifier not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M7"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M7"/>
   <xsl:template match="*[gco:CharacterString]" priority="4000" mode="M8">
      <xsl:if test="(normalize-space(gco:CharacterString) = '') and (not(@gco:nilReason) or not(contains('inapplicable missing template unknown withheld',@gco:nilReason)))">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>CharacterString must have content or parent\'s nilReason attribute must be legitimate.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M8"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M8"/>
   <xsl:template match="//gml:DirectPositionType" priority="4000" mode="M9">
      <xsl:if test="not(@srsDimension) or @srsName">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>The presence of a dimension attribute implies the presence of the srsName attribute.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:if test="not(@axisLabels) or @srsName">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>The presence of an axisLabels attribute implies the presence of the srsName attribute.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:if test="not(@uomLabels) or @srsName">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>The presence of an uomLabels attribute implies the presence of the srsName attribute.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:if test="(not(@uomLabels) and not(@axisLabels)) or (@uomLabels and @axisLabels)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>The presence of an uomLabels attribute implies the presence of the axisLabels attribute and vice versa.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M9"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M9"/>
   <xsl:template match="//gmd:CI_ResponsibleParty" priority="4000" mode="M10">
      <xsl:choose>
         <xsl:when test="(count(gmd:individualName) + count(gmd:organisationName) + count(gmd:positionName)) &gt; 0"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>You must specify one or more of individualName, organisationName or positionName.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M10"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M10"/>
   <xsl:template match="//gmd:MD_LegalConstraints" priority="4000" mode="M11">
      <xsl:if test="gmd:accessConstraints/gmd:MD_RestrictionCode/@codeListValue='otherRestrictions' and not(gmd:otherConstraints)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>otherConstraints: documented if accessConstraints or useConstraints = \"otherRestrictions\."</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:if test="gmd:useConstraints/gmd:MD_RestrictionCode/@codeListValue='otherRestrictions' and not(gmd:otherConstraints)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>otherConstraints: documented if accessConstraints or useConstraints = \"otherRestrictions\."</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M11"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M11"/>
   <xsl:template match="//gmd:MD_Band" priority="4000" mode="M12">
      <xsl:if test="(gmd:maxValue or gmd:minValue) and not(gmd:units)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>\"units\" is mandatory if \"maxValue\" or \"minValue\" are provided.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M12"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M12"/>
   <xsl:template match="//gmd:LI_Source" priority="4000" mode="M13">
      <xsl:choose>
         <xsl:when test="gmd:description or gmd:sourceExtent"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>\"description\" is mandatory if \"sourceExtent\" is not documented.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M13"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M13"/>
   <xsl:template match="//gmd:LI_Source" priority="4000" mode="M14">
      <xsl:choose>
         <xsl:when test="gmd:description or gmd:sourceExtent"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>\"description\" is mandatory if \"sourceExtent\" is not documented.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M14"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M14"/>
   <xsl:template match="//gmd:DQ_DataQuality" priority="4000" mode="M15">
      <xsl:if test="(((count(*/gmd:LI_Lineage/gmd:source) + count(*/gmd:LI_Lineage/gmd:processStep)) = 0) and (gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode/@codeListValue='dataset' or gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode/@codeListValue='series')) and not(gmd:lineage/gmd:LI_Lineage/gmd:statement) and (gmd:lineage)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>If(count(source) + count(processStep) =0) and (DQ_DataQuality.scope.level = \'dataset\' or \'series\') then statement is mandatory.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M15"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M15"/>
   <xsl:template match="//gmd:LI_Lineage" priority="4000" mode="M16">
      <xsl:if test="not(gmd:source) and not(gmd:statement) and not(gmd:processStep)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>\"source\" role is mandatory if LI_Lineage.statement and \"processStep\" role are not documented.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M16"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M16"/>
   <xsl:template match="//gmd:LI_Lineage" priority="4000" mode="M17">
      <xsl:if test="not(gmd:processStep) and not(gmd:statement) and not(gmd:source)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>\"processStep\" role is mandatory if LI_Lineage.statement and \"source\" role are not documented.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M17"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M17"/>
   <xsl:template match="//gmd:DQ_DataQuality" priority="4000" mode="M18">
      <xsl:if test="gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode/@codeListValue='dataset' and not(gmd:report) and not(gmd:lineage)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>\"report\" or \"lineage\" role is mandatory if scope.DQ_Scope.level = \'dataset\'.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M18"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M18"/>
   <xsl:template match="//gmd:DQ_Scope" priority="4000" mode="M19">
      <xsl:choose>
         <xsl:when test="gmd:level/gmd:MD_ScopeCode/@codeListValue='dataset' or gmd:level/gmd:MD_ScopeCode/@codeListValue='series' or (gmd:levelDescription and ((normalize-space(gmd:levelDescription) != '') or (gmd:levelDescription/gmd:MD_ScopeDescription) or (gmd:levelDescription/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:levelDescription/@gco:nilReason))))"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>\"levelDescription\" is mandatory if \"level\" notEqual \'dataset\' or \'series\'.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M19"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M19"/>
   <xsl:template match="//gmd:MD_Medium" priority="4000" mode="M20">
      <xsl:if test="gmd:density and not(gmd:densityUnits)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>\"densityUnits\" is mandatory if \"density\" is provided.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M20"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M20"/>
   <xsl:template match="//gmd:MD_Distribution" priority="4000" mode="M21">
      <xsl:choose>
         <xsl:when test="count(gmd:distributionFormat)&gt;0 or count(gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat)&gt;0"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>count (distributionFormat + distributor/MD_Distributor/distributorFormat) &gt; 0.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M21"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M21"/>
   <xsl:template match="//gmd:EX_Extent" priority="4000" mode="M22">
      <xsl:choose>
         <xsl:when test="count(gmd:description)&gt;0 or count(gmd:geographicElement)&gt;0 or count(gmd:temporalElement)&gt;0 or count(gmd:verticalElement)&gt;0"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>count(description + geographicElement + temporalElement + verticalElement) &gt; 0.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M22"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M22"/>
   <xsl:template match="//*[gmd:identificationInfo/gmd:MD_DataIdentification]" priority="4000"
                 mode="M23">
      <xsl:if test="(not(gmd:hierarchyLevel) or gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='dataset') and (count(//gmd:MD_DataIdentification/gmd:extent/*/gmd:geographicElement/gmd:EX_GeographicBoundingBox) + count (//gmd:MD_DataIdentification/gmd:extent/*/gmd:geographicElement/gmd:EX_GeographicDescription)) =0 ">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>MD_Metadata.hierarchyLevel = \"dataset\" (i.e. the default value of this property on the parent) implies count (extent.geographicElement.EX_GeographicBoundingBox) + count (extent.geographicElement.EX_GeographicDescription) &gt;=1.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M23"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M23"/>
   <xsl:template match="//gmd:MD_DataIdentification" priority="4000" mode="M24">
      <xsl:if test="(not(../../gmd:hierarchyLevel) or (../../gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='dataset') or (../../gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='series')) and (not(gmd:topicCategory))">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>topicCategory is mandatory if MD_Metadata.hierarchyLevel equal \"dataset\" or \"series\" or doesn\'t exist.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M24"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M24"/>
   <xsl:template match="//gmd:MD_AggregateInformation" priority="4000" mode="M25">
      <xsl:choose>
         <xsl:when test="gmd:aggregateDataSetName or gmd:aggregateDataSetIdentifier"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>Either \"aggregateDataSetName\" or \"aggregateDataSetIdentifier\" must be documented.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M25"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M25"/>
   <xsl:template match="//gmd:MD_Metadata|//*[@gco:isoType='gmd:MD_Metadata']" priority="4000"
                 mode="M26">
      <xsl:choose>
         <xsl:when test="gmd:language and ((normalize-space(gmd:language) != '')  or (normalize-space(gmd:language/gco:CharacterString) != '') or (gmd:language/gmd:LanguageCode) or (gmd:language/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:language/@gco:nilReason)))"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>language not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M26"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M26"/>
   <xsl:template match="//gmd:MD_Metadata|//*[@gco:isoType='gmd:MD_Metadata']" priority="4000"
                 mode="M27">
      <xsl:apply-templates mode="M27"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M27"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M28">
      <xsl:choose>
         <xsl:when test="(gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelist' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='enumeration' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement') or (gmd:obligation and ((normalize-space(gmd:obligation) != '')  or (gmd:obligation/gmd:MD_ObligationCode) or (gmd:obligation/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:obligation/@gco:nilReason))))"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>if \"dataType\" notEqual \'codelist\', \'enumeration\' or \'codelistElement\' then \"obligation\" is mandatory.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="(gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelist' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='enumeration' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement') or (gmd:maximumOccurrence and ((normalize-space(gmd:maximumOccurrence) != '')  or (normalize-space(gmd:maximumOccurrence/gco:CharacterString) != '') or (gmd:maximumOccurrence/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:maximumOccurrence/@gco:nilReason))))"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>if \"dataType\" notEqual \'codelist\', \'enumeration\' or \'codelistElement\' then \"maximumOccurence\" is mandatory.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="(gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelist' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='enumeration' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement') or (gmd:domainValue and ((normalize-space(gmd:domainValue) != '')  or (normalize-space(gmd:domainValue/gco:CharacterString) != '') or (gmd:domainValue/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:domainValue/@gco:nilReason))))"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>if \"dataType\" notEqual \'codelist\', \'enumeration\' or \'codelistElement\' then \"domainValue\" is mandatory.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M28"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M28"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M29">
      <xsl:if test="gmd:obligation/gmd:MD_ObligationCode='conditional' and not(gmd:condition)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>if \"obligation\" = \'conditional\' then \"condition\" is mandatory.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M29"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M29"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M30">
      <xsl:if test="gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement' and not(gmd:domainCode)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>if \"dataType\" = \'codelistElement\' then \"domainCode\" is mandatory.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M30"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M30"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M31">
      <xsl:if test="gmd:dataType/gmd:MD_DatatypeCode/@codeListValue!='codelistElement' and not(gmd:shortName)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>if \"dataType\" not equal to \'codelistElement\' then \"shortName\" is mandatory.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M31"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M31"/>
   <xsl:template match="//gmd:MD_Georectified" priority="4000" mode="M32">
      <xsl:if test="(gmd:checkPointAvailability/gco:Boolean='1' or gmd:checkPointAvailability/gco:Boolean='true') and not(gmd:checkPointDescription)">
         <geonet:errorFound ref="#_{geonet:element/@ref}">
            <geonet:pattern name="{name(.)}"/>
            <geonet:diagnostics>\"checkPointDescription\" is mandatory if \"checkPointAvailability\" = 1 or true.</geonet:diagnostics>
         </geonet:errorFound>
      </xsl:if>
      <xsl:apply-templates mode="M32"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M32"/>
   <xsl:template match="/root/metadata/gmd:MD_Metadata|/root/metadata/*[@gco:isoType='gmd:MD_Metadata']"
                 priority="4000"
                 mode="M33">
      <xsl:choose>
         <xsl:when test="gmd:hierarchyLevelName or gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='dataset'"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>hierarchyLevelName must be documented if hierarchyLevel not = \"dataset\".</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M33"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M33"/>
   <xsl:template match="ADO:DP_Metadata | gmd:MD_Metadata" priority="4000" mode="M34">
      <xsl:choose>
         <xsl:when test="@xml:lang or gmd:language "/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>gmd:language should be present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M34"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M34"/>
   <xsl:template match="ADO:DP_Metadata | gmd:MD_Metadata" priority="4000" mode="M35">
      <xsl:choose>
         <xsl:when test="gmd:dataSetURI or gmd:parentIdentifier"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>dataSetURI is not present therefore parentIdentifier should be present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="gmd:dataSetURI or gmd:hierarchyLevel"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>dataSetURI is not present therefore hierarchyLevel should be present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="gmd:dataSetURI or gmd:hierarchyLevelName"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>dataSetURI is not present therefore hierarchyLevelName should be present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M35"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M35"/>
   <xsl:template match="//ADO:DP_Metadata" priority="4000" mode="M36">
      <xsl:choose>
         <xsl:when test="gmd:referenceSystemInfo"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>referenceSystemInfo is not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M36"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M36"/>
   <xsl:template match="//ADO:DP_Metadata" priority="4000" mode="M37">
      <xsl:choose>
         <xsl:when test="gmd:distributionInfo"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>distributionInfo is not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M37"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M37"/>
   <xsl:template match="//ADO:DP_Metadata" priority="4000" mode="M38">
      <xsl:choose>
         <xsl:when test="gmd:dataQualityInfo"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>dataQualityInfo is not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M38"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M38"/>
   <xsl:template match="//ADO:DP_DataIdentification" priority="4000" mode="M39">
      <xsl:choose>
         <xsl:when test="ADO:resourceConstraints"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>resourceConstraints is not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M39"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M39"/>
   <xsl:template match="//ADO:DP_Distributor" priority="4000" mode="M40">
      <xsl:choose>
         <xsl:when test="gmd:distributionFormat"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>distributionFormat is not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M40"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M40"/>
   <xsl:template match="//ADO:DP_Distributor" priority="4000" mode="M41">
      <xsl:choose>
         <xsl:when test="gmd:distributor"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>distributor is not present.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M41"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M41"/>
   <xsl:template match="//ADO:DP_ResponsibleParty" priority="4000" mode="M42">
      <xsl:choose>
         <xsl:when test="gmd:organisationName and normalize-space(gmd:organisationName)!=''"/>
         <xsl:otherwise>
            <geonet:errorFound ref="#_{geonet:element/@ref}">
               <geonet:pattern name="{name(.)}"/>
               <geonet:diagnostics>organisationName is not present or has no content.</geonet:diagnostics>
            </geonet:errorFound>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M42"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M42"/>
   <xsl:template match="text()" priority="-1"/>
</xsl:stylesheet>