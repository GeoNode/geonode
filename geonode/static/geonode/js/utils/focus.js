primaryColor = $('.gn-primary').css('background-color')

projectDiv = $('#related_project')
selectProj = projectDiv.find('select')
console.log(selectProj.text())


selectProj.filterMultiSelect();
checkbox = $('.filter-multi-select .dropdown-item .custom-control input')
// checkboxIndeter = $('.filter-multi-select .dropdown-item -checkbox')
selected = $('.filter-multi-select .selected-items')
checkbox.before().css("background-color", 'blue')
// checkboxIndeter.css("background-color", 'blue')

selected.addClass('btn-primary')

// selectProj.filterMultiSelect({
//     placeholderText: "nothing selected",
//     filterText: "Filter",
//     selectAllText: "Select All",
//     labelText: "",
//     selectionLimit: 0,
//     caseSensitive: false,
//     allowEnablingAndDisabling: true,
// });

// selectProj.find("option:selected").css("color", primaryColor)


console.log(selectProj.text())
console.log(selected)
console.log(checkbox)

