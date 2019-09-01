/* =============================================================
 * resources_harvest.js
 * =============================================================
 * Original written by ---------
 * =============================================================*/

/* =============================================================
 usage
 * tableFilter = new TableFilter();
 * filterInfo = [{"id": 'input elem id', "data_key": "data key in resources array"},..]
 * resources = [{"key1":"val1", "key2":"val2",..}, ...]
 * tableFilter.init(filterInfo, resources, "table_id");
 *
 * * ============================================================ */
var TableFilter = function () {
    var me = this;
    me.tableId = null;
    me.filterElems = {};
    me.filterButton = {}
    me.groupedData = {};

    me.init = function (filterInfo, resData, tableId) {
        me.tableId = tableId;
        for (var i in filterInfo) {
            if (filterInfo[i].id) {
                me.filterElems[filterInfo[i].id] = $('#' + filterInfo[i].id);
                me.filterButton[filterInfo[i].id] = $('#btn-' + filterInfo[i].id);
                me.groupedData[filterInfo[i].id] = _.groupBy(resData, filterInfo[i].data_key)
                values = _.keys(me.groupedData[filterInfo[i].id]);
                me.filterElems[filterInfo[i].id].typeahead({
                    source: values,
                    autoSelect: true,

                });
                me.filterElems[filterInfo[i].id].change(function () {
                    // var current = $(this).typeahead("getActive");
                    var val = $(this).val();
                    // if (current == val) {
                        me.searchRows();
                    // }

                });
                me.filterElems[filterInfo[i].id].keydown(function (e) {
                    if (e.which == 13) {
                        e.preventDefault();
                        me.searchRows();
                    }
                })
                me.filterButton[filterInfo[i].id].click(function (e) {
                    e.preventDefault();
                    me.searchRows();
                })
            }
        }
    }

    /*** seraching row in the resources ****/
    me.searchRows = function () {
        var rows = [];
        $("input[name='typeahead_search']").each(function (index, value) {
            var id = $(this).attr('id');
            var searchVal = me.filterElems[id].val().trim();
            var res = me.groupedData[id][searchVal];
            if (res && res.length > 0) {
                rows = rows.concat(res);
            }
        })
        if (rows.length > 0) {
            me.filterRows(rows)
        } else {
            me.restoreTable()
        }
    }

    /*** clear input elements ****/
    me.clearFilterElems = function () {
        for (var key in me.filterElems) {
            me.filterElems[key].val("");
        }
    }

    /*** restore table into original position ***/
    me.restoreTable = function () {
        var table = document.getElementById(me.tableId);
        var tr = table.getElementsByTagName("tr");
        for (i = tr.length - 1; i >= 2; i--) {
            if (tr[i].getAttribute("name") == "filter_row") {
                table.deleteRow(i)
            } else {
                tr[i].style.display = "";
            }
        }

    }

    /*** display filter table rows ****/
    me.filterRows = function (rows) {
        var table = document.getElementById(me.tableId);
        var tr = table.getElementsByTagName("tr");
        for (i = tr.length - 1; i >= 2; i--) {
            if (tr[i].getAttribute("name") === "filter_row") {
                table.deleteRow(i)
            } else {
                tr[i].style.display = "none";
            }
        }

        for (i = 0; i < rows.length; i++) {
            var tr = table.insertRow(i + 2);
            tr.setAttribute("name", "filter_row");
            var td = tr.insertCell(0);
            var chkbox = document.createElement("input");
            chkbox.setAttribute("type", "checkbox");
            chkbox.setAttribute("name", "resource_list");
            chkbox.setAttribute("id", "option_" + rows[i]["id"]);
            chkbox.setAttribute("value", "" + rows[i]["id"]);
            td.appendChild(chkbox)
            var j = 1;
            for (key in rows[i]) {
                td = tr.insertCell(j);
                td.innerHTML = rows[i][key]
                j++;
            }
        }
    }
}
