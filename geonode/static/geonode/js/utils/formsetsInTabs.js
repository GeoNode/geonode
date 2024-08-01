

let totalForms = $('#id_' + prefix + '-TOTAL_FORMS').val();
let initialForms = $('#id_' + prefix + '-INITIAL_FORMS').val();
let maxForms = $('#id_' + prefix + '-MAX_NUM_FORMS').val();
let minForms = $('#id_' + prefix + '-MIN_NUM_FORMS').val();
let deleteInput = $("#id_FORM-xx-DELETE")
let hiddenInput = $("#id_FORM-xx-id")

let allDelete = $('#DELETE')

let actualForms = totalForms

let templateTab = $('.templateTab')
let templateContent = $('.templateContent')
let allTabs = $('.allTabs')
let allforms = $('.allContent')

reOrder()
hideDeleteCheckbox()

$("#nav-add").on("click", function () {
    label = Number(actualForms) + 1
    removeActive()
    newTab = templateTab.clone(true).removeClass('hidden')
    newTab.removeClass('templateTab').removeClass('nav-empty')
    newTab.attr('id', '')
    newTab.find('a').attr('href', '#' + prefix + '-' + actualForms)
    newTab.attr('aria-controls', prefix + '-' + actualForms)
    newTab.find('.newTabTex').text(label)
    newTab.find('.newTabTex').addClass('tabTex').removeClass('newTabTex')
    newTab.insertBefore($('.li-add'))
    newTab.addClass('active')


    newContent = templateContent.clone(true).removeClass('hidden')
    newContent.removeClass('templateContent').removeClass('nav-empty')
    newContent.attr('id', prefix + '-' + actualForms)
    newContent.addClass('in active')
    newContent.find('select, input').each(
        function () {
            $(this).attr('name', $(this).attr('name').replace("__prefix__", actualForms))
            $(this).attr('id', $(this).attr('id').replace("__prefix__", actualForms))
        })
    newContent.insertBefore($('.templateContent'))

    actualForms++
    $('#id_' + prefix + '-TOTAL_FORMS').attr("value", actualForms)
});


$(".nav-remove").on("click", function () {
    removeActive()
    number = $(this).parent('a').attr('href').split('-')[1]
    tabToRemove = $(this).parent('a').parent('li')

    tabToRemove.remove()
    contentToRemove = $('#' + prefix + '-' + number)
    contentToRemove.find('#DELETE input').prop("checked", true)
    contentToRemove.removeAttr('role')
    toDjango = contentToRemove.children('div')
    toDjango.hide().insertAfter(templateContent)
    contentToRemove.remove()
    $('.allContent').find('.tab-pane').first().addClass('active')
    $('.allTabs').find('li:first').addClass('active').find('a').attr('aria-expanded', true)
    reOrder()
    actualForms--


});

function reOrder() {
    counter = 0
    $('.allTabs').find('li:first').addClass('active').find('a').attr('aria-expanded', true)

    $('.allTabs').find('li a').each(
        function () {
            $(this).attr('href', '#' + prefix + '-' + counter)
            $(this).attr('aria-controls', prefix + '-' + counter)
            counterLabel = counter + 1
            $(this).find('.tabTex').text(counterLabel)
            counter++
        }
    )

    counterCont = 0
    $('.allContent').find('.tab-pane').each(
        function () {
            if ($(this).attr('id') != 'templateContent') {
                $(this).attr('id', prefix + '-' + counterCont)
                $(this).find('#DELETE').find('input').attr('id', 'id_' + prefix + '-' + counterCont + '-DELETE')
                $(this).find('#DELETE').find('input').attr('name', prefix + '-' + counterCont + '-DELETE')
                $(this).find('div div:last').find('input').attr('id', 'id_' + prefix + '-' + counterCont + '-id')
                $(this).find('div div:last').find('input').attr('name', prefix + '-' + counterCont + '-id')
                counterCont++
            }

        }
    )

}

function removeActive() {
    $('.allTabs').find('li').each(
        function () {
            $(this).removeClass('active')
            $(this).find('a').attr('aria-expanded', false)
        })
    $('.allContent').find('.tab-pane').each(
        function () {

            $(this).removeClass('active')
        })

}

function hideDeleteCheckbox() {
    allforms.find('#DELETE').hide()
    allforms.find('#DELETE').prev().hide()
}
