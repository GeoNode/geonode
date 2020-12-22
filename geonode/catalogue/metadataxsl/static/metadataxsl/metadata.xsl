<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:gmd="http://www.isotc211.org/2005/gmd"
                xmlns:gco="http://www.isotc211.org/2005/gco"
                xmlns:gml="http://www.opengis.net/gml/3.2"
                xmlns:gml2="http://www.opengis.net/gml"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:srv="http://www.isotc211.org/2005/srv">

    <xsl:template match="/">
        <!-- VARIABLES -->
        <xsl:variable name="title" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString"/>
        <xsl:variable name="abstract" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:abstract/gco:CharacterString"/>
        <xsl:variable name="titleEN" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:citation/gmd:CI_Citation/gmd:title/gmd:PT_FreeText"/>
        <xsl:variable name="abstractEN" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:abstract/gmd:PT_FreeText"/>
        <xsl:variable name="keywords" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:descriptiveKeywords/gmd:MD_Keywords" />
        <xsl:variable name="res_id_code" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:citation/gmd:CI_Citation/gmd:identifier/*/gmd:code/gco:CharacterString"/>
        <xsl:variable name="res_id_codespace" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:citation/gmd:CI_Citation/gmd:identifier/*/gmd:codeSpace/gco:CharacterString"/>
        <xsl:variable name="hierarchyLevel" select="/gmd:MD_Metadata/gmd:hierarchyLevel/gmd:MD_ScopeCode"/>
        <xsl:variable name="status" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:status/gmd:MD_ProgressCode"/>
        <xsl:variable name="titlealt" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString"/>
        <xsl:variable name="purpose" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:purpose/gco:CharacterString"/>
        <xsl:variable name="topicCategory" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:topicCategory/gmd:MD_TopicCategoryCode"/>
        <!--<xsl:variable name="graphicOverview" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString"/>-->
        <xsl:variable name="graphicOverview" select="//gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL[contains(text(),'uploaded/thumb')]"/>
        <xsl:variable name="ReferenceSystem" select="/gmd:MD_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString"/>
        <xsl:variable name="resourceMaintenance" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode"/>
        <xsl:variable name="language" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:language/gmd:LanguageCode"/>
        <xsl:variable name="characterSet" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:characterSet/gmd:MD_CharacterSetCode"/>
        <xsl:variable name="statement" select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString"/>
        <xsl:variable name="statementEN" select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gmd:PT_FreeText"/>
        <xsl:variable name="specification" select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:title/gco:CharacterString"/>
        <xsl:variable name="specificationDate" select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date"/>
        <xsl:variable name="specificationDateType" select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode"/>
        <xsl:variable name="explanation" select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString"/>
        <xsl:variable name="credits" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:credit/gco:CharacterString"/>
        <xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz'" />
        <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />
        <xsl:variable name="replace" select="'T'" />
        <xsl:variable name="by" select="' '" />
        <xsl:variable name="replace2" select="'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/uom/ML_gmxUom.xml#'" />
        <xsl:variable name="by2" select="''" />
        <xsl:variable name="representationType" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode"/>
        <xsl:variable name="transferSize" select="/gmd:MD_Metadata/gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:transferSize/gco:Real" />
        <xsl:variable name="useLimitation" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString"/>
        <xsl:variable name="accessConstraints" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode"/>
        <xsl:variable name="useConstraints" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode"/>
        <xsl:variable name="otherConstraints" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString"/>
        <xsl:variable name="classification" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:resourceConstraints/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_ClassificationCode"/>
        <xsl:variable name="fileIdentifier" select="/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString"/>
        <xsl:variable name="metalanguage" select="/gmd:MD_Metadata/gmd:language/gmd:LanguageCode"/>
        <xsl:variable name="metacharacterSet" select="/gmd:MD_Metadata/gmd:characterSet/gmd:MD_CharacterSetCode"/>
        <xsl:variable name="dateStamp" select="/gmd:MD_Metadata/gmd:dateStamp/gco:Date"/>
        <xsl:variable name="metadataStandardName" select="/gmd:MD_Metadata/gmd:metadataStandardName/gco:CharacterString"/>
        <xsl:variable name="metadataStandardVersion" select="/gmd:MD_Metadata/gmd:metadataStandardVersion/gco:CharacterString"/>
        <xsl:variable name="point" select="'.'" />
        <xsl:variable name="comma" select="','" />
        <xsl:variable name="serviceType" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/srv:serviceType/gco:LocalName" />
        <xsl:variable name="couplingType" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/srv:couplingType/srv:SV_CouplingType" />
        <xsl:variable name="begin" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml2:TimePeriod/gml2:beginPosition"/>
        <xsl:variable name="end" select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml2:TimePeriod/gml2:endPosition"/>

        <HTML>
            <HEAD>
                <link rel="stylesheet" type="text/css" href="/static/metadataxsl/metadata.css"/>
            </HEAD>

            <BODY ONCONTEXTMENU="return true">
                <!-- LOGOS -->
                <DIV class="logos">
                    <img src="/static/geonode/img/logo-bg.png" class="fright geonodelogo"  />
                </DIV>


                <xsl:if test="$title | $abstract ">
                    <TABLE>
                        <TR>
                            <TD COLSPAN="2" class="header">
                                <!-- title -->
                                <xsl:for-each select="$title[1]">
                                    <H1>
                                        <xsl:value-of select="$title[1]"/>
                                    </H1>
                                </xsl:for-each>
                                <!-- abstract -->
                                <xsl:if test="$abstract">
                                    <P>
                                        <xsl:for-each select="$abstract">
                                            <strong>Abstract: </strong>
                                            <xsl:value-of select="$abstract"/>
                                        </xsl:for-each>
                                    </P>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD COLSPAN="2" class="header">
                                <!-- title -->
                                <xsl:for-each select="$titleEN[1]">
                                    <H2>
                                        <xsl:value-of select="$titleEN[1]"/>
                                    </H2>
                                </xsl:for-each>
                                <!-- abstract -->
                                <xsl:if test="$abstractEN">
                                    <P>
                                        <xsl:for-each select="$abstractEN">
                                            <strong>Abstract: </strong>
                                            <xsl:value-of select="$abstractEN"/>
                                        </xsl:for-each>
                                    </P>
                                </xsl:if>
                            </TD>
                        </TR>
                    </TABLE>
                </xsl:if>


                <TABLE>
                    <!-- Resource Type -->
                    <TR>
                        <TD class="header fixedcol">
                            <strong>Hierarchy level</strong>
                        </TD>
                        <TD class="header">
                            <xsl:if test="$hierarchyLevel ">
                                <xsl:value-of select="$hierarchyLevel"/>
                            </xsl:if>
                        </TD>
                        <!-- GraphicOverview -->
                        <TD class="header" ROWSPAN="4" width="150">
                            <xsl:choose>
                                <xsl:when test="not($graphicOverview)">
                                    <img src="/static/geonode/img/missing_thumb.png" width="150" height="150"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <img>
                                        <xsl:attribute name="src">
                                            <xsl:value-of select="$graphicOverview" />
                                        </xsl:attribute>
                                        <xsl:attribute name="width">150</xsl:attribute>
                                        <xsl:attribute name="height">150</xsl:attribute>
                                        <xsl:attribute name="onError">this.onerror=null;this.src='/static/geonode/img/missing_thumb.png'</xsl:attribute>
                                    </img>
                                </xsl:otherwise>
                            </xsl:choose>
                        </TD>
                    </TR>
                    <!-- Resource Code -->
                    <TR>
                        <TD class="header">
                            <strong>Resource Identifier</strong>
                        </TD>
                        <TD class="header">
                            <xsl:if test="$res_id_code | $res_id_codespace ">
                                <xsl:value-of select="$res_id_code"/> | <xsl:value-of select="$res_id_codespace"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <!-- Resource Alternative Title -->
                    <TR>
                        <TD class="header">
                            <strong>Alternative Title</strong>
                        </TD>
                        <TD class="header">
                            <xsl:if test="$titlealt">
                                <xsl:value-of select="$titlealt"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <!-- Resource Status -->
                    <TR>
                        <TD class="header">
                            <strong>Resource Status</strong>
                        </TD>
                        <TD class="header">
                            <xsl:if test="$status">
                                <xsl:for-each select="$status">
                                    <xsl:value-of select="."/>
                                    <br/>
                                </xsl:for-each>
                            </xsl:if>
                        </TD>
                    </TR>
                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="2" class="header">
                            <H2>WHAT</H2>
                        </TD>
                    </TR>
                    <!-- Resource Purpose -->
                    <TR>
                        <TD class="fixedcol">
                            <strong>Resource Purpose</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$purpose">
                                <xsl:value-of select="$purpose"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <!-- Spatial Representation Type -->
                    <TR>
                        <TD>
                            <strong>Spatial Representation Type</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$representationType">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <!-- Topic Category -->
                    <TR>
                        <TD>
                            <strong>Topic Category</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$topicCategory">
                                <xsl:for-each select="$topicCategory">
                                    <xsl:choose>
                                        <xsl:when test="(.='farming')">Farming <br/> </xsl:when>
                                        <xsl:when test="(.='biota')">Biota <br/> </xsl:when>
                                        <xsl:when test="(.='boundaries')">Boundaries <br/> </xsl:when>
                                        <xsl:when test="(.='climatologyMeteorologyAtmosphere')">Climatology, meteorology, atmosphere <br/> </xsl:when>
                                        <xsl:when test="(.='economy')">Economy <br/> </xsl:when>
                                        <xsl:when test="(.='elevation')">Elevation, Bathymetry <br/> </xsl:when>
                                        <xsl:when test="(.='environment')">Environment <br/> </xsl:when>
                                        <xsl:when test="(.='geoscientificInformation')">Geoscientific information <br/> </xsl:when>
                                        <xsl:when test="(.='health')">Health <br/> </xsl:when>
                                        <xsl:when test="(.='imageryBaseMapsEarthCover')">Imagery base maps earth cover <br/> </xsl:when>
                                        <xsl:when test="(.='intelligenceMilitary')">Intelligence military <br/> </xsl:when>
                                        <xsl:when test="(.='inlandWaters')">Inland waters <br/> </xsl:when>
                                        <xsl:when test="(.='location')">Location <br/> </xsl:when>
                                        <xsl:when test="(.='oceans')">Oceans <br/> </xsl:when>
                                        <xsl:when test="(.='planningCadastre')">Planning cadastre <br/> </xsl:when>
                                        <xsl:when test="(.='society')">Society <br/> </xsl:when>
                                        <xsl:when test="(.='structure')">Structure <br/> </xsl:when>
                                        <xsl:when test="(.='transportation')">Transportation <br/> </xsl:when>
                                        <xsl:when test="(.='utilitiesCommunication')">Utilities communication <br/> </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:value-of select="."/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:for-each>
                            </xsl:if>
                        </TD>
                    </TR>
                    <!-- Free Keywords -->
                    <TR>
                        <TD>
                            <strong>Keywords</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$keywords">
                                <xsl:if test="not(contains(., 'GEMET')) and not(contains(., '19119'))">
                                    <xsl:value-of select="."/>
                                    <br/>
                                </xsl:if>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <!-- Inspire Dataset Theme -->
                    <xsl:if test="contains($keywords, 'GEMET')">
                        <TR>
                            <TD>
                                <strong>Inspire Dataset Theme</strong>
                            </TD>
                            <TD>
                                <xsl:for-each select="$keywords">
                                    <xsl:variable name="thesaurus" select="./gmd:thesaurusName" />
                                    <xsl:variable name="keyword" select="./gmd:keyword/gco:CharacterString" />
                                    <xsl:if test="contains($thesaurus, 'GEMET')">
                                        <xsl:for-each select="$keyword">
                                            <xsl:value-of select="."/>
                                        </xsl:for-each>
                                    </xsl:if>
                                </xsl:for-each>
                            </TD>
                        </TR>
                    </xsl:if>
                    <!-- Inspire Service Theme -->
                    <xsl:if test="contains($keywords, '19119')">
                        <TR>
                            <TD>
                                <strong>Services</strong>
                            </TD>
                            <TD>
                                <xsl:for-each select="$keywords">
                                    <xsl:variable name="thesaurus" select="./gmd:thesaurusName" />
                                    <xsl:variable name="keyword" select="./gmd:keyword/gco:CharacterString" />
                                    <xsl:if test="contains($thesaurus, '19119')">
                                        <xsl:for-each select="$keyword">
                                            <xsl:value-of select="."/>
                                        </xsl:for-each>
                                    </xsl:if>
                                </xsl:for-each>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Related Resources</strong>
                            </TD>
                            <TD>
                                <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/srv:operatesOn">
                                    <xsl:variable name="resURL" select="@xlink:href" />
                                    <a href="{$resURL}" target="_blank">
                                        <xsl:value-of select="$resURL"/>
                                    </a>
                                    <br/>
                                </xsl:for-each>
                            </TD>
                        </TR>
                    </xsl:if>
                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="5" class="header">
                            <H2>WHERE</H2>
                        </TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="5" class="title">
                            GEOGRAPHIC LOCATION
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>North Bound</strong>
                        </TD>
                        <TD>
                            <strong>South Bound</strong>
                        </TD>
                        <TD>
                            <strong>West Bound</strong>
                        </TD>
                        <TD>
                            <strong>East Bound</strong>
                        </TD>
                    </TR>
                    <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/*/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox">
                        <tr>
                            <td>
                                <xsl:value-of select="translate(gmd:northBoundLatitude/gco:Decimal, $point, $comma)"/>
                            </td>
                            <td>
                                <xsl:value-of select="translate(gmd:southBoundLatitude/gco:Decimal, $point, $comma)"/>
                            </td>
                            <td>
                                <xsl:value-of select="translate(gmd:westBoundLongitude/gco:Decimal, $point, $comma)"/>
                            </td>
                            <td>
                                <xsl:value-of select="translate(gmd:eastBoundLongitude/gco:Decimal, $point, $comma)"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                    <TR>
                        <TD COLSPAN="4" class="title">
                            GEOGRAPHIC IDENTIFICATOR
                        </TD>
                    </TR>
                    <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicDescription">
                        <tr>
                            <td COLSPAN="4">
                                <xsl:value-of select="gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                    <TR>
                        <TD class="fixedcol">
                            <strong>Reference Systems</strong>
                        </TD>
                        <TD COLSPAN="4">
                            <xsl:for-each select="$ReferenceSystem">
                                <xsl:choose>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/4936')">ETRS89 / Geocentric <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/4937')">ETRS89 / Geocentric 3D <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/4258')">ETRS89 / Coordenadas Geocêntricas 2D <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3763')">ETRS89 / PT-TM06 <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5018')">Lisbon / Portuguese Grid New / Hayford-Gauss <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/20790')">Lisbon (Lisbon) / Portuguese National Grid<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5011')">ITRF93 / Geocentric <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5012')">ITRF93 / Geocentric 3D <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5013')">ITRF93 / Geocentric 2D <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5014')">ITRF93 / PTRA08 - UTM 25N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5015')">ITRF93 / PTRA08 - UTM 26N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5016')">ITRF93 / PTRA08 - UTM 28N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/2188')">Azores Occidental 1939 / UTM zone 25N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/2189')">Azores Central 1948 / UTM zone 26N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/2190')">Azores Oriental 1940 / UTM zone 26N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/2942')">Porto Santo / UTM zone 28N<br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3035')">ETRS89 / ETRS-LAEA (Lambert Azimuthal Equal Area) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3034')">ETRS89 / ETRS-LCC (Lambert Conformal Conic) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3038')">ETRS89 / ETRS-TM26N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3039')">ETRS89 / ETRS-TM27N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3040')">ETRS89 / ETRS-TM28N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3041')">ETRS89 / ETRS-TM29N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3042')">ETRS89 / ETRS-TM30N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3043')">ETRS89 / ETRS-TM31N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3044')">ETRS89 / ETRS-TM32N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3045')">ETRS89 / ETRS-TM33N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3046')">ETRS89 / ETRS-TM34N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3047')">ETRS89 / ETRS-TM35N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3048')">ETRS89 / ETRS-TM36N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3049')">ETRS89 / ETRS-TM37N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3050')">ETRS89 / ETRS-TM38N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3051')">ETRS89 / ETRS-TM39N (Transverse Mercator) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/5730')">EVRF2000 height (European Vertical Reference Frame 2000) <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/7409')">ETRS89 + EVRF2000 <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/4326')">WGS 84 / Geographic <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/3061')">Porto Santo 1995 / UTM Zona 28N <br/></xsl:when>
                                    <xsl:when test="(.='http://www.opengis.net/def/crs/EPSG/0/32628')">WGS 84 / UTM zone 28N <br/></xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="."/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="5" class="title">VERTICAL EXTENT</TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="1">
                            <strong>Min value</strong>
                        </TD>
                        <TD COLSPAN="1">
                            <strong>Max value</strong>
                        </TD>
                        <TD COLSPAN="3">
                            <strong>System Identificator</strong>
                        </TD>
                    </TR>

                    <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent">
                        <tr>
                            <td COLSPAN="1">
                                <xsl:value-of select="translate(gmd:minimumValue/gco:Real, $point, $comma)"/>
                            </td>
                            <td COLSPAN="1">
                                <xsl:value-of select="translate(gmd:maximumValue/gco:Real, $point, $comma)"/>
                            </td>
                            <td COLSPAN="3">
                                <xsl:choose>
                                    <xsl:when test="(gmd:verticalCRS/@xlink:href='urn:ogc:def:crs:EPSG:5701')">EPSG:5701 - ODN height</xsl:when>
                                    <xsl:when test="(gmd:verticalCRS/@xlink:href='urn:ogc:def:crs:EPSG:5780')">EPSG:5780 - Cascais height</xsl:when>
                                    <xsl:when test="(gmd:verticalCRS/@xlink:href='urn:ogc:def:crs:EPSG:5782')">EPSG:5782 - Alicante height</xsl:when>
                                    <xsl:when test="(gmd:verticalCRS/@xlink:href='urn:ogc:def:crs:EPSG:5730')">EPSG:5730 - EVRF2000</xsl:when>
                                    <xsl:when test="(gmd:verticalCRS/@xlink:href='urn:ogc:def:crs:EPSG:5621')">EPSG:5621 - EVRF2007</xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="gmd:verticalCRS/@xlink:href"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </td>
                        </tr>
                    </xsl:for-each>
                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="2" class="header">
                            <H2>WHEN</H2>
                        </TD>
                    </TR>
                    <TR>
                        <TD class="fixedcol">
                            <strong>Temporal References</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date">
                                <xsl:value-of select="gmd:date/gco:Date"/> ( <xsl:value-of select="gmd:dateType/gmd:CI_DateTypeCode"/> ) <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Temporal Extension</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$begin">
                                <xsl:value-of select="translate($begin, $replace, $by)"/> / <xsl:value-of select="translate($end, $replace, $by)"/>
                                <br/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <!-- resourceMaintenance -->
                    <TR>
                        <TD>
                            <strong>Resource Maintenance</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$resourceMaintenance ">
                                <xsl:value-of select="$resourceMaintenance"/>
                            </xsl:if>
                        </TD>
                    </TR>

                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="2" class="header">
                            <H2>HOW</H2>
                        </TD>
                    </TR>
                    <xsl:if test="not($serviceType)">
                        <!-- spatialResolution -->
                        <TR>
                            <TD COLSPAN="2" class="title">
                                SPATIAL RESOLUTION
                            </TD>
                        </TR>
                        <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:spatialResolution/gmd:MD_Resolution">
                            <TR>
                                <xsl:variable name="equivalentScale" select="./gmd:equivalentScale" />
                                <xsl:variable name="distance" select="./gmd:distance" />
                                <xsl:variable name="unit" select="./gmd:distance/gco:Distance" />
                                <xsl:if test="$equivalentScale">
                                    <TD>
                                        <strong>Equivalent Scale</strong>
                                    </TD>
                                    <TD>
                                        <xsl:choose>
                                            <xsl:when test="(./gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer='-1')">Unknown</xsl:when>
                                            <xsl:otherwise>1:<xsl:value-of select="./gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer"/></xsl:otherwise>
                                        </xsl:choose>
                                    </TD>
                                </xsl:if>
                                <xsl:if test="$distance">
                                    <TD>
                                        <strong>Distance</strong>
                                    </TD>
                                    <TD>
                                        <xsl:choose>
                                            <xsl:when test="contains($unit/@uom, '#m')">
                                                <xsl:value-of select="translate($distance, $point, $comma)"/> metre</xsl:when>
                                            <xsl:when test="contains($unit/@uom, '#deg')">
                                                <xsl:value-of select="translate($distance, $point, $comma)"/> deg</xsl:when>
                                            <xsl:when test="contains($unit/@uom, '#rad')">
                                                <xsl:value-of select="translate($distance, $point, $comma)"/> rad</xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="translate($distance, $point, $comma)"/>
                                                <xsl:value-of select="translate($unit/@uom, $replace2, $by2)"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </TD>
                                </xsl:if>
                            </TR>
                        </xsl:for-each>
                    </xsl:if>

                    <TR>
                        <TD COLSPAN="3" class="title">QUALITY</TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Statement</strong>
                        </TD>
                        <TD COLSPAN="2">
                            <xsl:if test="$statement">
                                <xsl:value-of select="$statement"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD class="fixedcol">
                            <strong>Process Step <br /> (Description | Date | Rationale)</strong>
                        </TD>
                        <TD COLSPAN="2">
                            <xsl:for-each select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LI_ProcessStep">
                                <xsl:value-of select="gmd:description"/> | <xsl:value-of select="gmd:dateTime/gco:DateTime"/> | <xsl:value-of select="gmd:rationale/gco:CharacterString"/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Data Source</strong>
                        </TD>
                        <TD COLSPAN="2">
                            <xsl:for-each select="/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source/gmd:description">
                                <xsl:value-of select="gco:CharacterString"/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="3"><strong>Conformity results</strong></TD>
                    </TR>
                    <TR>
                        <TD><strong>Specification</strong></TD>
                        <TD COLSPAN="2">
                            <xsl:if test="$specification">
                                <xsl:value-of select="$specification"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD><strong>Specification Date</strong></TD>
                        <TD COLSPAN="2">
                            <xsl:if test="$specificationDate">
                                <xsl:value-of select="$specificationDate"/> ( <xsl:value-of select="$specificationDateType"/> )
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD><strong>Explanation</strong></TD>
                        <TD COLSPAN="2">
                            <xsl:if test="$explanation">
                                <xsl:value-of select="$explanation"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Conformance pass</strong>
                        </TD>
                        <TD COLSPAN="2">
                            <xsl:choose>
                                <xsl:when test="(/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:pass/gco:Boolean='true')">True</xsl:when>
                                <xsl:when test="(/gmd:MD_Metadata/gmd:dataQualityInfo[1]/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:pass/gco:Boolean='false')">False</xsl:when>
                                <xsl:otherwise></xsl:otherwise>
                            </xsl:choose>
                        </TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="2" class="title">
                            OTHER INFO
                        </TD>
                    </TR>
                    <!-- Idioma do Recurso -->
                    <TR>
                        <TD>
                            <strong>Language</strong>
                        </TD>
                        <TD COLSPAN="2">
                            <xsl:if test="$language">
                                <xsl:value-of select="$language"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <!-- Codificação do Recurso -->
                    <TR>
                        <TD>
                            <strong>Character Set</strong>
                        </TD>
                        <TD COLSPAN="2">
                            <xsl:if test="$characterSet">
                                <xsl:value-of select="$characterSet"/>
                            </xsl:if>
                        </TD>
                    </TR>
                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="2" class="header">
                            <H2>WHO</H2>
                        </TD>
                    </TR>
                    <!-- Responsável pelo Recurso -->
                    <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/gmd:pointOfContact/gmd:CI_ResponsibleParty">
                        <!-- Role -->
                        <TR>
                            <TD COLSPAN="2" class="title">
                                <xsl:if test="gmd:role/gmd:CI_RoleCode">
                                    <xsl:value-of select="translate(gmd:role/gmd:CI_RoleCode, $smallcase, $uppercase)" />
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Organisation</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:organisationName">
                                    <strong>
                                        <xsl:value-of select="gmd:organisationName/gco:CharacterString"/>
                                    </strong>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Individual Name</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:individualName">
                                    <xsl:value-of select="gmd:individualName/gco:CharacterString"/>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Address</strong>
                            </TD>
                            <TD>
                                <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:deliveryPoint/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:postalCode/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:city/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:country/gco:CharacterString"/>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Telephone</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:contactInfo/gmd:CI_Contact/gmd:phone/gmd:CI_Telephone/gmd:voice">
                                    <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:phone/gmd:CI_Telephone/gmd:voice/gco:CharacterString"/>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>E-mail</strong>
                            </TD>
                            <TD>
                                <xsl:for-each select="./gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString">
                                    <xsl:value-of select="."/>
                                    <br/>
                                </xsl:for-each>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Online Resource</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:contactInfo/gmd:CI_Contact/gmd:onlineResource/gmd:CI_OnlineResource/gmd:linkage/gmd:URL">
                                    <xsl:variable name="URL" select="gmd:contactInfo/gmd:CI_Contact/gmd:onlineResource/gmd:CI_OnlineResource/gmd:linkage/gmd:URL" />
                                    <a href="{$URL}" target="_blank">
                                        <xsl:value-of select="$URL"/>
                                    </a>
                                </xsl:if>
                            </TD>
                        </TR>
                    </xsl:for-each>
                    <TR>
                        <TD COLSPAN="2" class="title">
                            OTHER INFO
                        </TD>
                    </TR>
                    <TR>
                        <TD class="fixedcol">
                            <strong>Credits</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$credits">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="2" class="header">
                            <H2>DISTRIBUTION</H2>
                        </TD>
                    </TR>
                    <TR>
                        <TD class="fixedcol">
                            <strong>Online resources</strong>
                        </TD>
                        <TD>
                            <TABLE>

                                <xsl:variable name="onlineNodes" select="/gmd:MD_Metadata/gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine" />
                                <xsl:variable name="function" select="/gmd:MD_Metadata/gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine" />
                                <xsl:for-each select="$onlineNodes">
                                    <TR>
                                        <xsl:variable name="name" select="./gmd:CI_OnlineResource/gmd:name" />
                                        <xsl:variable name="descr" select="./gmd:CI_OnlineResource/gmd:description" />
                                        <TD>
                                            <a href="{./gmd:CI_OnlineResource/gmd:linkage/gmd:URL}">
                                                <xsl:choose>
                                                    <xsl:when test="$descr">
                                                        <xsl:value-of select="$descr"/>
                                                    </xsl:when>
                                                    <xsl:when test="$name">
                                                        <xsl:value-of select="$name"/>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <xsl:value-of select="./gmd:CI_OnlineResource/gmd:linkage/gmd:URL"/>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </a>
                                        </TD>
                                    </TR>
                                </xsl:for-each>
                            </TABLE>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Distribution format</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="/gmd:MD_Metadata/gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:distributionFormat">
                                <xsl:value-of select="./gmd:MD_Format/gmd:name/gco:CharacterString"/> ( version <xsl:value-of select="./gmd:MD_Format/gmd:version/gco:CharacterString"/> ) <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>File size</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$transferSize">
                                <xsl:value-of select="$transferSize"/> MB <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <xsl:if test="$serviceType">
                        <TR>
                            <TD COLSPAN="2" class="title">
                                SERVICES
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Service type | Coupling type</strong>
                            </TD>
                            <TD>
                                <xsl:choose>
                                    <xsl:when test="($serviceType='discovery')">Discovery | <xsl:value-of select="$couplingType"/></xsl:when>
                                    <xsl:when test="($serviceType='view')">View | <xsl:value-of select="$couplingType"/></xsl:when>
                                    <xsl:when test="($serviceType='download')">Download | <xsl:value-of select="$couplingType"/></xsl:when>
                                    <xsl:when test="($serviceType='transformation')">Transformation | <xsl:value-of select="$couplingType"/></xsl:when>
                                    <xsl:when test="($serviceType='invoke')">Invocation | <xsl:value-of select="$couplingType"/></xsl:when>
                                    <xsl:when test="($serviceType='other')">Other | <xsl:value-of select="$couplingType"/></xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$serviceType"/> | <xsl:value-of select="$couplingType"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Operations</strong>
                            </TD>
                            <TD>
                                <strong>DCP | Access points</strong>
                            </TD>
                        </TR>
                        <xsl:for-each select="/gmd:MD_Metadata/gmd:identificationInfo[1]/*/srv:containsOperations/srv:SV_OperationMetadata">
                            <TR>
                                <TD>
                                    <xsl:value-of select="srv:operationName/gco:CharacterString"/>
                                </TD>
                                <xsl:variable name="DCP" select="./srv:DCP/srv:DCPList" />
                                <xsl:variable name="connectPoint" select="./srv:connectPoint" />
                                <TD>
                                    <xsl:for-each select="$DCP">
                                        <xsl:value-of select="."/> | <xsl:value-of select="$connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL"/>
                                        <br/>
                                    </xsl:for-each>
                                </TD>
                            </TR>
                        </xsl:for-each>
                    </xsl:if>
                    <TR>
                        <TD COLSPAN="2" class="title">
                            LEGAL RESTRICTIONS
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Use limitations</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$useLimitation">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Access limitations</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$accessConstraints">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Use restrictions</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$useConstraints">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Other restrictions</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$otherConstraints">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Security restrictions</strong>
                        </TD>
                        <TD>
                            <xsl:for-each select="$classification">
                                <xsl:value-of select="."/>
                                <br/>
                            </xsl:for-each>
                        </TD>
                    </TR>
                    <!-- Responsible party for distribution -->
                    <TR>
                        <TD COLSPAN="2" class="title">
                            DISTRIBUTOR
                        </TD>
                    </TR>
                    <xsl:for-each select="/gmd:MD_Metadata/gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact/gmd:CI_ResponsibleParty">
                        <TR>
                            <TD>
                                <strong>Organization</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:organisationName">
                                    <strong>
                                        <xsl:value-of select="gmd:organisationName/gco:CharacterString"/>
                                    </strong>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Individual name</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:individualName">
                                    <xsl:value-of select="gmd:individualName/gco:CharacterString"/>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Address</strong>
                            </TD>
                            <TD>
                                <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:deliveryPoint/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:postalCode/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:city/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:country/gco:CharacterString"/>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Telephone</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:contactInfo/gmd:CI_Contact/gmd:phone/gmd:CI_Telephone/gmd:voice">
                                    <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:phone/gmd:CI_Telephone/gmd:voice/gco:CharacterString"/>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>E-mail</strong>
                            </TD>
                            <TD>
                                <xsl:for-each select="./gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString">
                                    <xsl:value-of select="."/>
                                    <br/>
                                </xsl:for-each>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Online resource</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:contactInfo/gmd:CI_Contact/gmd:onlineResource/gmd:CI_OnlineResource/gmd:linkage/gmd:URL">
                                    <xsl:variable name="URL" select="gmd:contactInfo/gmd:CI_Contact/gmd:onlineResource/gmd:CI_OnlineResource/gmd:linkage/gmd:URL" />
                                    <a href="{$URL}" target="_blank">
                                        <xsl:value-of select="$URL"/>
                                    </a>
                                </xsl:if>
                            </TD>
                        </TR>
                    </xsl:for-each>
                </TABLE>

                <TABLE>
                    <TR>
                        <TD COLSPAN="2" class="header">
                            <H2>METAINFO</H2>
                        </TD>
                    </TR>
                    <TR>
                        <TD class="fixedcol">
                            <strong>Identifier</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$fileIdentifier">
                                <xsl:value-of select="$fileIdentifier"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Date</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$dateStamp">
                                <xsl:value-of select="$dateStamp"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Language</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$metalanguage">
                                <xsl:value-of select="$metalanguage"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Character set</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$metacharacterSet">
                                <xsl:value-of select="$metacharacterSet"/>
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD>
                            <strong>Metadata standard / profile</strong>
                        </TD>
                        <TD>
                            <xsl:if test="$metadataStandardName">
                                <xsl:value-of select="$metadataStandardName"/> ( version <xsl:value-of select="$metadataStandardVersion"/> )
                            </xsl:if>
                        </TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="2" class="title">
                            Responsible parties
                        </TD>
                    </TR>
                    <xsl:for-each select="/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty">
                        <TR>
                            <TD>
                                <strong>Organisation</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:organisationName">
                                    <strong>
                                        <xsl:value-of select="gmd:organisationName/gco:CharacterString"/>
                                    </strong>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Individual Name</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:individualName">
                                    <xsl:value-of select="gmd:individualName/gco:CharacterString"/>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Address</strong>
                            </TD>
                            <TD>
                                <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:deliveryPoint/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:postalCode/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:city/gco:CharacterString"/>, <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:country/gco:CharacterString"/>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Telephone</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:contactInfo/gmd:CI_Contact/gmd:phone/gmd:CI_Telephone/gmd:voice">
                                    <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:phone/gmd:CI_Telephone/gmd:voice/gco:CharacterString"/>
                                </xsl:if>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>E-mail</strong>
                            </TD>
                            <TD>
                                <xsl:for-each select="./gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString">
                                    <xsl:value-of select="."/>
                                    <br/>
                                </xsl:for-each>
                            </TD>
                        </TR>
                        <TR>
                            <TD>
                                <strong>Online resource</strong>
                            </TD>
                            <TD>
                                <xsl:if test="gmd:contactInfo/gmd:CI_Contact/gmd:onlineResource/gmd:CI_OnlineResource/gmd:linkage/gmd:URL">
                                    <xsl:variable name="URL" select="gmd:contactInfo/gmd:CI_Contact/gmd:onlineResource/gmd:CI_OnlineResource/gmd:linkage/gmd:URL" />
                                    <a href="{$URL}" target="_blank">
                                        <xsl:value-of select="$URL"/>
                                    </a>
                                </xsl:if>
                            </TD>
                        </TR>
                    </xsl:for-each>
                </TABLE>

                <br/>
                <br/>

            </BODY>
        </HTML>
    </xsl:template>

</xsl:stylesheet>
