/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var TemplateUtils = require('../TemplateUtils');


describe('TemplateUtils', () => {
    beforeEach( () => {

    });
    afterEach((done) => {
        document.body.innerHTML = '';

        setTimeout(done);
    });
    it('test template generation', () => {
        let templateFunction = TemplateUtils.generateTemplateString("this is a ${test}");
        expect(templateFunction).toExist();
        let templateResult = templateFunction({test: "TEST"});
        expect(templateResult).toBe("this is a TEST");
    });
    it('test template cache', () => {
        let templateFunction = TemplateUtils.generateTemplateString("this is a ${test}");
        expect(templateFunction).toExist();
        let templateResult = templateFunction({test: "TEST"});
        expect(templateResult).toBe("this is a TEST");
        let templateFunction2 = TemplateUtils.generateTemplateString("this is a ${test}");
        expect(templateFunction2).toExist();
        let templateResult2 = templateFunction2({test: "TEST"});
        expect(templateResult2).toBe("this is a TEST");
        expect(templateFunction).toBe(templateFunction2);
        let templateFunction3 = TemplateUtils.generateTemplateString("this is a second ${test}");
        let templateResult3 = templateFunction3({test: "TEST"});
        expect(templateResult3).toBe("this is a second TEST");

    });
});
