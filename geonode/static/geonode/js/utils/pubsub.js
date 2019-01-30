import PubSub from "pubsub-js";

/*
  Wrapper for pubsub library being used on project.
*/

export default {
  publish(data) {
    PubSub.publish(data);
  },
  subscribe(event, callback) {
    PubSub.subscribe(event, callback);
  }
};
