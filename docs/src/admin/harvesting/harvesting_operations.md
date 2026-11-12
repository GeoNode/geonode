# Harvester operations

Each GeoNode harvester is able to perform a finite set of operations. These can be performed either:

1. In an **automated fashion**, being dispatched by the [harvesting scheduler](gnode_harvesting_concepts.md#harvesting-scheduler). Automated harvesting is only performed when the corresponding harvester has `scheduling_enabled=True`
2. **On-demand**, by explicit request of the user. On-demand execution can be requested in one of two ways:

    1. By selecting the relevant harvester or harvesters in the `Harvesting -> Harvesters` section of the GeoNode admin area and then selecting and running an action from the drop-down menu
    2. By interacting with the GeoNode REST API. Harvester actions are requested by issuing `HTTP PATCH` requests to the `/api/v2/harvesters/{harvester-id}/` endpoint. The payload of such requests must specify the corresponding status. For example, by issuing a request like:

        ```bash
        curl -X PATCH http://localhost/api/v2/harvesters/1/ \
          -H "Content-Type: application/json" \
          -u "myuser:mypass" \
          --data '{"status": "updating-harvestable-resources"}'
        ```

        We are asking that the harvester status be changed to `updating-harvestable-resources`. If the server accepts this request, then the update list of harvestable resources operation is triggered.

        !!! Note
            The server will not accept the API request if the harvester current status is not `ready`.

While performing an action, the harvester `status` property transitions from `ready` to whatever action-related status is appropriate, as indicated below. As the operation finishes execution, the harvester status transitions back to `ready`. If the harvester has any status other than `ready`, then it is currently busy. When a harvester is busy it cannot execute other operations, you need to wait until the current operation finishes.

## Check if the remote service is available operation

This operation causes the harvester to perform a simple health check on the remote service, in order to check whether it responds successfully. The response is stored in the harvester `remote_available` property. This operation is performed in the same process as the main GeoNode, that is, it runs synchronously.

When triggered, this operation causes the harvester status to transition to `checking-availability`. As the operation finishes, the harvester status transitions back to `ready`.

Invocation via the GeoNode admin is performed by selecting the `Check availability of selected harvesters` command.

Invocation via the GeoNode REST API is performed by issuing an HTTP PATCH request with a payload that sets the harvester status.

## Update the list of harvestable resources operation

This operation causes the harvester to interact with the remote service in order to discover which resources are available for being harvested. Existing remote resources are then saved as harvestable resources.

Since this operation can potentially take a long time to complete, as we do not know how many resources may exist on the remote service, it is run using a background process. GeoNode creates a new [refresh session](gnode_harvesting_concepts.md#refresh-session) and uses it to track the progress of this operation.

When triggered, this operation causes the harvester status to transition to `updating-harvestable-resources`. As the operation finishes, the harvester status transitions back to `ready`.

Invocation via the GeoNode admin is performed by selecting the `Update harvestable resources for selected harvesters` command.

Invocation via the GeoNode REST API is performed by issuing an HTTP PATCH request with a payload that sets the harvester status.

## Perform harvesting operation

This operation causes the harvester to check which harvestable resources are currently marked as being harvestable and then, for each one, harvest the resource from the remote server.

Since this operation can potentially take a long time to complete, as we do not know how many resources may exist on the remote service, it is run using a background process. GeoNode creates a new [harvesting session](gnode_harvesting_concepts.md#harvesting-session) and uses it to track the progress of this operation.

When triggered, this operation causes the harvester status to transition to `harvesting-resources`. As the operation finishes, the harvester status transitions back to `ready`.

Invocation via the GeoNode admin is performed by selecting the `Perform harvesting on selected harvesters` command.

Invocation via the GeoNode REST API is performed by issuing an HTTP PATCH request with a payload that sets the harvester status.

## Abort update of harvestable resources operation

This operation causes the harvester to abort an ongoing update list of harvestable resources operation.

When triggered, this operation causes the harvester status to transition to `aborting-update-harvestable-resources`. As the operation finishes, the harvester status transitions back to `ready`.

Invocation via the GeoNode admin is performed by selecting the `Abort on-going update of harvestable resources for selected harvesters` command.

Invocation via the GeoNode REST API is performed by issuing an HTTP PATCH request with a payload that sets the harvester status.

## Abort harvesting operation

This operation causes the harvester to abort an ongoing perform harvesting operation.

When triggered, this operation causes the harvester status to transition to `aborting-performing-harvesting`. As the operation finishes, the harvester status transitions back to `ready`.

Invocation via the GeoNode admin is performed by selecting the `Abort on-going harvesting sessions for selected harvesters` command.

Invocation via the GeoNode REST API is performed by issuing an HTTP PATCH request with a payload that sets the harvester status.

## Reset harvester operation

This operation causes the harvester status to be reset back to `ready`. It is mainly useful for troubleshooting potential errors, in order to unlock harvesters that may get stuck in a non-actionable status when some unforeseen error occurs.

When triggered, this operation causes the harvester status to transition to `ready` immediately.

Invocation via the GeoNode admin is performed by selecting the `Reset harvester status` command.

This operation cannot be called via the GeoNode API.
