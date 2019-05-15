MapStore 2 leverages a full separation of concerns between the **backend** and the **frontend**.

The frontend is a Javascript web application communicating with MapStore 2 own web services using AJAX and external ones through an internal, configurable, _proxy_.

The backend is a suite of web services, developed in Java and deployed into a J2EE container (e.g. Apache Tomcat).
![General Infrastructure](https://docs.google.com/drawings/d/1X-yA-_GQ6HqhoYQfIbuxzdt8c-9fD0K3tf1WVbXecSE/pub?w=480&h=360)

# Frontend

The frontend is based on the [ReactJS](https://facebook.github.io/react/) library and the [Redux](http://rackt.github.io/redux/) architecture, which is a specific implementation of the [Flux](http://facebook.github.io/flux/) architecture.

<img src="https://facebook.github.io/flux/img/flux-simple-f8-diagram-with-client-action-1300w.png" style="max-width:500px" alt="Flux infrastructure" />

It allows plugging different mapping libraries (with **Leaflet** and **OpenLayers 3** as our first implementation targets) abstracting libraries implementation details using ReactJS _web components_ and _actions based communication_.

![MapStore 2 - Frontend](https://docs.google.com/drawings/d/1k8Qja6ZFeOpoW3WqbZJvU3f7PvKpL-oTGq0vErQng44/pub?w=480&h=360)

## Frontend Technologies
 * [ReactJS and Redux introduction](reactjs-and-redux-introduction)

# Backend

Backend services include at least (but not only) these ones:
 * Generic, configurable, **HTTP-Proxy** to avoid CORS issues when the frontend tries to communicate with external services, based on the GeoSolutions [http-proxy](https://github.com/geosolutions-it/http-proxy) project.
 * Internal **storage** for non structured resources (json, XML, etc.) based  on the GeoSolutions [GeoStore](https://github.com/geosolutions-it/geostore) project.
 * **Configuration** services, to allow full application(s) and services configurability
 * **Security** with the ability to configure authentication using an internal or external service, and a flexible authorization policy for services and resources access

![MapStore 2 - Backend](https://docs.google.com/drawings/d/12SURY5tdrjOXwYx0kH1LHUmHogZpWvmcEoFCGJOgJWY/pub?w=480&h=360)
