primaryColor = $('.gn-primary').css('background-color')

projectDiv = $('#related_project')
selectProj = projectDiv.find('select')


selectProj.filterMultiSelect();
checkbox = $('.filter-multi-select .dropdown-item .custom-control input[type=checkbox]')

selected = $('.filter-multi-select .selected-items')
checkbox.css('background', 'red');
