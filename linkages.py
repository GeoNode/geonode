import json
from geonode.base.models import ResourceBase

sources = [881,1016,1019,1128,1129,1130,1137,1146,1147,1161,1164,1330,1350,1352,1355,1356,1363,1364,4312,4313,4314,4315,4316,4327,4335,4336,4337,4338,4339,4340,4341,4342,4343,4344,4345,4346,4347,4348,4349,4350,4351,4352,4353,4354,4355,4356,4357,4358,4359,4360]



def get_linkages(sources, as_target=False):
	linkages = {}
	for source_id in sources:
		linked_resources = ResourceBase.objects.get(pk=source_id).get_real_instance().get_linked_resources(as_target=as_target)
		for l in linked_resources:
			us = l.target if as_target else l.source
			them = l.source if as_target else l.target
			if source_id not in linkages:
				linkages[source_id] = {
					"resource": {
						"id": source_id,
						"title": us.title,
						"type": us.resource_type,
						"owner": {
							"id": us.owner.id,
							"username": us.owner.username
						}
					},
					"linked_resources": []
				}
			
			linkages[source_id]["linked_resources"].append({
			"id":them.id, 
			"title":them.title, 
			"type":them.resource_type,
			"owner": {
				"id": them.owner.id,
				"username": them.owner.username
			}
			})
	return linkages
	

linkages_forward = get_linkages(sources)
with open("linkages_forward.json", "w") as fout:
	json.dump(linkages_forward, fout, indent=4)


linkages_backward = get_linkages(sources, True)
with open("linkages_backward.json", "w") as fout:
	json.dump(linkages_backward, fout, indent=4)