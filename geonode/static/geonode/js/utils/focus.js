primaryColor = $('.gn-primary').css('background-color')

projectDiv = $('#related_project')
selectProj = projectDiv.find('select')
console.log(selectProj.text())


selectProj.filterMultiSelect();
checkbox = $('.filter-multi-select .dropdown-item .custom-control input[type=checkbox]')
// checkboxIndeter = $('.filter-multi-select .dropdown-item -checkbox')
selected = $('.filter-multi-select .selected-items')
checkbox.css('background', 'red');
// checkboxIndeter.css("background-color", 'blue')

// selected.css('background', 'red');

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

