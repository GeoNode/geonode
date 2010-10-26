<#--
Body section of the GetFeatureInfo template, it's provided with one feature collection, and
will be called multiple times if there are various feature collections
-->
<#--
Body section of the GetFeatureInfo template, it's provided with one feature collection, and
will be called multiple times if there are various feature collections
-->

layer: "${type.name}",
columns: [
<#list type.attributes as attribute>
  <#if !attribute.isGeometry>
        "${attribute.name}",
  </#if>
</#list>
],
  features: [
<#list features as feature>
  {
  <#list feature.attributes as attribute>
    <#if !attribute.isGeometry>
    "${attribute.name}" : "${attribute.value}",
    </#if>
  </#list>
  },
</#list>
]
