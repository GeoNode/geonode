import PubSub from "pubsub-js";

const SelectionTree = ({ id, data, eventId }) => {
  const $id = $(`#${id}`);
  $id.treeview({
    data,
    multiSelect: true,
    onNodeSelected: ($event, node) => {
      PubSub.publish(`select_${eventId}`, node);
      if (node.nodes) {
        for (let i = 0; i < node.nodes.length; i++) {
          $id.treeview("selectNode", node.nodes[i]);
        }
      }
    },
    onNodeUnselected: ($event, node) => {
      PubSub.publish(`unselect_${eventId}`, node);
      if (node.nodes) {
        for (let i = 0; i < node.nodes.length; i++) {
          $id.treeview("unselectNode", node.nodes[i]);
          $id.trigger("nodeUnselected", $.extend(true, {}, node.nodes[i]));
        }
      }
    }
  });
};

export default SelectionTree;
