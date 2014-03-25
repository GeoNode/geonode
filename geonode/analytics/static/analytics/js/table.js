d3.json('/static/analytics/data/data.json', function (error,data) {
  
  var keys = data.map(function(d){return d.caption;});
  var values = data.map(function(d){return d.measure;});
 
  function showDataAsTable(container, values, keys, labels, sortable) {

      var table = d3.select(container).append("table");
          theadtr = table.append("thead").append("tr");
          tbody = table.append("tbody");

      var th = theadtr.selectAll("th")
          .data(labels)
        .enter().append("th")
          .text(function(d) { return d; });

      var tr = tbody.selectAll("tr")
          .data(values)
        .enter().append("tr");

      var td = tr.selectAll("td")
          .data(function(d, i) { return [keys[i], d]; })
        .enter().append("td")
          .text(function(d) { return d; });
      
      if (sortable) {
        $(table).tableSort();
      }

    }
    showDataAsTable('#table', values, keys, ['Pays', 'Valeur'], true);
});



