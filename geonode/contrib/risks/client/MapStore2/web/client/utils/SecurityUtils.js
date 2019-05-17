/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const ConfigUtils = require('./ConfigUtils');
const URL = require('url');
const assign = require('object-assign');
const {head} = require('lodash');

/**
 * This utility class will get information about the current logged user directly from the store.
 */
const SecurityUtils = {

    /**
     * Stores the logged user secuirty information.
     */
    setStore: function(store) {
        this.store = store;
    },

    /**
     * Gets security state form the store.
     */
    getSecurityInfo() {
        return this.store.getState().security;
    },

    /**
     * Returns the current user or undefined if not available.
     */
    getUser() {
        const securityInfo = this.getSecurityInfo();
        return securityInfo && securityInfo.user;
    },

    /**
     * Returns the current user basic authentication header value.
     */
    getBasicAuthHeader() {
        const securityInfo = this.getSecurityInfo();
        return securityInfo && securityInfo.authHeader;
    },

    /**
     * Returns the current user token value.
     */
    getToken() {
        const securityInfo = this.getSecurityInfo();
        return securityInfo && securityInfo.token;
    },

    /**
     * Return the user attributes as an array. If the user is undefined or
     * doens't have any attributes an empty array is returned.
     */
    getUserAttributes: function(providedUser) {
        const user = providedUser ? providedUser : this.getUser();
        if (!user || !user.attribute) {
            // not user defined or the user doesn't have any attributes
            return [];
        }
        let attributes = user.attribute;
        // if the user has only one attribute we need to put it in an array
        return Array.isArray(attributes) ? attributes : [attributes];
    },

    /**
     * Search in the user attributes an attribute that matchs the provided
     * attribute name. The search will not be case sensitive. Undefined is
     * returned if the attribute could not be found.
     */
    findUserAttribute: function(attributeName) {
        // getting the user attributes
        let userAttributes = this.getUserAttributes();
        if (!userAttributes || !attributeName ) {
            // the user as no attributes or the provided attribute name is undefined
            return undefined;
        }
        return head(userAttributes.filter(attribute => attribute.name
            && attribute.name.toLowerCase() === attributeName.toLowerCase()));
    },

    /**
     * Search in the user attributes an attribute that matchs the provided
     * attribute name. The search will not be case sensitive. Undefined is
     * returned if the attribute could not be found otherwise the attribute
     * value is returned.
     */
    findUserAttributeValue: function(attributeName) {
        let userAttribute = this.findUserAttribute(attributeName);
        return userAttribute && userAttribute.value;
    },

    /**
     * Returns an array with the configured authentication rules. If no rules
     * were configured an empty array is returned.
     */
    getAuthenticationRules: function() {
        return ConfigUtils.getConfigProp('authenticationRules') || [];
    },

    /**
     * Checks if authentication is activated or not.
     */
    isAuthenticationActivated: function() {
        return ConfigUtils.getConfigProp('useAuthenticationRules') || false;
    },

    /**
     * Returns the authentication method that should be used for the provided URL.
     * We go through the authentication rules and find the first one that matchs
     * the provided URL, if no rule matchs the provided URL undefined is returned.
     */
    getAuthenticationMethod: function(url) {
        const foundRule = head(this.getAuthenticationRules().filter(
            rule => rule && rule.urlPattern && url.match(new RegExp(rule.urlPattern, "i"))));
        return foundRule ? foundRule.method : undefined;
    },

    /**
     * This method will add query parameter based authentications to an url.
     */
    addAuthenticationToUrl: function(url) {
        if (!url || !this.isAuthenticationActivated()) {
            return url;
        }
        const parsedUrl = URL.parse(url, true);
        parsedUrl.query = this.addAuthenticationParameter(url, parsedUrl.query);
        // we need to remove this to force the use of query
        delete parsedUrl.search;
        return URL.format(parsedUrl);
    },

    /**
     * This method will add query parameter based authentications to an object
     * containing query paramaters.
     */
    addAuthenticationParameter: function(url, parameters) {
        if (!url || !this.isAuthenticationActivated()) {
            return parameters;
        }
        switch (this.getAuthenticationMethod(url)) {
            case 'authkey':
                const token = this.getToken();
                if (!token) {
                    return parameters;
                }
                return assign(parameters || {}, {'authkey': token});
            default:
                // we cannot handle the required authentication method
                return parameters;
        }
    }
};

module.exports = SecurityUtils;
