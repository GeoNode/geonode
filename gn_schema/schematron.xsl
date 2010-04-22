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
   <xsl:output method="html"/>
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
      <html>
         <style>
         a:link    { color: black}
         a:visited { color: gray}
         a:active  { color: #FF0088}
         h3        { background-color:black; color:white;
                     font-family:Arial Black; font-size:12pt; }
         h3.linked { background-color:black; color:white;
                     font-family:Arial Black; font-size:12pt; }
      </style>
         <h2 title="Schematron contact-information is at the end of                   this page">
            <font color="#FF0080">Schematron</font> Report
      </h2>
         <h1 title=" ">Schematron validation for ADO Profile of AS/NZS 19115(19139)</h1>
         <div class="errors">
            <ul>
               <h3>ANZLIC Metadata Profile Version 1.1.1 Annex B Table 5 row 3 - fileIdentifier required</h3>
               <xsl:apply-templates select="/" mode="M7"/>
               <h3>CharacterString must have content or it's parent must have a valid nilReason attribute.</h3>
               <xsl:apply-templates select="/" mode="M8"/>
               <h3>CRS attributes constraints</h3>
               <xsl:apply-templates select="/" mode="M9"/>
               <h3>ISOFTDS19139:2005-TableA1-Row24 - name required</h3>
               <xsl:apply-templates select="/" mode="M10"/>
               <h3>ISOFTDS19139:2005-TableA1-Row07 - otherConstraints required if otherRestrictions</h3>
               <xsl:apply-templates select="/" mode="M11"/>
               <h3>ISOFTDS19139:2005-TableA1-Row16 - units required for values</h3>
               <xsl:apply-templates select="/" mode="M12"/>
               <h3>ISOFTDS19139:2005-TableA1-Row13 - description required if no sourceExtent</h3>
               <xsl:apply-templates select="/" mode="M13"/>
               <h3>ISOFTDS19139:2005-TableA1-Row14 - sourceExtent required if no description</h3>
               <xsl:apply-templates select="/" mode="M14"/>
               <h3>ISOFTDS19139:2005-TableA1-Row10 - content mandatory for dataset or series</h3>
               <xsl:apply-templates select="/" mode="M15"/>
               <h3>ISOFTDS19139:2005-TableA1-Row11 - source required if no statement or processStep</h3>
               <xsl:apply-templates select="/" mode="M16"/>
               <h3>ISOFTDS19139:2005-TableA1-Row12 - processStep required if no statement or source</h3>
               <xsl:apply-templates select="/" mode="M17"/>
               <h3>ISOFTDS19139:2005-TableA1-Row08 - dataset must have report or lineage</h3>
               <xsl:apply-templates select="/" mode="M18"/>
               <h3>ISOFTDS19139:2005-TableA1-Row09 - levelDescription needed unless dataset or series</h3>
               <xsl:apply-templates select="/" mode="M19"/>
               <h3>ISOFTDS19139:2005-TableA1-Row17 - units required for density values</h3>
               <xsl:apply-templates select="/" mode="M20"/>
               <h3>ISOFTDS19139:2005-TableA1-Row18 - MD_Format required</h3>
               <xsl:apply-templates select="/" mode="M21"/>
               <h3>ISOFTDS19139:2005-TableA1-Row23 - element required</h3>
               <xsl:apply-templates select="/" mode="M22"/>
               <h3>ISOFTDS19139:2005-TableA1-Row04 - dataset must have extent</h3>
               <xsl:apply-templates select="/" mode="M23"/>
               <h3>ISOFTDS19139:2005-TableA1-Row05 - dataset or series must have topicCategory</h3>
               <xsl:apply-templates select="/" mode="M24"/>
               <h3>ISOFTDS19139:2005-TableA1-Row06 - either aggregateDataSetName or aggregateDataSetIdentifier must be documented</h3>
               <xsl:apply-templates select="/" mode="M25"/>
               <h3>ISOFTDS19139:2005-TableA1-Row01 - language indication</h3>
               <xsl:apply-templates select="/" mode="M26"/>
               <h3>ISOFTDS19139:2005-TableA1-Row02 - character set indication</h3>
               <xsl:apply-templates select="/" mode="M27"/>
               <h3>ISOFTDS19139:2005-TableA1-Row19 - detail required unless simple term</h3>
               <xsl:apply-templates select="/" mode="M28"/>
               <h3>ISOFTDS19139:2005-TableA1-Row20 - condition</h3>
               <xsl:apply-templates select="/" mode="M29"/>
               <h3>ISOFTDS19139:2005-TableA1-Row21 - domainCode</h3>
               <xsl:apply-templates select="/" mode="M30"/>
               <h3>ISOFTDS19139:2005-TableA1-Row22 - shortName</h3>
               <xsl:apply-templates select="/" mode="M31"/>
               <h3>ISOFTDS19139:2005-TableA1-Row15 - checkPointDescription required if available</h3>
               <xsl:apply-templates select="/" mode="M32"/>
               <h3>hierarchy level name</h3>
               <xsl:apply-templates select="/" mode="M33"/>
               <h3>Encoding Set</h3>
               <xsl:apply-templates select="/" mode="M34"/>
               <h3>Test the setting of the dataset</h3>
               <xsl:apply-templates select="/" mode="M35"/>
               <h3>from gmdRedefined.xsd in the ADO - referenceSystemInfo required</h3>
               <xsl:apply-templates select="/" mode="M36"/>
               <h3>from gmdRedefined.xsd in the ADO - distributionInfo required</h3>
               <xsl:apply-templates select="/" mode="M37"/>
               <h3>from gmdRedefined.xsd in the ADO - dataQualityInfo required</h3>
               <xsl:apply-templates select="/" mode="M38"/>
               <h3>from gmdRedefined.xsd in the ADO - resourceConstraints required</h3>
               <xsl:apply-templates select="/" mode="M39"/>
               <h3>from gmdRedefined.xsd in the ADO - distributionFormat required</h3>
               <xsl:apply-templates select="/" mode="M40"/>
               <h3>from gmdRedefined.xsd in the ADO - distributor required</h3>
               <xsl:apply-templates select="/" mode="M41"/>
               <h3>from gmdRedefined.xsd in the ADO - organisationName required</h3>
               <xsl:apply-templates select="/" mode="M42"/>
            </ul>
         </div>
         <hr color="#FF0080"/>
         <p>
            <font size="2">Schematron Report by David Carlisle.
      <a href="http://www.ascc.net/xml/resource/schematron/schematron.html"
                  title="Link to the home page of the Schematron,                  a tree-pattern schema language">
                  <font color="#FF0080">The Schematron</font>
               </a> by
      <a href="mailto:ricko@gate.sinica.edu.tw"
                  title="Email to Rick Jelliffe (pronounced RIK JELIF)">Rick Jelliffe</a>,
      <a href="http://www.sinica.edu.tw" title="Link to home page of Academia Sinica">Academia Sinica Computing Centre</a>.
      </font>
         </p>
      </html>
   </xsl:template>
   <xsl:template match="//gmd:MD_Metadata|//*[@gco:isoType='gmd:MD_Metadata']" priority="4000"
                 mode="M7">
      <xsl:choose>
         <xsl:when test="gmd:fileIdentifier and ((normalize-space(gmd:fileIdentifier) != '')  or (normalize-space(gmd:fileIdentifier/gco:CharacterString) != ''))"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>fileIdentifier not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M7"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M7"/>
   <xsl:template match="*[gco:CharacterString]" priority="4000" mode="M8">
      <xsl:if test="(normalize-space(gco:CharacterString) = '') and (not(@gco:nilReason) or not(contains('inapplicable missing template unknown withheld',@gco:nilReason)))">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>CharacterString must have content or parent's nilReason attribute must be legitimate.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M8"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M8"/>
   <xsl:template match="//gml:DirectPositionType" priority="4000" mode="M9">
      <xsl:if test="not(@srsDimension) or @srsName">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>The presence of a dimension attribute implies the presence of the srsName attribute.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:if test="not(@axisLabels) or @srsName">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>The presence of an axisLabels attribute implies the presence of the srsName attribute.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:if test="not(@uomLabels) or @srsName">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>The presence of an uomLabels attribute implies the presence of the srsName attribute.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:if test="(not(@uomLabels) and not(@axisLabels)) or (@uomLabels and @axisLabels)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>The presence of an uomLabels attribute implies the presence of the axisLabels attribute and vice versa.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M9"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M9"/>
   <xsl:template match="//gmd:CI_ResponsibleParty" priority="4000" mode="M10">
      <xsl:choose>
         <xsl:when test="(count(gmd:individualName) + count(gmd:organisationName) + count(gmd:positionName)) &gt; 0"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>You must specify one or more of individualName, organisationName or positionName.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M10"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M10"/>
   <xsl:template match="//gmd:MD_LegalConstraints" priority="4000" mode="M11">
      <xsl:if test="gmd:accessConstraints/gmd:MD_RestrictionCode/@codeListValue='otherRestrictions' and not(gmd:otherConstraints)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>otherConstraints: documented if accessConstraints or useConstraints = "otherRestrictions."<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:if test="gmd:useConstraints/gmd:MD_RestrictionCode/@codeListValue='otherRestrictions' and not(gmd:otherConstraints)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>otherConstraints: documented if accessConstraints or useConstraints = "otherRestrictions."<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M11"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M11"/>
   <xsl:template match="//gmd:MD_Band" priority="4000" mode="M12">
      <xsl:if test="(gmd:maxValue or gmd:minValue) and not(gmd:units)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>"units" is mandatory if "maxValue" or "minValue" are provided.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M12"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M12"/>
   <xsl:template match="//gmd:LI_Source" priority="4000" mode="M13">
      <xsl:choose>
         <xsl:when test="gmd:description or gmd:sourceExtent"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>"description" is mandatory if "sourceExtent" is not documented.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M13"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M13"/>
   <xsl:template match="//gmd:LI_Source" priority="4000" mode="M14">
      <xsl:choose>
         <xsl:when test="gmd:description or gmd:sourceExtent"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>"description" is mandatory if "sourceExtent" is not documented.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M14"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M14"/>
   <xsl:template match="//gmd:DQ_DataQuality" priority="4000" mode="M15">
      <xsl:if test="(((count(*/gmd:LI_Lineage/gmd:source) + count(*/gmd:LI_Lineage/gmd:processStep)) = 0) and (gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode/@codeListValue='dataset' or gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode/@codeListValue='series')) and not(gmd:lineage/gmd:LI_Lineage/gmd:statement) and (gmd:lineage)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>If(count(source) + count(processStep) =0) and (DQ_DataQuality.scope.level = 'dataset' or 'series') then statement is mandatory.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M15"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M15"/>
   <xsl:template match="//gmd:LI_Lineage" priority="4000" mode="M16">
      <xsl:if test="not(gmd:source) and not(gmd:statement) and not(gmd:processStep)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>"source" role is mandatory if LI_Lineage.statement and "processStep" role are not documented.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M16"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M16"/>
   <xsl:template match="//gmd:LI_Lineage" priority="4000" mode="M17">
      <xsl:if test="not(gmd:processStep) and not(gmd:statement) and not(gmd:source)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>"processStep" role is mandatory if LI_Lineage.statement and "source" role are not documented.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M17"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M17"/>
   <xsl:template match="//gmd:DQ_DataQuality" priority="4000" mode="M18">
      <xsl:if test="gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode/@codeListValue='dataset' and not(gmd:report) and not(gmd:lineage)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>"report" or "lineage" role is mandatory if scope.DQ_Scope.level = 'dataset'.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M18"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M18"/>
   <xsl:template match="//gmd:DQ_Scope" priority="4000" mode="M19">
      <xsl:choose>
         <xsl:when test="gmd:level/gmd:MD_ScopeCode/@codeListValue='dataset' or gmd:level/gmd:MD_ScopeCode/@codeListValue='series' or (gmd:levelDescription and ((normalize-space(gmd:levelDescription) != '') or (gmd:levelDescription/gmd:MD_ScopeDescription) or (gmd:levelDescription/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:levelDescription/@gco:nilReason))))"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>"levelDescription" is mandatory if "level" notEqual 'dataset' or 'series'.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M19"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M19"/>
   <xsl:template match="//gmd:MD_Medium" priority="4000" mode="M20">
      <xsl:if test="gmd:density and not(gmd:densityUnits)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>"densityUnits" is mandatory if "density" is provided.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M20"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M20"/>
   <xsl:template match="//gmd:MD_Distribution" priority="4000" mode="M21">
      <xsl:choose>
         <xsl:when test="count(gmd:distributionFormat)&gt;0 or count(gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat)&gt;0"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>count (distributionFormat + distributor/MD_Distributor/distributorFormat) &gt; 0.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M21"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M21"/>
   <xsl:template match="//gmd:EX_Extent" priority="4000" mode="M22">
      <xsl:choose>
         <xsl:when test="count(gmd:description)&gt;0 or count(gmd:geographicElement)&gt;0 or count(gmd:temporalElement)&gt;0 or count(gmd:verticalElement)&gt;0"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>count(description + geographicElement + temporalElement + verticalElement) &gt; 0.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M22"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M22"/>
   <xsl:template match="//*[gmd:identificationInfo/gmd:MD_DataIdentification]" priority="4000"
                 mode="M23">
      <xsl:if test="(not(gmd:hierarchyLevel) or gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='dataset') and (count(//gmd:MD_DataIdentification/gmd:extent/*/gmd:geographicElement/gmd:EX_GeographicBoundingBox) + count (//gmd:MD_DataIdentification/gmd:extent/*/gmd:geographicElement/gmd:EX_GeographicDescription)) =0 ">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>MD_Metadata.hierarchyLevel = "dataset" (i.e. the default value of this property on the parent) implies count (extent.geographicElement.EX_GeographicBoundingBox) + count (extent.geographicElement.EX_GeographicDescription) &gt;=1.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M23"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M23"/>
   <xsl:template match="//gmd:MD_DataIdentification" priority="4000" mode="M24">
      <xsl:if test="(not(../../gmd:hierarchyLevel) or (../../gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='dataset') or (../../gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue='series')) and (not(gmd:topicCategory))">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>topicCategory is mandatory if MD_Metadata.hierarchyLevel equal "dataset" or "series" or doesn't exist.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M24"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M24"/>
   <xsl:template match="//gmd:MD_AggregateInformation" priority="4000" mode="M25">
      <xsl:choose>
         <xsl:when test="gmd:aggregateDataSetName or gmd:aggregateDataSetIdentifier"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>Either "aggregateDataSetName" or "aggregateDataSetIdentifier" must be documented.<b/>
               </a>
            </li>
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
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>language not present.<b/>
               </a>
            </li>
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
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>if "dataType" notEqual 'codelist', 'enumeration' or 'codelistElement' then "obligation" is mandatory.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="(gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelist' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='enumeration' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement') or (gmd:maximumOccurrence and ((normalize-space(gmd:maximumOccurrence) != '')  or (normalize-space(gmd:maximumOccurrence/gco:CharacterString) != '') or (gmd:maximumOccurrence/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:maximumOccurrence/@gco:nilReason))))"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>if "dataType" notEqual 'codelist', 'enumeration' or 'codelistElement' then "maximumOccurence" is mandatory.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="(gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelist' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='enumeration' or gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement') or (gmd:domainValue and ((normalize-space(gmd:domainValue) != '')  or (normalize-space(gmd:domainValue/gco:CharacterString) != '') or (gmd:domainValue/@gco:nilReason and contains('inapplicable missing template unknown withheld',gmd:domainValue/@gco:nilReason))))"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>if "dataType" notEqual 'codelist', 'enumeration' or 'codelistElement' then "domainValue" is mandatory.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M28"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M28"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M29">
      <xsl:if test="gmd:obligation/gmd:MD_ObligationCode='conditional' and not(gmd:condition)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>if "obligation" = 'conditional' then "condition" is mandatory.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M29"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M29"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M30">
      <xsl:if test="gmd:dataType/gmd:MD_DatatypeCode/@codeListValue='codelistElement' and not(gmd:domainCode)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>if "dataType" = 'codelistElement' then "domainCode" is mandatory.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M30"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M30"/>
   <xsl:template match="//gmd:MD_ExtendedElementInformation" priority="4000" mode="M31">
      <xsl:if test="gmd:dataType/gmd:MD_DatatypeCode/@codeListValue!='codelistElement' and not(gmd:shortName)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>if "dataType" not equal to 'codelistElement' then "shortName" is mandatory.<b/>
            </a>
         </li>
      </xsl:if>
      <xsl:apply-templates mode="M31"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M31"/>
   <xsl:template match="//gmd:MD_Georectified" priority="4000" mode="M32">
      <xsl:if test="(gmd:checkPointAvailability/gco:Boolean='1' or gmd:checkPointAvailability/gco:Boolean='true') and not(gmd:checkPointDescription)">
         <li>
            <a href="schematron-out.html#{generate-id(.)}" target="out"
               title="Link to where this pattern was found">
               <i/>"checkPointDescription" is mandatory if "checkPointAvailability" = 1 or true.<b/>
            </a>
         </li>
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
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>hierarchyLevelName must be documented if hierarchyLevel not = "dataset".<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M33"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M33"/>
   <xsl:template match="ADO:DP_Metadata | gmd:MD_Metadata" priority="4000" mode="M34">
      <xsl:choose>
         <xsl:when test="@xml:lang or gmd:language "/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>gmd:language should be present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M34"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M34"/>
   <xsl:template match="ADO:DP_Metadata | gmd:MD_Metadata" priority="4000" mode="M35">
      <xsl:choose>
         <xsl:when test="gmd:dataSetURI or gmd:parentIdentifier"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>dataSetURI is not present therefore parentIdentifier should be present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="gmd:dataSetURI or gmd:hierarchyLevel"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>dataSetURI is not present therefore hierarchyLevel should be present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
         <xsl:when test="gmd:dataSetURI or gmd:hierarchyLevelName"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>dataSetURI is not present therefore hierarchyLevelName should be present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M35"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M35"/>
   <xsl:template match="//ADO:DP_Metadata" priority="4000" mode="M36">
      <xsl:choose>
         <xsl:when test="gmd:referenceSystemInfo"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>referenceSystemInfo is not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M36"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M36"/>
   <xsl:template match="//ADO:DP_Metadata" priority="4000" mode="M37">
      <xsl:choose>
         <xsl:when test="gmd:distributionInfo"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>distributionInfo is not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M37"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M37"/>
   <xsl:template match="//ADO:DP_Metadata" priority="4000" mode="M38">
      <xsl:choose>
         <xsl:when test="gmd:dataQualityInfo"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>dataQualityInfo is not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M38"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M38"/>
   <xsl:template match="//ADO:DP_DataIdentification" priority="4000" mode="M39">
      <xsl:choose>
         <xsl:when test="ADO:resourceConstraints"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>resourceConstraints is not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M39"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M39"/>
   <xsl:template match="//ADO:DP_Distributor" priority="4000" mode="M40">
      <xsl:choose>
         <xsl:when test="gmd:distributionFormat"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>distributionFormat is not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M40"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M40"/>
   <xsl:template match="//ADO:DP_Distributor" priority="4000" mode="M41">
      <xsl:choose>
         <xsl:when test="gmd:distributor"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>distributor is not present.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M41"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M41"/>
   <xsl:template match="//ADO:DP_ResponsibleParty" priority="4000" mode="M42">
      <xsl:choose>
         <xsl:when test="gmd:organisationName and normalize-space(gmd:organisationName)!=''"/>
         <xsl:otherwise>
            <li>
               <a href="schematron-out.html#{generate-id(.)}" target="out"
                  title="Link to where this pattern was expected">
                  <i/>organisationName is not present or has no content.<b/>
               </a>
            </li>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates mode="M42"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M42"/>
   <xsl:template match="text()" priority="-1"/>
</xsl:stylesheet>