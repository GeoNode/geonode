/**
 * @file Intake system parameter graph
 * configurations (Step 2 of create wizard)
 * @version 1.0
 */
/**  
 * Global variables for save data 
 * @param {Array} resultdb   all data from DB
 * @param {Object} selectedCell  cell selected from Diagram 
 */

var resultdb = [];
var selectedCell;
var graphData = [];
var connection = [];
var funcostdb = [];
var bandera = true;
var xmlGraph = `<mxGraphModel>
<root>
  <Diagram label="My Diagram" href="http://www.jgraph.com/" id="0">
    <mxCell />
  </Diagram>
  <Layer label="Default Layer" id="1">
    <mxCell parent="0" />
  </Layer>
  <Symbol label="River (2)" name="River" externalData="false" varcost="[&quot;Q_2&quot;,&quot;CSed_2&quot;,&quot;CN_2&quot;,&quot;CP_2&quot;,&quot;WSed_2&quot;,&quot;WN_2&quot;,&quot;WP_2&quot;,&quot;WSed_ret_2&quot;,&quot;WN_ret_2&quot;,&quot;WP_ret_2&quot;]" resultdb="[{&quot;model&quot;: &quot;waterproof_intake.processefficiencies&quot;, &quot;pk&quot;: 34, &quot;fields&quot;: {&quot;name&quot;: &quot;Captaci\u00f3n&quot;, &quot;unitary_process&quot;: &quot;River&quot;, &quot;symbol&quot;: &quot;R&quot;, &quot;categorys&quot;: &quot;River&quot;, &quot;normalized_category&quot;: &quot;RIVER&quot;, &quot;id_wb&quot;: 0, &quot;minimal_sediment_perc&quot;: 0, &quot;predefined_sediment_perc&quot;: &quot;0.00&quot;, &quot;maximal_sediment_perc&quot;: 0, &quot;minimal_nitrogen_perc&quot;: 0, &quot;predefined_nitrogen_perc&quot;: &quot;0.00&quot;, &quot;maximal_nitrogen_perc&quot;: 0, &quot;minimal_phoshorus_perc&quot;: 0, &quot;predefined_phosphorus_perc&quot;: &quot;0.00&quot;, &quot;maximal_phosphorus_perc&quot;: 0, &quot;minimal_transp_water_perc&quot;: 1, &quot;predefined_transp_water_perc&quot;: &quot;100.00&quot;, &quot;maximal_transp_water_perc&quot;: 100}}]" id="2">
    <mxCell style="rio" parent="1" vertex="1">
      <mxGeometry x="40" y="30" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <Symbol name="Bocatoma" label="Water Intake (3)" externalData="false" varcost="[&quot;Q_3&quot;,&quot;CSed_3&quot;,&quot;CN_3&quot;,&quot;CP_3&quot;,&quot;WSed_3&quot;,&quot;WN_3&quot;,&quot;WP_3&quot;,&quot;WSed_ret_3&quot;,&quot;WN_ret_3&quot;,&quot;WP_ret_3&quot;]" resultdb="[{&quot;model&quot;: &quot;waterproof_intake.processefficiencies&quot;, &quot;pk&quot;: 2, &quot;fields&quot;: {&quot;name&quot;: &quot;Captaci\u00f3n&quot;, &quot;unitary_process&quot;: &quot;Bocatoma&quot;, &quot;symbol&quot;: &quot;BO&quot;, &quot;categorys&quot;: &quot;Bocatoma de Fondo&quot;, &quot;normalized_category&quot;: &quot;BOCATOMADEFONDO&quot;, &quot;id_wb&quot;: 0, &quot;minimal_sediment_perc&quot;: 1, &quot;predefined_sediment_perc&quot;: &quot;2.50&quot;, &quot;maximal_sediment_perc&quot;: 4, &quot;minimal_nitrogen_perc&quot;: 1, &quot;predefined_nitrogen_perc&quot;: &quot;1.10&quot;, &quot;maximal_nitrogen_perc&quot;: 4, &quot;minimal_phoshorus_perc&quot;: 1, &quot;predefined_phosphorus_perc&quot;: &quot;1.42&quot;, &quot;maximal_phosphorus_perc&quot;: 4, &quot;minimal_transp_water_perc&quot;: 0, &quot;predefined_transp_water_perc&quot;: &quot;100.00&quot;, &quot;maximal_transp_water_perc&quot;: 100}}]" funcost="[{&quot;model&quot;: &quot;waterproof_intake.costfunctionsprocess&quot;, &quot;pk&quot;: 10401, &quot;fields&quot;: {&quot;symbol&quot;: &quot;BO&quot;, &quot;categorys&quot;: &quot;Bocatoma de Fondo&quot;, &quot;energy&quot;: &quot;0.0000&quot;, &quot;labour&quot;: &quot;90.0000&quot;, &quot;mater_equipment&quot;: &quot;10.0000&quot;, &quot;function_value&quot;: &quot;(4.1181*(text(Q)^(-0.344)))*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))&quot;, &quot;function_name&quot;: &quot;Bocatoma de Fondo&quot;, &quot;function_description&quot;: null}}, {&quot;model&quot;: &quot;waterproof_intake.costfunctionsprocess&quot;, &quot;pk&quot;: 10402, &quot;fields&quot;: {&quot;symbol&quot;: &quot;BO&quot;, &quot;categorys&quot;: &quot;Bocatoma Lateral&quot;, &quot;energy&quot;: &quot;0.0000&quot;, &quot;labour&quot;: &quot;90.0000&quot;, &quot;mater_equipment&quot;: &quot;10.0000&quot;, &quot;function_value&quot;: &quot;((381.44*text(Q)) + 46465.2)*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))&quot;, &quot;function_name&quot;: &quot;Bocatoma Lateral&quot;, &quot;function_description&quot;: null}}]" id="3">
    <mxCell style="bocatoma" parent="1" vertex="1" dbreference="BOCATOMADEFONDO" funcionreference="BO">
      <mxGeometry x="250" y="30" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <mxCell id="4" value="{&quot;connectorType&quot;:&quot;EC&quot;,&quot;varcost&quot;:[&quot;Q_4&quot;,&quot;CSed_4&quot;,&quot;CN_4&quot;,&quot;CP_4&quot;,&quot;WSed_4&quot;,&quot;WN_4&quot;,&quot;WP_4&quot;,&quot;WSed_ret_4&quot;,&quot;WN_ret_4&quot;,&quot;WP_ret_4&quot;],&quot;external&quot;:false,&quot;resultdb&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.processefficiencies\&quot;, \&quot;pk\&quot;: 30, \&quot;fields\&quot;: {\&quot;name\&quot;: \&quot;Captaci\\u00f3n\&quot;, \&quot;unitary_process\&quot;: \&quot;Extraction connection\&quot;, \&quot;symbol\&quot;: \&quot;EC\&quot;, \&quot;categorys\&quot;: \&quot;Extraction connection\&quot;, \&quot;normalized_category\&quot;: \&quot;EXTRACTIONCONNECTION\&quot;, \&quot;id_wb\&quot;: 0, \&quot;minimal_sediment_perc\&quot;: 0, \&quot;predefined_sediment_perc\&quot;: \&quot;3.00\&quot;, \&quot;maximal_sediment_perc\&quot;: 99, \&quot;minimal_nitrogen_perc\&quot;: 0, \&quot;predefined_nitrogen_perc\&quot;: \&quot;6.00\&quot;, \&quot;maximal_nitrogen_perc\&quot;: 25, \&quot;minimal_phoshorus_perc\&quot;: 0, \&quot;predefined_phosphorus_perc\&quot;: \&quot;10.00\&quot;, \&quot;maximal_phosphorus_perc\&quot;: 80, \&quot;minimal_transp_water_perc\&quot;: 0, \&quot;predefined_transp_water_perc\&quot;: \&quot;100.00\&quot;, \&quot;maximal_transp_water_perc\&quot;: 100}}]&quot;,&quot;name&quot;:&quot;Extraction connection&quot;,&quot;funcost&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.costfunctionsprocess\&quot;, \&quot;pk\&quot;: 10901, \&quot;fields\&quot;: {\&quot;symbol\&quot;: \&quot;EC\&quot;, \&quot;categorys\&quot;: \&quot;Conexion Extraccion\&quot;, \&quot;energy\&quot;: \&quot;20.0000\&quot;, \&quot;labour\&quot;: \&quot;60.0000\&quot;, \&quot;mater_equipment\&quot;: \&quot;20.0000\&quot;, \&quot;function_value\&quot;: \&quot;15.43*text(Wsed)*((1^6)/31536)\&quot;, \&quot;function_name\&quot;: \&quot;Canal\&quot;, \&quot;function_description\&quot;: null}}]&quot;}" style="EXTRACTIONCONNECTION" parent="1" source="2" target="3" edge="1">
    <mxGeometry relative="1" as="geometry" />
  </mxCell>
  <Symbol name="Desarenador" label="Desander (5)" externalData="false" varcost="[&quot;Q_5&quot;,&quot;CSed_5&quot;,&quot;CN_5&quot;,&quot;CP_5&quot;,&quot;WSed_5&quot;,&quot;WN_5&quot;,&quot;WP_5&quot;,&quot;WSed_ret_5&quot;,&quot;WN_ret_5&quot;,&quot;WP_ret_5&quot;]" resultdb="[{&quot;model&quot;: &quot;waterproof_intake.processefficiencies&quot;, &quot;pk&quot;: 5, &quot;fields&quot;: {&quot;name&quot;: &quot;Captaci\u00f3n&quot;, &quot;unitary_process&quot;: &quot;Desarenador&quot;, &quot;symbol&quot;: &quot;D&quot;, &quot;categorys&quot;: &quot;Desarenador&quot;, &quot;normalized_category&quot;: &quot;DESARENADOR&quot;, &quot;id_wb&quot;: 0, &quot;minimal_sediment_perc&quot;: 2, &quot;predefined_sediment_perc&quot;: &quot;4.50&quot;, &quot;maximal_sediment_perc&quot;: 7, &quot;minimal_nitrogen_perc&quot;: 1, &quot;predefined_nitrogen_perc&quot;: &quot;1.98&quot;, &quot;maximal_nitrogen_perc&quot;: 5, &quot;minimal_phoshorus_perc&quot;: 1, &quot;predefined_phosphorus_perc&quot;: &quot;2.55&quot;, &quot;maximal_phosphorus_perc&quot;: 7, &quot;minimal_transp_water_perc&quot;: 0, &quot;predefined_transp_water_perc&quot;: &quot;100.00&quot;, &quot;maximal_transp_water_perc&quot;: 100}}]" funcost="[{&quot;model&quot;: &quot;waterproof_intake.costfunctionsprocess&quot;, &quot;pk&quot;: 10501, &quot;fields&quot;: {&quot;symbol&quot;: &quot;D&quot;, &quot;categorys&quot;: &quot;Desarenador&quot;, &quot;energy&quot;: &quot;3.0000&quot;, &quot;labour&quot;: &quot;89.0000&quot;, &quot;mater_equipment&quot;: &quot;8.0000&quot;, &quot;function_value&quot;: &quot;((16.498*text(Q)) + 10264)*((16.498*text(Q)) + 10264)*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))&quot;, &quot;function_name&quot;: &quot;Desarenador&quot;, &quot;function_description&quot;: null}}]" id="5">
    <mxCell style="desarenador" parent="1" vertex="1" dbreference="DESARENADOR" funcionreference="D">
      <mxGeometry x="410" y="30" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <mxCell id="6" value="{&quot;connectorType&quot;:&quot;CH&quot;,&quot;varcost&quot;:[&quot;Q_6&quot;,&quot;CSed_6&quot;,&quot;CN_6&quot;,&quot;CP_6&quot;,&quot;WSed_6&quot;,&quot;WN_6&quot;,&quot;WP_6&quot;,&quot;WSed_ret_6&quot;,&quot;WN_ret_6&quot;,&quot;WP_ret_6&quot;],&quot;external&quot;:false,&quot;resultdb&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.processefficiencies\&quot;, \&quot;pk\&quot;: 8, \&quot;fields\&quot;: {\&quot;name\&quot;: \&quot;Captaci\\u00f3n\&quot;, \&quot;unitary_process\&quot;: \&quot;Canal\&quot;, \&quot;symbol\&quot;: \&quot;C\&quot;, \&quot;categorys\&quot;: \&quot;Canal\&quot;, \&quot;normalized_category\&quot;: \&quot;CHANNEL\&quot;, \&quot;id_wb\&quot;: 0, \&quot;minimal_sediment_perc\&quot;: 1, \&quot;predefined_sediment_perc\&quot;: \&quot;2.00\&quot;, \&quot;maximal_sediment_perc\&quot;: 7, \&quot;minimal_nitrogen_perc\&quot;: 1, \&quot;predefined_nitrogen_perc\&quot;: \&quot;0.88\&quot;, \&quot;maximal_nitrogen_perc\&quot;: 5, \&quot;minimal_phoshorus_perc\&quot;: 1, \&quot;predefined_phosphorus_perc\&quot;: \&quot;1.13\&quot;, \&quot;maximal_phosphorus_perc\&quot;: 7, \&quot;minimal_transp_water_perc\&quot;: 0, \&quot;predefined_transp_water_perc\&quot;: \&quot;100.00\&quot;, \&quot;maximal_transp_water_perc\&quot;: 100}}]&quot;,&quot;name&quot;:&quot;Channel&quot;,&quot;funcost&quot;:&quot;[]&quot;}" style="CHANNEL" parent="1" source="3" target="5" edge="1">
    <mxGeometry relative="1" as="geometry" />
  </mxCell>
  <Symbol name="Reservorio de Agua Cruda (RAC)" label="Water reservoir (7)" externalData="false" varcost="[&quot;Q_7&quot;,&quot;CSed_7&quot;,&quot;CN_7&quot;,&quot;CP_7&quot;,&quot;WSed_7&quot;,&quot;WN_7&quot;,&quot;WP_7&quot;,&quot;WSed_ret_7&quot;,&quot;WN_ret_7&quot;,&quot;WP_ret_7&quot;]" resultdb="[{&quot;model&quot;:&quot;waterproof_intake.processefficiencies&quot;,&quot;pk&quot;:28,&quot;fields&quot;:{&quot;name&quot;:&quot;Captación&quot;,&quot;unitary_process&quot;:&quot;Reservorio Agua Cruda&quot;,&quot;symbol&quot;:&quot;RAC&quot;,&quot;categorys&quot;:&quot;No Aplica&quot;,&quot;normalized_category&quot;:&quot;RESERVORIOAGUACRUDA&quot;,&quot;id_wb&quot;:0,&quot;minimal_sediment_perc&quot;:34,&quot;predefined_sediment_perc&quot;:&quot;1&quot;,&quot;maximal_sediment_perc&quot;:99,&quot;minimal_nitrogen_perc&quot;:15,&quot;predefined_nitrogen_perc&quot;:&quot;2&quot;,&quot;maximal_nitrogen_perc&quot;:55,&quot;minimal_phoshorus_perc&quot;:20,&quot;predefined_phosphorus_perc&quot;:&quot;3&quot;,&quot;maximal_phosphorus_perc&quot;:70,&quot;minimal_transp_water_perc&quot;:0,&quot;predefined_transp_water_perc&quot;:&quot;100&quot;,&quot;maximal_transp_water_perc&quot;:100}}]" id="7">
    <mxCell style="reservorioagua" parent="1" vertex="1" dbreference="RESERVORIOAGUACRUDA" funcionreference="">
      <mxGeometry x="580" y="30" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <mxCell id="8" value="{&quot;connectorType&quot;:&quot;CH&quot;,&quot;varcost&quot;:[&quot;Q_8&quot;,&quot;CSed_8&quot;,&quot;CN_8&quot;,&quot;CP_8&quot;,&quot;WSed_8&quot;,&quot;WN_8&quot;,&quot;WP_8&quot;,&quot;WSed_ret_8&quot;,&quot;WN_ret_8&quot;,&quot;WP_ret_8&quot;],&quot;external&quot;:false,&quot;resultdb&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.processefficiencies\&quot;, \&quot;pk\&quot;: 8, \&quot;fields\&quot;: {\&quot;name\&quot;: \&quot;Captaci\\u00f3n\&quot;, \&quot;unitary_process\&quot;: \&quot;Canal\&quot;, \&quot;symbol\&quot;: \&quot;C\&quot;, \&quot;categorys\&quot;: \&quot;Canal\&quot;, \&quot;normalized_category\&quot;: \&quot;CHANNEL\&quot;, \&quot;id_wb\&quot;: 0, \&quot;minimal_sediment_perc\&quot;: 1, \&quot;predefined_sediment_perc\&quot;: \&quot;2.00\&quot;, \&quot;maximal_sediment_perc\&quot;: 7, \&quot;minimal_nitrogen_perc\&quot;: 1, \&quot;predefined_nitrogen_perc\&quot;: \&quot;0.88\&quot;, \&quot;maximal_nitrogen_perc\&quot;: 5, \&quot;minimal_phoshorus_perc\&quot;: 1, \&quot;predefined_phosphorus_perc\&quot;: \&quot;1.13\&quot;, \&quot;maximal_phosphorus_perc\&quot;: 7, \&quot;minimal_transp_water_perc\&quot;: 0, \&quot;predefined_transp_water_perc\&quot;: \&quot;100.00\&quot;, \&quot;maximal_transp_water_perc\&quot;: 100}}]&quot;,&quot;name&quot;:&quot;Channel&quot;,&quot;funcost&quot;:&quot;[]&quot;}" style="CHANNEL" parent="1" source="5" target="7" edge="1">
    <mxGeometry relative="1" as="geometry" />
  </mxCell>
  <Symbol name="Camara de Quiebre" label="Break chamber (9)" externalData="false" varcost="[&quot;Q_9&quot;,&quot;CSed_9&quot;,&quot;CN_9&quot;,&quot;CP_9&quot;,&quot;WSed_9&quot;,&quot;WN_9&quot;,&quot;WP_9&quot;,&quot;WSed_ret_9&quot;,&quot;WN_ret_9&quot;,&quot;WP_ret_9&quot;]" resultdb="[{&quot;model&quot;: &quot;waterproof_intake.processefficiencies&quot;, &quot;pk&quot;: 6, &quot;fields&quot;: {&quot;name&quot;: &quot;Captaci\u00f3n&quot;, &quot;unitary_process&quot;: &quot;C\u00e1mara De Quiebre&quot;, &quot;symbol&quot;: &quot;CQ&quot;, &quot;categorys&quot;: &quot;C\u00e1mara de quiebre&quot;, &quot;normalized_category&quot;: &quot;CAMARADEQUIEBRE&quot;, &quot;id_wb&quot;: 0, &quot;minimal_sediment_perc&quot;: 1, &quot;predefined_sediment_perc&quot;: &quot;2.00&quot;, &quot;maximal_sediment_perc&quot;: 3, &quot;minimal_nitrogen_perc&quot;: 1, &quot;predefined_nitrogen_perc&quot;: &quot;0.88&quot;, &quot;maximal_nitrogen_perc&quot;: 3, &quot;minimal_phoshorus_perc&quot;: 1, &quot;predefined_phosphorus_perc&quot;: &quot;1.13&quot;, &quot;maximal_phosphorus_perc&quot;: 3, &quot;minimal_transp_water_perc&quot;: 0, &quot;predefined_transp_water_perc&quot;: &quot;100.00&quot;, &quot;maximal_transp_water_perc&quot;: 100}}]" funcost="[{&quot;model&quot;: &quot;waterproof_intake.costfunctionsprocess&quot;, &quot;pk&quot;: 10601, &quot;fields&quot;: {&quot;symbol&quot;: &quot;CQ&quot;, &quot;categorys&quot;: &quot;C\u00e1mara de quiebre&quot;, &quot;energy&quot;: &quot;3.0000&quot;, &quot;labour&quot;: &quot;89.0000&quot;, &quot;mater_equipment&quot;: &quot;8.0000&quot;, &quot;function_value&quot;: &quot;((164.98*text(Q)) + 10264)*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))&quot;, &quot;function_name&quot;: &quot;C\u00e1mara de quiebre&quot;, &quot;function_description&quot;: null}}]" id="9">
    <mxCell style="camaraquiebre" parent="1" vertex="1" dbreference="CAMARADEQUIEBRE" funcionreference="CQ">
      <mxGeometry x="580" y="220" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <mxCell id="10" value="{&quot;connectorType&quot;:&quot;PL&quot;,&quot;varcost&quot;:[&quot;Q_10&quot;,&quot;CSed_10&quot;,&quot;CN_10&quot;,&quot;CP_10&quot;,&quot;WSed_10&quot;,&quot;WN_10&quot;,&quot;WP_10&quot;,&quot;WSed_ret_10&quot;,&quot;WN_ret_10&quot;,&quot;WP_ret_10&quot;],&quot;external&quot;:false,&quot;resultdb&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.processefficiencies\&quot;, \&quot;pk\&quot;: 7, \&quot;fields\&quot;: {\&quot;name\&quot;: \&quot;Captaci\\u00f3n\&quot;, \&quot;unitary_process\&quot;: \&quot;Pipeline\&quot;, \&quot;symbol\&quot;: \&quot;P\&quot;, \&quot;categorys\&quot;: \&quot;Pipeline\&quot;, \&quot;normalized_category\&quot;: \&quot;PIPELINE\&quot;, \&quot;id_wb\&quot;: 0, \&quot;minimal_sediment_perc\&quot;: 0, \&quot;predefined_sediment_perc\&quot;: \&quot;0.50\&quot;, \&quot;maximal_sediment_perc\&quot;: 2, \&quot;minimal_nitrogen_perc\&quot;: 0, \&quot;predefined_nitrogen_perc\&quot;: \&quot;0.22\&quot;, \&quot;maximal_nitrogen_perc\&quot;: 2, \&quot;minimal_phoshorus_perc\&quot;: 0, \&quot;predefined_phosphorus_perc\&quot;: \&quot;0.28\&quot;, \&quot;maximal_phosphorus_perc\&quot;: 2, \&quot;minimal_transp_water_perc\&quot;: 0, \&quot;predefined_transp_water_perc\&quot;: \&quot;100.00\&quot;, \&quot;maximal_transp_water_perc\&quot;: 100}}]&quot;,&quot;name&quot;:&quot;Pipeline&quot;,&quot;funcost&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.costfunctionsprocess\&quot;, \&quot;pk\&quot;: 10701, \&quot;fields\&quot;: {\&quot;symbol\&quot;: \&quot;T\&quot;, \&quot;categorys\&quot;: \&quot;Tuber\\u00eda\&quot;, \&quot;energy\&quot;: \&quot;20.0000\&quot;, \&quot;labour\&quot;: \&quot;60.0000\&quot;, \&quot;mater_equipment\&quot;: \&quot;20.0000\&quot;, \&quot;function_value\&quot;: \&quot;(0.01861*((0.763*text(Q))+(8.402*RAIZ(text(Q)))))*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))\&quot;, \&quot;function_name\&quot;: \&quot;Tuber\\u00eda\&quot;, \&quot;function_description\&quot;: null}}]&quot;}" style="PIPELINE" parent="1" source="7" target="9" edge="1">
    <mxGeometry relative="1" as="geometry" />
  </mxCell>
  <Symbol name="CSINFRA" label="CS Infra (11)" externalData="false" varcost="[&quot;Q_11&quot;,&quot;CSed_11&quot;,&quot;CN_11&quot;,&quot;CP_11&quot;,&quot;WSed_11&quot;,&quot;WN_11&quot;,&quot;WP_11&quot;,&quot;WSed_ret_11&quot;,&quot;WN_ret_11&quot;,&quot;WP_ret_11&quot;]" funcost="[]" resultdb="[{&quot;model&quot;: &quot;waterproof_intake.processefficiencies&quot;, &quot;pk&quot;: 33, &quot;fields&quot;: {&quot;name&quot;: &quot;Captaci\u00f3n&quot;, &quot;unitary_process&quot;: &quot;Case Study Infrastructure&quot;, &quot;symbol&quot;: &quot;CS&quot;, &quot;categorys&quot;: &quot;Case Study Infrastructure&quot;, &quot;normalized_category&quot;: &quot;CSINFRA&quot;, &quot;id_wb&quot;: 0, &quot;minimal_sediment_perc&quot;: 0, &quot;predefined_sediment_perc&quot;: &quot;13.00&quot;, &quot;maximal_sediment_perc&quot;: 99, &quot;minimal_nitrogen_perc&quot;: 0, &quot;predefined_nitrogen_perc&quot;: &quot;15.00&quot;, &quot;maximal_nitrogen_perc&quot;: 25, &quot;minimal_phoshorus_perc&quot;: 0, &quot;predefined_phosphorus_perc&quot;: &quot;18.00&quot;, &quot;maximal_phosphorus_perc&quot;: 80, &quot;minimal_transp_water_perc&quot;: 0, &quot;predefined_transp_water_perc&quot;: &quot;100.00&quot;, &quot;maximal_transp_water_perc&quot;: 100}}]" id="11">
    <mxCell style="csinfra" parent="1" vertex="1" dbreference="CSINFRA" funcionreference="CS">
      <mxGeometry x="590" y="380" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <mxCell id="12" value="{&quot;connectorType&quot;:&quot;CH&quot;,&quot;varcost&quot;:[&quot;Q_12&quot;,&quot;CSed_12&quot;,&quot;CN_12&quot;,&quot;CP_12&quot;,&quot;WSed_12&quot;,&quot;WN_12&quot;,&quot;WP_12&quot;,&quot;WSed_ret_12&quot;,&quot;WN_ret_12&quot;,&quot;WP_ret_12&quot;],&quot;external&quot;:false,&quot;resultdb&quot;:&quot;[{\&quot;model\&quot;: \&quot;waterproof_intake.processefficiencies\&quot;, \&quot;pk\&quot;: 8, \&quot;fields\&quot;: {\&quot;name\&quot;: \&quot;Captaci\\u00f3n\&quot;, \&quot;unitary_process\&quot;: \&quot;Canal\&quot;, \&quot;symbol\&quot;: \&quot;C\&quot;, \&quot;categorys\&quot;: \&quot;Canal\&quot;, \&quot;normalized_category\&quot;: \&quot;CHANNEL\&quot;, \&quot;id_wb\&quot;: 0, \&quot;minimal_sediment_perc\&quot;: 1, \&quot;predefined_sediment_perc\&quot;: \&quot;2.00\&quot;, \&quot;maximal_sediment_perc\&quot;: 7, \&quot;minimal_nitrogen_perc\&quot;: 1, \&quot;predefined_nitrogen_perc\&quot;: \&quot;0.88\&quot;, \&quot;maximal_nitrogen_perc\&quot;: 5, \&quot;minimal_phoshorus_perc\&quot;: 1, \&quot;predefined_phosphorus_perc\&quot;: \&quot;1.13\&quot;, \&quot;maximal_phosphorus_perc\&quot;: 7, \&quot;minimal_transp_water_perc\&quot;: 0, \&quot;predefined_transp_water_perc\&quot;: \&quot;100.00\&quot;, \&quot;maximal_transp_water_perc\&quot;: 100}}]&quot;,&quot;name&quot;:&quot;Channel&quot;,&quot;funcost&quot;:&quot;[]&quot;}" style="CHANNEL" parent="1" source="9" target="11" edge="1">
    <mxGeometry relative="1" as="geometry" />
  </mxCell>
  <Symbol name="External Input" label="External Input (13)" externalData="true" varcost="[&quot;Q13&quot;,&quot;CSed13&quot;,&quot;CN13&quot;,&quot;CP13&quot;,&quot;WSed13&quot;,&quot;WN13&quot;,&quot;WP13&quot;,&quot;WSedRet13&quot;,&quot;WNRet13&quot;,&quot;WPRet13&quot;]" funcost="[]" resultdb="[{&quot;model&quot;: &quot;waterproof_intake.processefficiencies&quot;, &quot;pk&quot;: 32, &quot;fields&quot;: {&quot;name&quot;: &quot;Captaci\u00f3n&quot;, &quot;unitary_process&quot;: &quot;External input&quot;, &quot;symbol&quot;: &quot;EI&quot;, &quot;categorys&quot;: &quot;External input&quot;, &quot;normalized_category&quot;: &quot;ENTRADAEXTERNA&quot;, &quot;id_wb&quot;: 0, &quot;minimal_sediment_perc&quot;: 0, &quot;predefined_sediment_perc&quot;: &quot;11.00&quot;, &quot;maximal_sediment_perc&quot;: 99, &quot;minimal_nitrogen_perc&quot;: 0, &quot;predefined_nitrogen_perc&quot;: &quot;7.00&quot;, &quot;maximal_nitrogen_perc&quot;: 25, &quot;minimal_phoshorus_perc&quot;: 0, &quot;predefined_phosphorus_perc&quot;: &quot;17.00&quot;, &quot;maximal_phosphorus_perc&quot;: 80, &quot;minimal_transp_water_perc&quot;: 0, &quot;predefined_transp_water_perc&quot;: &quot;100.00&quot;, &quot;maximal_transp_water_perc&quot;: 100}}]" id="13">
    <mxCell style="externalinput" vertex="1" dbreference="ENTRADAEXTERNA" funcionreference="EX" parent="1">
      <mxGeometry x="440" y="210" width="60" height="92" as="geometry" />
    </mxCell>
  </Symbol>
  <mxCell id="14" value="{&quot;connectorType&quot;:&quot;CH&quot;,&quot;varcost&quot;:[&quot;Q14&quot;,&quot;CSed14&quot;,&quot;CN14&quot;,&quot;CP14&quot;,&quot;WSed14&quot;,&quot;WN14&quot;,&quot;WP14&quot;,&quot;WSedRet14&quot;,&quot;WNRet14&quot;,&quot;WPRet14&quot;],&quot;external&quot;:false,&quot;resultdb&quot;:[{&quot;model&quot;:&quot;waterproof_intake.processefficiencies&quot;,&quot;pk&quot;:8,&quot;fields&quot;:{&quot;name&quot;:&quot;Captación&quot;,&quot;unitary_process&quot;:&quot;Canal&quot;,&quot;symbol&quot;:&quot;C&quot;,&quot;categorys&quot;:&quot;Canal&quot;,&quot;normalized_category&quot;:&quot;CHANNEL&quot;,&quot;id_wb&quot;:0,&quot;minimal_sediment_perc&quot;:1,&quot;predefined_sediment_perc&quot;:&quot;2.00&quot;,&quot;maximal_sediment_perc&quot;:7,&quot;minimal_nitrogen_perc&quot;:1,&quot;predefined_nitrogen_perc&quot;:&quot;0.88&quot;,&quot;maximal_nitrogen_perc&quot;:5,&quot;minimal_phoshorus_perc&quot;:1,&quot;predefined_phosphorus_perc&quot;:&quot;1.13&quot;,&quot;maximal_phosphorus_perc&quot;:7,&quot;minimal_transp_water_perc&quot;:0,&quot;predefined_transp_water_perc&quot;:&quot;100.00&quot;,&quot;maximal_transp_water_perc&quot;:100}}],&quot;name&quot;:&quot;Channel&quot;,&quot;funcost&quot;:[]}" style="CHANNEL" edge="1" parent="1" source="13" target="9">
    <mxGeometry relative="1" as="geometry" />
  </mxCell>
</root>
</mxGraphModel>
`;
// Program starts here. The document.onLoad executes the
// createEditor function with a given configuration.
// In the config file, the mxEditor.onInit method is
// overridden to invoke this global function as the
// last step in the editor constructor.
function onInit(editor) {
    // Enables rotation handle
    mxVertexHandler.prototype.rotationEnabled = false;

    // Enables guides
    mxGraphHandler.prototype.guidesEnabled = false;

    // Alt disables guides
    mxGuide.prototype.isEnabledForEvent = function(evt) {
        return !mxEvent.isAltDown(evt);
    };

    // Enables snapping waypoints to terminals
    mxEdgeHandler.prototype.snapToTerminals = true;

    // Defines an icon for creating new connections in the connection handler.
    // This will automatically disable the highlighting of the source vertex.
    mxConnectionHandler.prototype.connectImage = new mxImage('/static/mxgraph/images/connector.gif', 16, 16);

    // Enables connections in the graph and disables
    // reset of zoom and translate on root change
    // (ie. switch between XML and graphical mode).
    editor.graph.setConnectable(true);

    // Clones the source if new connection has no target
    //editor.graph.connectionHandler.setCreateTarget(true);

    var style = editor.graph.getStylesheet().getDefaultEdgeStyle();
    style[mxConstants.STYLE_ROUNDED] = true;
    style[mxConstants.STYLE_EDGE] = mxEdgeStyle.ElbowConnector;
    style[mxConstants.STYLE_STROKEWIDTH] = 4;
    style[mxConstants.STYLE_STROKECOLOR] = "#ff0000";
    style[mxConstants.STYLE_FONTSIZE] = '11';
    style[mxConstants.STYLE_ALIGN] = mxConstants.ALIGN_CENTER;
    style[mxConstants.STYLE_VERTICAL_ALIGN] = mxConstants.ALIGN_BOTTOM;


    // Installs a popupmenu handler using local function (see below).
    editor.graph.popupMenuHandler.factoryMethod = function(menu, cell, evt) {
        return createPopupMenu(editor.graph, menu, cell, evt);
    };

    // Removes cells when [DELETE] is pressed
    // elements with id == 2 is River and id==3 is CSINFRA can't remove
    var keyHandler = new mxKeyHandler(editor.graph);
    keyHandler.bindKey(46, function(evt) {
        deleteWithValidations(editor);
    });

    editor.graph.setAllowDanglingEdges(false);
    editor.graph.setMultigraph(false);

    var listener = function(sender, evt) {
        editor.graph.validateGraph();
    };

    editor.graph.getLabel = function(cell) {
        var label = (this.labelsVisible) ? this.convertValueToString(cell) : '';
        var geometry = this.model.getGeometry(cell);

        if (geometry != null && geometry.width == 0) {
            var style = this.getCellStyle(cell);
            var fontSize = style[mxConstants.STYLE_FONTSIZE] || mxConstants.DEFAULT_FONTSIZE;
        }
        if (label == undefined) {
            label = "This connection doesn't have a defined type, \n please define a type";
            if (typeof(cell.value) == "string" && cell.value.length > 0) {
                try {
                    let obj = JSON.parse(cell.value);
                    label = connectionsType[obj.connectorType].name + " (" + cell.id + ")";
                } catch (e) {
                    label = "";
                }
            }
        }
        return label;
    };

    editor.graph.addListener(mxEvent.CELLS_ADDED, function(sender, evt) {
        //return;

        let cell = evt.properties.cells[0];
        if (cell.value != undefined && typeof(cell.value) == "object") {
            let lbl = cell.getAttribute("label");
            cell.setAttribute("label", lbl + " (" + cell.id + ")");
            editor.graph.model.setValue(cell, cell.value);
        }
    });

    editor.graph.getModel().addListener(mxEvent.CHANGE, listener);

    // Updates the title if the root changes
    var title = document.getElementById('title');

    if (title != null) {
        var f = function(sender) {
            title.innerHTML = sender.getTitle();
        };

        editor.addListener(mxEvent.ROOT, f);
        f(editor);
    }

    // Defines a new action to switch between
    // XML and graphical display
    var textNode = document.getElementById('xml');
    var graphNode = editor.graph.container;
    var parent = editor.graph.getDefaultParent();
    var xmlDocument = mxUtils.createXmlDocument();
    var sourceNode = xmlDocument.createElement('Symbol');

    //Create River at the beginning of the diagram
    var river = editor.graph.insertVertex(parent, null, sourceNode, 40, 30, 60, 92);
    river.setAttribute('name', 'River');
    river.setAttribute('label', 'River (2)');
    river.setAttribute('externalData', 'false');
    editor.graph.model.setStyle(river, 'rio');
    var temp = [];
    temp.push(
        `Q${river.id}`,
        `CSed${river.id}`,
        `CN${river.id}`,
        `CP${river.id}`,
        `WSed${river.id}`,
        `WN${river.id}`,
        `WP${river.id}`,
        `WSedRet${river.id}`,
        `WNRet${river.id}`,
        `WPRet${river.id}`
    );

    $.ajax({
        url: `/intake/loadProcess/RIVER`,
        success: function(result) {
            river.setAttribute('varcost', JSON.stringify(temp));
            river.setAttribute('resultdb', result);
        }
    });

    // River not have a entrance connection
    editor.graph.multiplicities.push(new mxMultiplicity(
        false, 'Symbol', 'name', 'River', 0, 0, ['Symbol'],
        `No element can be connected to the River`));

    // External input not have a entrance connection
    editor.graph.multiplicities.push(new mxMultiplicity(
        false, 'Symbol', 'name', 'External Input', 0, 0, ['Symbol'],
        `No element can be connected to the External input`));

    // External input needs 1 connected Targets
    editor.graph.multiplicities.push(new mxMultiplicity(
        true, 'Symbol', 'name', 'External Input', 0, 1, ['Symbol'],
        'External Input only have 1 target',
        'Source Must Connect to Target'));

    // Source nodes needs 1 connected Targets
    editor.graph.multiplicities.push(new mxMultiplicity(
        true, 'Symbol', 'name', 'River', 0, 1, ['Symbol'],
        'River only have 1 target',
        'Source Must Connect to Target'));

    // Target needs exactly one incoming connection from Source
    editor.graph.multiplicities.push(new mxMultiplicity(
        true, 'Symbol', 'name', 'CSINFRA', 0, 0, ['Symbol'],
        `From element CSINFRA can't connect to other element`,
        'Target Must Connect From Source'));

    var getdata = document.getElementById('getdata');
    getdata.checked = false;

    var funct = function(editor) {
        if (getdata.checked) {
            graphNode.style.display = 'none';
            textNode.style.display = 'inline';

            var enc = new mxCodec();
            var node = enc.encode(editor.graph.getModel());

            textNode.value = mxUtils.getPrettyXml(node);
            textNode.originalValue = textNode.value;
            textNode.focus();
        } else {
            graphNode.style.display = '';

            if (textNode.value != textNode.originalValue) {
                var doc = mxUtils.parseXml(textNode.value);
                var dec = new mxCodec(doc);
                dec.decode(doc.documentElement, editor.graph.getModel());
            }
            textNode.originalValue = null;
            // Makes sure nothing is selected in IE
            if (mxClient.IS_IE) {
                mxUtils.clearSelection();
            }

            textNode.style.display = 'none';

            // Moves the focus back to the graph
            editor.graph.container.focus();
        }
    };

    editor.addAction('switchView', funct);

    // Defines a new action to switch between
    // XML and graphical display
    mxEvent.addListener(getdata, 'click', function() {
        editor.execute('switchView');
    });

    // Create select actions in page
    //var node = document.getElementById('mainActions');
    var buttons = ['group', 'ungroup', 'cut', 'copy', 'paste', 'delete', 'undo', 'redo', 'print', 'show'];

    // Only adds image and SVG export if backend is available
    // NOTE: The old image export in mxEditor is not used, the urlImage is used for the new export.
    if (editor.urlImage != null) {
        // Client-side code for image export
        var exportImage = function(editor) {
            var graph = editor.graph;
            var scale = graph.view.scale;
            var bounds = graph.getGraphBounds();

            // New image export
            var xmlDoc = mxUtils.createXmlDocument();
            var root = xmlDoc.createElement('output');
            xmlDoc.appendChild(root);

            // Renders graph. Offset will be multiplied with state's scale when painting state.
            var xmlCanvas = new mxXmlCanvas2D(root);
            xmlCanvas.translate(Math.floor(1 / scale - bounds.x), Math.floor(1 / scale - bounds.y));
            xmlCanvas.scale(scale);

            var imgExport = new mxImageExport();
            imgExport.drawState(graph.getView().getState(graph.model.root), xmlCanvas);

            // Puts request data together
            var w = Math.ceil(bounds.width * scale + 2);
            var h = Math.ceil(bounds.height * scale + 2);
            var xml = mxUtils.getXml(root);

            // Requests image if request is valid
            if (w > 0 && h > 0) {
                var name = 'export.png';
                var format = 'png';
                var bg = '&bg=#FFFFFF';

                new mxXmlRequest(editor.urlImage, 'filename=' + name + '&format=' + format +
                    bg + '&w=' + w + '&h=' + h + '&xml=' + encodeURIComponent(xml)).
                simulate(document, '_blank');
            }
        };

        editor.addAction('exportImage', exportImage);

        // Client-side code for SVG export
        var exportSvg = function(editor) {
            var graph = editor.graph;
            var scale = graph.view.scale;
            var bounds = graph.getGraphBounds();

            // Prepares SVG document that holds the output
            var svgDoc = mxUtils.createXmlDocument();
            var root = (svgDoc.createElementNS != null) ?
                svgDoc.createElementNS(mxConstants.NS_SVG, 'svg') : svgDoc.createElement('svg');

            if (root.style != null) {
                root.style.backgroundColor = '#FFFFFF';
            } else {
                root.setAttribute('style', 'background-color:#FFFFFF');
            }

            if (svgDoc.createElementNS == null) {
                root.setAttribute('xmlns', mxConstants.NS_SVG);
            }

            root.setAttribute('width', Math.ceil(bounds.width * scale + 2) + 'px');
            root.setAttribute('height', Math.ceil(bounds.height * scale + 2) + 'px');
            root.setAttribute('xmlns:xlink', mxConstants.NS_XLINK);
            root.setAttribute('version', '1.1');

            // Adds group for anti-aliasing via transform
            var group = (svgDoc.createElementNS != null) ?
                svgDoc.createElementNS(mxConstants.NS_SVG, 'g') : svgDoc.createElement('g');
            group.setAttribute('transform', 'translate(0.5,0.5)');
            root.appendChild(group);
            svgDoc.appendChild(root);

            // Renders graph. Offset will be multiplied with state's scale when painting state.
            var svgCanvas = new mxSvgCanvas2D(group);
            svgCanvas.translate(Math.floor(1 / scale - bounds.x), Math.floor(1 / scale - bounds.y));
            svgCanvas.scale(scale);

            var imgExport = new mxImageExport();
            imgExport.drawState(graph.getView().getState(graph.model.root), svgCanvas);

            var name = 'export.svg';
            var xml = encodeURIComponent(mxUtils.getXml(root));

            new mxXmlRequest(editor.urlEcho, 'filename=' + name + '&format=svg' + '&xml=' + xml).simulate(document, "_blank");
        };

        editor.addAction('exportSvg', exportSvg);

        buttons.push('exportImage');
        buttons.push('exportSvg');
    };

    for (var i = 0; i < buttons.length; i++) {
        var button = document.createElement('button');
        mxUtils.write(button, mxResources.get(buttons[i]));

        var factory = function(name) {
            return function() {
                editor.execute(name);
            };
        };

        mxEvent.addListener(button, 'click', factory(buttons[i]));
        //node.appendChild(button);
    }

    //use jquery
    $(document).ready(function() {

        var MQ = MathQuill.getInterface(2);
        var CostSelected = null;
        var mathFieldSpan = document.getElementById('math-field');
        var latexSpan = document.getElementById('latex');
        var mathField = MQ.MathField(mathFieldSpan, {
            spaceBehavesLikeTab: true,
            handlers: {
                edit: function() {
                    latexSpan.textContent = mathField.latex();
                }
            }
        });

        //load data when add an object in a diagram
        editor.graph.addListener(mxEvent.ADD_CELLS, function(sender, evt) {

            var selectedCell = evt.getProperty("cells");
            var idvar = selectedCell[0].id;
            if (selectedCell != undefined) {
                var varcost = [];
                varcost.push(
                    `Q${idvar}`,
                    `CSed${idvar}`,
                    `CN${idvar}`,
                    `CP${idvar}`,
                    `WSed${idvar}`,
                    `WN${idvar}`,
                    `WP${idvar}`,
                    `WSedRet${idvar}`,
                    `WNRet${idvar}`,
                    `WPRet${idvar}`
                );
                selectedCell[0].setAttribute('varcost', JSON.stringify(varcost));

                $.ajax({
                    url: `/intake/loadProcess/${selectedCell[0].dbreference}`,
                    success: function(result) {
                        selectedCell[0].setAttribute("resultdb", result);
                    }
                });

                $.ajax({
                    url: `/intake/loadFunctionBySymbol/${selectedCell[0].funcionreference}`,
                    success: function(result) {
                        selectedCell[0].setAttribute("funcost", result);
                    }
                });
            }
        });

        //Load data from figure to html
        editor.graph.addListener(mxEvent.CLICK, function(sender, evt) {
            selectedCell = evt.getProperty('cell');
            // Clear Inputs
            if (selectedCell != undefined) clearDataHtml(selectedCell, evt);
            if (selectedCell != undefined) { addData(selectedCell, MQ); } else { clearDataHtml(selectedCell, evt); }
        });

        //Button for valide graph
        $('#saveGraph').click(function() {
            validateGraphIntake();
        });

        function validateGraphIntake() {
            graphData = [];
            connection = [];
            var enc = new mxCodec();
            var node = enc.encode(editor.graph.getModel());
            var textxml = mxUtils.getPrettyXml(node);
            bandera = validations(node, editor.graph.getModel());
            if (!bandera) {
                $('#hideCostFuntion').show();
                node.querySelectorAll('Symbol').forEach(function(node) {
                    graphData.push({
                        'id': node.id,
                        "name": node.getAttribute('name'),
                        'resultdb': node.getAttribute('resultdb'),
                        'varcost': node.getAttribute('varcost'),
                        'funcost': node.getAttribute('funcost'),
                        'external': node.getAttribute('externalData'),
                        'externaldata': []
                    })
                });

                let temp = [];
                node.querySelectorAll('mxCell').forEach(function(node) {
                    if (node.id != "") {
                        let value = Object.values(JSON.parse(node.getAttribute('value')));
                        graphData.push({
                            'id': node.id,
                            'source': node.getAttribute('source'),
                            'target': node.getAttribute('target'),
                            'resultdb': value[3],
                            'funcost': value[5],
                            'name': JSON.stringify(value[4]),
                            'varcost': JSON.stringify(value[1])
                        });
                        temp.push({
                            'id': node.id,
                            'source': node.getAttribute('source'),
                            'target': node.getAttribute('target'),
                        })
                    }
                });

                for (let index = 0; index < temp.length; index++) {
                    connection.push({
                        "source": temp[index].source,
                        "target": temp[index].id
                    })
                    connection.push({
                        "source": temp[index].id,
                        "target": temp[index].target
                    })
                }
                $('#graphConnections').val(JSON.stringify(connection));
                $('#xmlGraph').val(textxml);
                $('#graphElements').val(JSON.stringify(graphData));
            }


        }

        //Set var into calculator
        $(document).on('click', '.list-group-item', function() {
            addInfo(`\\mathit{${$(this).attr('value')}}`);
        });


        $('#saveAndValideCost').click(function() {
            funcostdb[CostSelected].fields.function_value = mathField.latex();
            selectedCell.setAttribute('funcost', JSON.stringify(funcostdb));
            $('#funcostgenerate div').remove();
            for (let index = 0; index < funcostdb.length; index++) {
                funcost(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);
            }
            $('#CalculatorModal').modal('hide');
            validateGraphIntake();
        });

        $('button[name=mathKeyBoard]').each(function() {
            MQ.StaticMath(this);
        });

        //Edit funcion cost 
        $(document).on('click', 'a[name=glyphicon-edit]', function() {
            mathField.clearSelection();
            $('#CalculatorModal').modal('show');
            CostSelected = $(this).attr('idvalue');
            setVarCost();
            let value = funcostdb[CostSelected].fields.function_value;
            mathField.latex(value);
            mathField.focus();
        });

        //Delete funcion cost 
        $(document).on('click', 'a[name=glyphicon-trash]', function() {
            Swal.fire({
                title: 'Are you sure?',
                text: "You won't be able to revert this!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, delete it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    var id = $(this).attr('idvalue');
                    $(`#funcostgenerate div[idvalue = 'fun_${id}']`).remove();
                    if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                        var obj = JSON.parse(selectedCell.value);
                        let dbfields = JSON.parse(obj.funcost);
                        dbfields.splice(id, 1);
                        obj.funcost = JSON.stringify(dbfields);
                        selectedCell.setValue(JSON.stringify(obj));
                        $('#funcostgenerate div').remove();
                        for (let index = 0; index < funcostdb.length; index++) {
                            funcost(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);
                        }
                    } else {
                        funcostdb.splice(id, 1);
                        selectedCell.setAttribute('funcost', JSON.stringify(funcostdb));
                        $('#funcostgenerate div').remove();
                        for (let index = 0; index < funcostdb.length; index++) {
                            funcost(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);
                        }
                    }

                    Swal.fire(
                        'Deleted!',
                        'Your funcion has been deleted.',
                        'success'
                    )
                }
            })
        });

        function setVarCost() {
            $('#VarCostListGroup div').remove();
            for (const index of graphData) {
                var costlabel = "";
                for (const iterator of JSON.parse(index.varcost)) {
                    costlabel += `<a value="${iterator}" class="list-group-item list-group-item-action" style="padding-top: 4px;padding-bottom: 4px;">${iterator}</a>`
                }
                $('#VarCostListGroup').append(`
                    <div class="panel panel-info">
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <a data-toggle="collapse" data-parent="#VarCostListGroup" href="#VarCostListGroup_${index.id}">${index.id} - ${index.name}</a>
                            </h4>
                        </div>
                        <div id="VarCostListGroup_${index.id}" class="panel-collapse collapse">
                            ${costlabel}
                        </div>
                    </div>
                `);
            }
        }

        $('#ModalAddCostBtn').click(function() {
            $('#VarCostListGroup div').remove();
            for (const index of graphData) {
                var costlabel = "";
                for (const iterator of JSON.parse(index.varcost)) {
                    costlabel += `<a value="${iterator}" class="list-group-item list-group-item-action" style="padding-top: 4px;padding-bottom: 4px;">${iterator}</a>`
                }
                $('#VarCostListGroup').append(`
                <div class="panel panel-info">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#VarCostListGroup" href="#VarCostListGroup_${index.id}">${index.id} - ${index.name}</a>
                        </h4>
                    </div>
                    <div id="VarCostListGroup_${index.id}" class="panel-collapse collapse">
                        ${costlabel}
                    </div>
                </div>
                `);
            }
        });

        //KeyBoard calculator funcion cost
        $('button[name=mathKeyBoard]').click(function() {
            addInfo($(this).attr('value'));
        });

        //Add value entered in sediments in the field resultdb
        $('#sedimentosDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_sediment_perc = $('#sedimentosDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_sediment_perc = $('#sedimentosDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }

        });

        //Add value entered in nitrogen in the field resultdb
        $('#nitrogenoDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_nitrogen_perc = $('#nitrogenoDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_nitrogen_perc = $('#nitrogenoDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }
        });

        //Add value entered in phosphorus in the field resultdb
        $('#fosforoDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_phosphorus_perc = $('#fosforoDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_phosphorus_perc = $('#fosforoDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }
        });

        //Add value entered in aguaDiagram in the field resultdb
        $('#aguaDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_transp_water_perc = $('#aguaDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_transp_water_perc = $('#aguaDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }
            validationTransportedWater(editor, selectedCell);
        });



        jQuery.fn.ForceNumericOnly = function() {
            return this.each(function() {
                $(this).keydown(function(e) {
                    var key = e.charCode || e.keyCode || 0;
                    return (
                        key == 8 ||
                        key == 9 ||
                        key == 13 ||
                        key == 46 ||
                        key == 110 ||
                        key == 190 ||
                        (key >= 35 && key <= 40) ||
                        (key >= 48 && key <= 57) ||
                        (key >= 96 && key <= 105));
                });
            });
        };
        //Force only numbers into calculator funcion cost
        $("#math-field").ForceNumericOnly();
        //Append values and var into funcion cost
        function addInfo(value) {
            mathField.cmd(value);
            mathField.focus();
        }

    });

}