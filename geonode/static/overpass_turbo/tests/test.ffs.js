describe("ide.ffs", function () {

  var ffs;
  before(function() {
    ffs = turbo.ffs();
  });

  function compact(q) {
    q = q.replace(/\/\*[\s\S]*?\*\//g,"");
    q = q.replace(/\/\/.*/g,"");
    q = q.replace(/\[out:json\]\[timeout:.*?\];/,"");
    q = q.replace(/\(\{\{bbox\}\}\)/g,"(bbox)");
    q = q.replace(/\{\{geocodeArea:([^\}]*)\}\}/g,"area($1)");
    q = q.replace(/\{\{geocodeCoords:([^\}]*)\}\}/g,"coords:$1");
    q = q.replace(/\{\{date:([^\}]*)\}\}/g,"date:$1");
    q = q.replace(/\{\{[\s\S]*?\}\}/g,"");
    q = q.replace(/ *\n */g,"");
    return q;
  };
  var out_str = "out body;>;out skel qt;";

  // basic conditions
  describe("basic conditions", function () {
    // key
    it("key=*", function () {
      var search = "foo=*";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"](bbox);"+
          "way[\"foo\"](bbox);"+
          "relation[\"foo\"](bbox);"+
        ");"+
        out_str
      );
    });
    // not key
    it("key!=*", function () {
      var search = "foo!=*";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"!~\".*\"](bbox);"+
          "way[\"foo\"!~\".*\"](bbox);"+
          "relation[\"foo\"!~\".*\"](bbox);"+
        ");"+
        out_str
      );
    });
    // key-value
    it("key=value", function () {
      var search = "foo=bar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"=\"bar\"](bbox);"+
          "way[\"foo\"=\"bar\"](bbox);"+
          "relation[\"foo\"=\"bar\"](bbox);"+
        ");"+
        out_str
      );
    });
    // not key-value
    it("key!=value", function () {
      var search = "foo!=bar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"!=\"bar\"](bbox);"+
          "way[\"foo\"!=\"bar\"](bbox);"+
          "relation[\"foo\"!=\"bar\"](bbox);"+
        ");"+
        out_str
      );
    });
    // regex key-value
    it("key~value", function () {
      var search = "foo~bar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"~\"bar\"](bbox);"+
          "way[\"foo\"~\"bar\"](bbox);"+
          "relation[\"foo\"~\"bar\"](bbox);"+
        ");"+
        out_str
      );
    });
    // regex key
    it("~key~value", function () {
      var search = "~foo~bar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[~\"foo\"~\"bar\"](bbox);"+
          "way[~\"foo\"~\"bar\"](bbox);"+
          "relation[~\"foo\"~\"bar\"](bbox);"+
        ");"+
        out_str
      );
    });
    // not regex key-value
    it("key!~value", function () {
      var search = "foo!~bar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"!~\"bar\"](bbox);"+
          "way[\"foo\"!~\"bar\"](bbox);"+
          "relation[\"foo\"!~\"bar\"](bbox);"+
        ");"+
        out_str
      );
    });
    // susbtring key-value
    it("key:value", function () {
      // normal case: just do a regex search
      var search = "foo:bar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"~\"bar\"](bbox);"+
          "way[\"foo\"~\"bar\"](bbox);"+
          "relation[\"foo\"~\"bar\"](bbox);"+
        ");"+
        out_str
      );
      // but also escape special characters
      search = "foo:'*'";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"~\"\\\\*\"](bbox);"+
          "way[\"foo\"~\"\\\\*\"](bbox);"+
          "relation[\"foo\"~\"\\\\*\"](bbox);"+
        ");"+
        out_str
      );
    });
  });

  // data types
  describe("data types", function () {
    describe("strings", function () {
      // strings
      it("double quoted strings", function () {
        var search, result;
        // double-quoted string
        search = '"a key"="a value"';
        result = ffs.construct_query(search);
        expect(compact(result)).to.equal(
          '('+
            'node["a key"="a value"](bbox);'+
            'way["a key"="a value"](bbox);'+
            'relation["a key"="a value"](bbox);'+
          ');'+
          out_str
        );
      });        
      it("single-quoted string", function () {
        var search, result;
        // single-quoted string
        search = "'foo bar'='asd fasd'";
        result = ffs.construct_query(search);
        expect(compact(result)).to.equal(
          '('+
            'node["foo bar"="asd fasd"](bbox);'+
            'way["foo bar"="asd fasd"](bbox);'+
            'relation["foo bar"="asd fasd"](bbox);'+
          ');'+
          out_str
        );
      });
      it("quoted unicode string", function () {
        var search = "name='بیجنگ'";
        var result = ffs.construct_query(search);
        expect(compact(result)).to.equal(
          '('+
            'node["name"="بیجنگ"](bbox);'+
            'way["name"="بیجنگ"](bbox);'+
            'relation["name"="بیجنگ"](bbox);'+
          ');'+
          out_str
        );
      });
      it("unicode string", function () {
        var search = "name=Béziers";
        var result = ffs.construct_query(search);
        expect(compact(result)).to.equal(
          '('+
            'node["name"="Béziers"](bbox);'+
            'way["name"="Béziers"](bbox);'+
            'relation["name"="Béziers"](bbox);'+
          ');'+
          out_str
        );
      });
    });
    // regexes
    it("regex", function () {
      var search, result;
      // simple regex
      search = "foo~/bar/";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"~\"bar\"](bbox);"+
          "way[\"foo\"~\"bar\"](bbox);"+
          "relation[\"foo\"~\"bar\"](bbox);"+
        ");"+
        out_str
      );
      // simple regex with modifier
      search = "foo~/bar/i";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"~\"bar\",i](bbox);"+
          "way[\"foo\"~\"bar\",i](bbox);"+
          "relation[\"foo\"~\"bar\",i](bbox);"+
        ");"+
        out_str
      );
    });
  });

  // boolean logic
  describe("boolean logic", function () {
    // logical and
    it("logical and", function () {
      var search = "foo=bar and asd=fasd";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"=\"bar\"][\"asd\"=\"fasd\"](bbox);"+
          "way[\"foo\"=\"bar\"][\"asd\"=\"fasd\"](bbox);"+
          "relation[\"foo\"=\"bar\"][\"asd\"=\"fasd\"](bbox);"+
        ");"+
        out_str
      );
    });
    it("logical and (& operator)", function () {
      var search = "foo=bar & asd=fasd";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        '('+
          'node["foo"="bar"]["asd"="fasd"](bbox);'+
          'way["foo"="bar"]["asd"="fasd"](bbox);'+
          'relation["foo"="bar"]["asd"="fasd"](bbox);'+
        ');'+
        out_str
      );
    });
    it("logical and (&& operator)", function () {
      var search = "foo=bar && asd=fasd";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        '('+
          'node["foo"="bar"]["asd"="fasd"](bbox);'+
          'way["foo"="bar"]["asd"="fasd"](bbox);'+
          'relation["foo"="bar"]["asd"="fasd"](bbox);'+
        ');'+
        out_str
      );
    });
    // logical or
    it("logical or", function () {
      var search = "foo=bar or asd=fasd";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"=\"bar\"](bbox);"+
          "way[\"foo\"=\"bar\"](bbox);"+
          "relation[\"foo\"=\"bar\"](bbox);"+
          "node[\"asd\"=\"fasd\"](bbox);"+
          "way[\"asd\"=\"fasd\"](bbox);"+
          "relation[\"asd\"=\"fasd\"](bbox);"+
        ");"+
        out_str
      );
    });
    it("logical or (| operator)", function () {
      var search = "foo=bar | asd=fasd";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        '('+
          'node["foo"="bar"](bbox);'+
          'way["foo"="bar"](bbox);'+
          'relation["foo"="bar"](bbox);'+
          'node["asd"="fasd"](bbox);'+
          'way["asd"="fasd"](bbox);'+
          'relation["asd"="fasd"](bbox);'+
        ');'+
        out_str
      );
    });
    it("logical or (|| operator)", function () {
      var search = "foo=bar || asd=fasd";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        '('+
          'node["foo"="bar"](bbox);'+
          'way["foo"="bar"](bbox);'+
          'relation["foo"="bar"](bbox);'+
          'node["asd"="fasd"](bbox);'+
          'way["asd"="fasd"](bbox);'+
          'relation["asd"="fasd"](bbox);'+
        ');'+
        out_str
      );
    });
    // boolean expression
    it("boolean expression", function () {
      var search = "(foo=* or bar=*) and (asd=* or fasd=*)";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"][\"asd\"](bbox);"+
          "way[\"foo\"][\"asd\"](bbox);"+
          "relation[\"foo\"][\"asd\"](bbox);"+
          "node[\"foo\"][\"fasd\"](bbox);"+
          "way[\"foo\"][\"fasd\"](bbox);"+
          "relation[\"foo\"][\"fasd\"](bbox);"+
          "node[\"bar\"][\"asd\"](bbox);"+
          "way[\"bar\"][\"asd\"](bbox);"+
          "relation[\"bar\"][\"asd\"](bbox);"+
          "node[\"bar\"][\"fasd\"](bbox);"+
          "way[\"bar\"][\"fasd\"](bbox);"+
          "relation[\"bar\"][\"fasd\"](bbox);"+
        ");"+
        out_str
      );
    });
  });

  // meta conditions
  describe("meta conditions", function () {
    // type
    it("type", function () {
      // simple
      var search = "foo=bar and type:node";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"=\"bar\"](bbox);"+
        ");"+
        out_str
      );
      // multiple types
      search = "foo=bar and (type:node or type:way)";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"=\"bar\"](bbox);"+
          "way[\"foo\"=\"bar\"](bbox);"+
        ");"+
        out_str
      );
      // excluding types
      search = "foo=bar and type:node and type:way";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
        ");"+
        out_str
      );
    });
    // newer
    it("newer", function () {
      // regular
      var search = "newer:\"2000-01-01T01:01:01Z\" and type:node";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(newer:\"2000-01-01T01:01:01Z\")(bbox);"+
        ");"+
        out_str
      );
      // relative
      search = "newer:1day and type:node";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(newer:\"date:1day\")(bbox);"+
        ");"+
        out_str
      );
    });
    // user
    it("user", function () {
      // user name
      var search = "user:foo and type:node";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(user:\"foo\")(bbox);"+
        ");"+
        out_str
      );
      // uid
      search = "uid:123 and type:node";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(uid:123)(bbox);"+
        ");"+
        out_str
      );
    });
    // id
    it("id", function () {
      // with type
      var search = "id:123 and type:node";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(123)(bbox);"+
        ");"+
        out_str
      );
      // without type
      search = "id:123";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(123)(bbox);"+
          "way(123)(bbox);"+
          "relation(123)(bbox);"+
        ");"+
        out_str
      );
    });
  });

  // search-regions
  describe("regions", function () {
    // global
    it("global", function () {
      var search = "foo=bar and type:node global";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node[\"foo\"=\"bar\"];"+
        ");"+
        out_str
      );
    });
    // bbox
    it("in bbox", function () {
      // implicit
      var search = "type:node";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(bbox);"+
        ");"+
        out_str
      );
      // explicit
      search = "type:node in bbox";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(bbox);"+
        ");"+
        out_str
      );
    });
    // area
    it("in area", function () {
      var search = "type:node in foobar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "area(foobar)->.searchArea;"+
        "("+
          "node(area.searchArea);"+
        ");"+
        out_str
      );
    });
    // around
    it("around", function () {
      var search = "type:node around foobar";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "node(around:,coords:foobar);"+
        ");"+
        out_str
      );
    });

  });

  // free form
  describe("free form", function () {

    before(function() {
      var fake_ajax = {
        success: function(cb) { 
          cb({
            "amenity/hospital": {
              "name": "Hospital",
              "terms": [],
              "geometry": ["point","area"],
              "tags": {"amenity": "hospital"}
            },
            "amenity/shelter": {
              "name": "Shelter",
              "terms": [],
              "geometry": ["point"],
              "tags": {"amenity": "shelter"}
            },
            "highway": {
              "name": "Highway",
              "terms": [],
              "geometry": ["line"],
              "tags": {"highway": "*"}
            }
          });
          return fake_ajax;
        },
        error: function(cb) {}
      };
      sinon.stub($,"ajax").returns(fake_ajax);
      i18n = {getLanguage: function() {return "en";}};
    });
    after(function() {
      $.ajax.restore();
    });

    it("preset", function() {
      var search, result;
      // preset not found
      search = "foo";
      result = ffs.construct_query(search);
      expect(result).to.equal(false);
      // preset (points, key-value)
      search = "Shelter";
      result = ffs.construct_query(search);
      expect(result).to.not.equal(false);
      expect(compact(result)).to.equal(
        "("+
          "node[\"amenity\"=\"shelter\"](bbox);"+
        ");"+
        out_str
      );
      // preset (points, areas, key-value)
      search = "Hospital";
      result = ffs.construct_query(search);
      expect(result).to.not.equal(false);
      expect(compact(result)).to.equal(
        "("+
          "node[\"amenity\"=\"hospital\"](bbox);"+
          "way[\"amenity\"=\"hospital\"](bbox);"+
          "relation[\"amenity\"=\"hospital\"](bbox);"+
        ");"+
        out_str
      );
      // preset (lines, key=*)
      search = "Highway";
      result = ffs.construct_query(search);
      expect(result).to.not.equal(false);
      expect(compact(result)).to.equal(
        "("+
          "way[\"highway\"](bbox);"+
        ");"+
        out_str
      );

    });

  });

  // sanity conversions for special conditions
  describe("special cases", function () {
    // empty value
    it("empty value", function () {
      var search = "foo='' and type:way";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "way[\"foo\"~\"^$\"](bbox);"+
        ");"+
        out_str
      );
    });
    // empty key
    it("empty key", function () {
      var search = "''=bar and type:way";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "way[~\"^$\"~\"^bar$\"](bbox);"+
        ");"+
        out_str
      );
      // make sure stuff in the value section gets escaped properly
      search = "''='*' and type:way";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "way[~\"^$\"~\"^\\\\*$\"](bbox);"+
        ");"+
        out_str
      );
      // does also work for =*, ~ and : searches
      search = "(''=* or ''~/.../) and type:way";
      result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "way[~\"^$\"~\".*\"](bbox);"+
          "way[~\"^$\"~\"...\"](bbox);"+
        ");"+
        out_str
      );
    });
    // newlines, tabs
    it("newlines, tabs", function () {
      var search = "(foo='\t' or foo='\n' or asd='\\t') and type:way";
      var result = ffs.construct_query(search);
      expect(compact(result)).to.equal(
        "("+
          "way[\"foo\"=\"\\t\"](bbox);"+
          "way[\"foo\"=\"\\n\"](bbox);"+
          "way[\"asd\"=\"\\t\"](bbox);"+
        ");"+
        out_str
      );
    });

  });
  
});
