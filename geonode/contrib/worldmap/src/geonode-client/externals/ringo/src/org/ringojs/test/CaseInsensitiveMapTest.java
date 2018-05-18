/*
 *  Copyright 2006 Hannes Wallnoefer <hannes@helma.at>
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

package org.ringojs.test;

import junit.framework.TestCase;
import org.ringojs.util.CaseInsensitiveMap;

import java.util.Map;
import java.util.HashMap;

public class CaseInsensitiveMapTest extends TestCase {

    private static final Map<String, Boolean> fixture = new HashMap<String, Boolean>();

    static {
        fixture.put("AAA", true);
        fixture.put("Bbb", true);
        fixture.put("cCC", true);
    }

    public void testAddRemove() {
        Map<String, Boolean> map = new CaseInsensitiveMap<Boolean>();
        map.put("AAA", true);
        map.put("Bbb", true);
        map.put("cCC", true);
        map.put("ZZtop", true);
        map.remove("zzTOP");
        assertEquals(fixture, map);
    }

    public void testOverwrite() {
        Map<String, Boolean> map = new CaseInsensitiveMap<Boolean>();
        map.put("AAA", true);
        map.put("Bbb", true);
        map.put("CCC", false);
        // NOTE: fixture.equals(map) will return true because of
        // the specifics of AbstractMap.equals() implementation
        assertFalse(map.equals(fixture));
        map.put("cCC", true);
        assertEquals(fixture, map);
    }

}
