# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import json


def _layer_json(layers, sources):
    """
    return a list of layer config for the provided layer
    """
    server_lookup = {}

    def uniqify(seq):
        """
        get a list of unique items from the input sequence.

        This relies only on equality tests, so you can use it on most
        things.  If you have a sequence of hashables, list(set(seq)) is
        better.
        """
        results = []
        for x in seq:
            if x not in results:
                results.append(x)
        return results

    configs = [l.source_config() for l in layers]

    i = 0
    for source in uniqify(configs):
        while str(i) in sources:
            i = i + 1
        sources[str(i)] = source
        server_lookup[json.dumps(source)] = str(i)

    def source_lookup(source):
        for k, v in sources.iteritems():
            if v == source:
                return k
        return None

    def layer_config(l, user=None):
        cfg = l.layer_config(user=user)
        src_cfg = l.source_config()
        source = source_lookup(src_cfg)
        if source:
            cfg["source"] = source
        return cfg

    return [layer_config(l, user=None) for l in layers]
