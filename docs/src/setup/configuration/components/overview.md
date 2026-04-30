# Overview

GeoNode interacts with GeoServer through an advanced security mechanism based on the OAuth2 protocol and GeoFence. This section is a walk-through of the configuration and setup of GeoNode and GeoServer advanced security.

What we will see in this section is:

- **Introduction**

- **GeoNode** (Security Backend):

    1. Django Authentication

    2. Django OAuth Toolkit Setup and Configuration

    3. Details on `settings.py` security settings

- **GeoServer** (Security Backend):

    1. GeoServer Security Subsystem

    2. Introduction to the GeoServer OAuth2 Security Plugin

    3. Configuration of the `GeoNode REST Role Service`

    4. Configuration of the `GeoNode OAuth2 Authentication Filter`

    5. The GeoServer Authentication Filter Chains

    6. Introduction to GeoFence Plugin, the advanced security framework for GeoServer

- **Troubleshooting and Advanced Features**:

    1. Common Issues and Fixes

    2. How to setup `HTTPS` secured endpoints

    3. GeoFence Advanced Features

## Introduction

GeoServer, the geospatial backend server of GeoNode, is a spatial server that needs authenticated users in order to access protected resources or administration functions.

GeoServer supports several kinds of authentication and authorization mechanisms. Those systems are pluggable and GeoServer can use them at the same time by means of a `Filter Chain`. Briefly, this mechanism allows GeoServer to check different A&A protocols one by one. The first one matching is used by GeoServer to authorize the users.

GeoNode authentication is based by default on the Django security subsystem. Django authentication allows GeoNode to manage its internal users, groups, roles, and sessions.

GeoNode has some external components, like GeoServer or QGIS Server, which are pluggable and stand-alone services devoted to the management of geospatial data. Those external services have their own authentication and authorization mechanisms, which must be synchronized somehow with the GeoNode one. Also, those external services maintain, in most cases and unless a specific configuration disables this, alternative security access which, for instance, allows GeoNode to modify the geospatial catalog under the hood, or a system administrator to have independent and privileged access to the servers.

Before going deeply into how GeoServer/GeoNode A&A works and how it can be configured to work correctly with GeoNode, let’s quickly clarify the difference between `Authentication` and `Authorization`.

## Authentication

Authentication is the process of verifying the identity of someone through the use of some sort of credentials and a handshake protocol. If the credentials are valid, the authorization process starts. Authentication always proceeds to authorization, although they may often seem combined. The two terms are often used synonymously, but they are two different processes.

For more details and an explanation of the authentication concepts, take a look [here](http://searchsecurity.techtarget.com/definition/authentication).

## Authorization

Authorization is the process of allowing authenticated users to access protected resources by checking their roles and rights against some sort of security rules mechanism or protocol. In other words, it allows you to control access rights by granting or denying specific permissions to specific authorized users.
