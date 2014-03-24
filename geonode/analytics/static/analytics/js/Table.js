var Table = {  
  table : null,
  theadtr : null,
  tbody : null,

  init : function (selector) {
    this.table = d3.select(selector).append("table");
    this.thead = this.table.append("thead").append("tr");
    this.tbody = this.table.append("tbody");
  },

  setData : function (data, labels, sortable) {
    var keys = d3.keys(data);
    var values = d3.values(data);

    var captions = values.map(function(d){return d.caption});
    var measures = values.map(function(d){return d.measure});

    // Header
    var th = this.thead.selectAll("th")
        .data(labels);

    th.enter().append("th");// Enter
    th.exit().remove();// Exit
     
    th.text(function(d) { return d; });// Update

    // Lines
    var tr = this.tbody.selectAll("tr")
        .data(measures);

    tr.enter().append("tr");// Enter
    tr.exit().remove();// Exit, no update here this is td that will be updated

    
    var td = tr.selectAll("td")
        .data(function(d, i) { return [captions[i], d]; });

    td.enter().append("td");// Enter
    td.exit().remove();// Exit
    td.text(function(d) { return d; });// Update

    if (sortable) {
      $(table).tableSort();
    }
  }  
}