describe("ide.permalink", function () {
  // check share links
  it("share uncompressed", function () {
    var q = '<!--\nThis is an example Overpass query.\nTry it out by pressing the Run button above!\nYou can find more examples with the Load tool.\n-->\n<query type="node">\n  <has-kv k="amenity" v="drinking_water"/>\n  <bbox-query {{bbox}}/><!--this is auto-completed with the\n                   current map view coordinates.-->\n</query>\n<print/>';
    var p = ide.compose_share_link(q,false,false,false);
    expect(p).to.have.string("?Q=%3C!--%0AThis%20is%20an%20example%20Overpass%20query.%0ATry%20it%20out%20by%20pressing%20the%20Run%20button%20above!%0AYou%20can%20find%20more%20examples%20with%20the%20Load%20tool.%0A--%3E%0A%3Cquery%20type%3D%22node%22%3E%0A%20%20%3Chas-kv%20k%3D%22amenity%22%20v%3D%22drinking_water%22%2F%3E%0A%20%20%3Cbbox-query%20%7B%7Bbbox%7D%7D%2F%3E%3C!--this%20is%20auto-completed%20with%20the%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20current%20map%20view%20coordinates.--%3E%0A%3C%2Fquery%3E%0A%3Cprint%2F%3E");
    expect(p).not.to.have.string("?q=");
    expect(p).not.to.have.string("&C=");
    expect(p).not.to.have.string("&c=");
    expect(p).not.to.have.string("&R");
  });
  it("share compressed", function () {
    var q = '<!--\nThis is an example Overpass query.\nTry it out by pressing the Run button above!\nYou can find more examples with the Load tool.\n-->\n<query type="node">\n  <has-kv k="amenity" v="drinking_water"/>\n  <bbox-query {{bbox}}/><!--this is auto-completed with the\n                   current map view coordinates.-->\n</query>\n<print/>';
    var p = ide.compose_share_link(q,true,false,false);
    expect(p).not.to.have.string("?Q=");
    expect(p).to.have.string("?q=PCEtLQpUaGlzIMSHIGFuIGV4YW1wbGUgT3ZlcnBhc8SIcXXEmXkuxIRyecSJdCBvdcSoYsSmcHJlxJ1pbmcgdGjElVJ1xI1ixKt0b8SNYWJvxJghClnEqiBjxIwgZsSzZCBtb8SwxI7EkMSSxJTEiHdpxLfEtsS4IExvYcWQxL9vbMSjxII-CjzEn8ShxLZ5cGU9Im5vZGUixakgIDxoxJwta3Yga8WyxJFlbsWbeSIgdsWyZHLEs2vEs2dfd2F0xJkiL8W5xbtixYN4LcWsxKUge3vGnW94fX3GmsSAxILEt8SKxIphxKtvLWNvxZdlxpfFkMWaxZzEt2UKxbrHgMeBx4LHgmN1csSwbsSobWFwxotpZXfFim_Fk2TEs8aWxLEuxajFqi_GoXnFqTzEr8SzdMaa");
    expect(p).not.to.have.string("&C=");
    expect(p).not.to.have.string("&c=");
    expect(p).not.to.have.string("&R");
  });
  it("share coordinates", function () {
    var q = ' ';
    ide.map = {
      getCenter: function() {return {lat:12.3456, lng:-65.4321}; },
      getZoom: function() {return 8},
    };
    var p;
    p = ide.compose_share_link(q,false,true,false);
    expect(p).to.have.string("&C=12.3456;-65.4321;8");
    expect(p).not.to.have.string("&c=");
    p = ide.compose_share_link(q,true,true,false);
    expect(p).not.to.have.string("&C=");
    expect(p).to.have.string("&c=Au47axyXAI");
  });
  it("share autorun", function () {
    var q = ' ';
    var p;
    p = ide.compose_share_link(q,false,false,true);
    expect(p).to.have.string("&R");
  });

});
