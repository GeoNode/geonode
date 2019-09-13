/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

const fs = require('fs-extra');
const STATIC_PATH = '../static/monitoring/';
const additionalResources = [
    {
        from: 'translations/',
        to: `${STATIC_PATH}translations/`
    },
    {
        from: 'assets/',
        to: `${STATIC_PATH}assets/`
    }
];

function copyAdditionalResources() {
    return new Promise(function(resolve, reject) {
        console.log('## COPY ADDITIONAL RESOURCES ##');
        try {
            additionalResources.forEach(function(additionalResource) {
                fs.copySync(additionalResource.from, additionalResource.to);
                console.log(`   - ${additionalResource.to} copied`);
            });
            if (additionalResources.length === 0) console.log('   - no additional resources to copy');
        } catch(e) {
            return reject(e);
        }
        return resolve();
    });
}

copyAdditionalResources();