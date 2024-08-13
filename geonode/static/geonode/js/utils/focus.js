primaryColor = $('.gn-primary').css('background-color')

projectDiv = $('#related_project')
selectProj = projectDiv.find('select')


selectProj.filterMultiSelect({
    placeholderText: "nothing selected",
    filterText: "Filter",
    selectAllText: "Select All",
    labelText: "",
    selectionLimit: 0,
    caseSensitive: false,
    allowEnablingAndDisabling: true,
});

selectProj.find("option:selected").css("color", primaryColor)


// console.log(selectProj.text())

