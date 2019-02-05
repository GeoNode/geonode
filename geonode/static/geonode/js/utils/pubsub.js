import PubSub from "pubsub-js";

/*
  Wrapper for pubsub library being used on project.
*/

export default {
  publish(event, data) {
    PubSub.publish(event, data);
  },
  subscribe(event, callback) {
    PubSub.subscribe(event, callback);
  }
};
