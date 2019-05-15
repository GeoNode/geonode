/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
 /**
 * This definition of DC add the dc:URI to the possible Dublin core elements
 * originally available in the ogc-schemas mappings.
 */
module.exports = {
    n: 'DC_1_1',
    dens: 'http:\/\/purl.org\/dc\/elements\/1.1\/',
    tis: [{
        ln: 'ElementContainer',
        tn: 'elementContainer',
        ps: [{
            n: 'dcElement',
            mno: 0,
            col: true,
            mx: false,
            dom: false,
            en: 'DC-element',
            ti: '.SimpleLiteral',
            t: 'er'
        }, {
            n: 'dcElement',
            mno: 0,
            col: true,
            mx: false,
            dom: false,
            en: 'DC-element',
            ti: '.URI',
            t: 'er'
          }]
      }, {
        ln: 'SimpleLiteral',
        ps: [{
            n: 'content',
            col: true,
            dom: false,
            t: 'ers'
          }, {
            n: 'scheme',
            an: {
              lp: 'scheme'
            },
            t: 'a'
          }]
      }, {
        ln: 'URI',
        ti: 'URI',
        sh: 'DC-element',
        collection: true,
        propertyInfos: [ {
            type: 'attribute',
            name: 'name',
            attributeName: 'name',
            typeInfo: 'String'
        }, {
            type: 'attribute',
            name: 'description',
            attributeName: 'description',
            typeInfo: 'String'
        }, {
            type: 'attribute',
            name: 'protocol',
            attributeName: 'protocol',
            typeInfo: 'String'
        }, {
            type: 'value',
            name: 'value',
            typeInfo: 'String'
        }]
    }],
    eis: [{
        en: 'identifier',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'relation',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'format',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'title',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'description',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'source',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'date',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'type',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'language',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'DC-element',
        ti: '.SimpleLiteral'
      }, {
        en: 'rights',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'creator',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'publisher',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'contributor',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'subject',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'coverage',
        ti: '.SimpleLiteral',
        sh: 'DC-element'
      }, {
        en: 'URI',
        ti: '.URI',
        sh: 'DC-element'
      }]
};
