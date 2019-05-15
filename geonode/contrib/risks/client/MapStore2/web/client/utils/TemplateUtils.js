/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = {
    /**
     * generates a template string to use for static replacements.
     * It's useful for using a similar syntax for static configured strings to
     * use as templates.
     */
    generateTemplateString: (function() {
        var cache = {};

        function generateTemplate(template) {

            var fn = cache[template];

            if (!fn) {
            // Replace ${expressions} (etc) with ${map.expressions}.
                let sanitized = template
                .replace(/\$\{([\s]*[^;\s\{]+[\s]*)\}/g, function(_, match) {
                    return `\$\{map.${match.trim()}\}`;
                })
                // Afterwards, replace anything that's not ${map.expressions}' (etc) with a blank string.
                .replace(/(\$\{(?!map\.)[^}]+\})/g, '');

                fn = Function('map', `return \`${sanitized}\``);
                cache[template] = fn;

            }
            return fn;
        }
        return generateTemplate;
    })()
};
