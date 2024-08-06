
console.log('carregado')


for (let name of formsetsInTabs) {

    form = $('#' + name)
    console.log(form)
    console.log("acima")

    reOrder(form)
    hideDeleteCheckbox(form)
}


function dataForm(form) {
    instance = form.attr('id')
    console.log(instance)
    totalForms = $('#id_' + instance + '-TOTAL_FORMS').val();
    initialForms = $('#id_' + instance + '-INITIAL_FORMS').val();
    maxForms = $('#id_' + instance + '-MAX_NUM_FORMS').val();
    minForms = $('#id_' + instance + '-MIN_NUM_FORMS').val();

    allDelete = form.find('#DELETE')

    actualForms = totalForms

    templateTab = form.find('.templateTab')
    templateContent = form.find('.templateContent')
    allTabs = form.find('.allTabs')
    allForms = form.find('.allContent')



    return {
        totalForms,
        initialForms,
        maxForms,
        minForms,
        allDelete,
        actualForms,
        templateTab,
        templateContent,
        allTabs,
        allForms,
    }
}



// let totalForms = activeForm.totalForms
// let initialForms = activeForm.initialForms
// let maxForms = activeForm.maxForms
// let minForms = activeForm.minForms




function addNewTab(element) {
    button = $("#" + element.id)
    form = button.closest("div[id^=form]")
    infosForm = dataForm(form)
    prefix = form.attr("id")
    actualForms = infosForm.actualForms
    label = Number(actualForms) + 1
    removeActive(form)
    newTab = infosForm.templateTab.clone(true).removeClass('hidden')
    console.log(newTab)
    newTab.removeClass('templateTab').removeClass('nav-empty')
    newTab.attr('id', '')
    newTab.find('a').attr('href', '#' + prefix + '-' + actualForms)
    newTab.attr('aria-controls', prefix + '-' + actualForms)
    newTab.find('.newTabTex').text(label)
    newTab.find('.newTabTex').addClass('tabTex').removeClass('newTabTex')

    newTab.insertBefore(form.find('.li-add'))
    newTab.addClass('active')

    templateContent = infosForm.templateContent
    newContent = templateContent.clone(true).removeClass('hidden')
    newContent.removeClass('templateContent').removeClass('nav-empty')
    newContent.attr('id', prefix + '-' + actualForms)
    newContent.addClass('in active')
    newContent.find('select, input').each(
        function () {
            $(this).attr('name', $(this).attr('name').replace("__prefix__", actualForms))
            $(this).attr('id', $(this).attr('id').replace("__prefix__", actualForms))
        })
    newContent.insertBefore(form.find('.templateContent'))

    actualForms++
    $('#id_' + prefix + '-TOTAL_FORMS').attr("value", actualForms)
};


function removeTab(element) {

    element = $(element)
    form = element.closest("div[id^=form]")
    console.log(form.attr("id"))
    infosForm = dataForm(form)
    prefix = form.attr("id")
    actualForms = infosForm.actualForms
    removeActive(form)
    console.log(element[0])
    number = element.parent('a').attr('href').split('-')[1]
    tabToRemove = element.parent('a').parent('li')

    tabToRemove.remove()
    contentToRemove = $('#' + prefix + '-' + number)
    contentToRemove.find('#DELETE input').prop("checked", true)
    contentToRemove.removeAttr('role')
    toDjango = contentToRemove.children('div')
    toDjango.hide().insertAfter(templateContent)
    contentToRemove.remove()
    form.find('.allContent').find('.tab-pane').first().addClass('active')
    form.find('.allTabs').find('li:first').addClass('active').find('a').attr('aria-expanded', true)
    reOrder(form)
    actualForms--
    console.log(actualForms)
    console.log(prefix)
    $('#id_' + prefix + '-TOTAL_FORMS').attr("value", actualForms)


};

function reOrder(form) {
    console.log(form[0])
    prefix = form.attr("id")
    console.log(prefix)
    counter = 0
    form.find('.allTabs').find('li:first').addClass('active').find('a').attr('aria-expanded', true)

    form.find('.allTabs').find('li a').each(
        function () {
            $(this).attr('href', '#' + prefix + '-' + counter)
            $(this).attr('aria-controls', prefix + '-' + counter)
            counterLabel = counter + 1
            $(this).find('.tabTex').text(counterLabel)
            counter++
        }
    )

    counterCont = 0
    form.find('.allContent').find('.tab-pane').each(
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

function removeActive(form) {
    form.find('.allTabs').find('li').each(
        function () {
            $(this).removeClass('active')
            $(this).find('a').attr('aria-expanded', false)
        })
    form.find('.allContent').find('.tab-pane').each(
        function () {

            $(this).removeClass('active')
        })

}

function hideDeleteCheckbox(form) {
    form.find('.allContent').find('#DELETE').hide()
    form.find('.allContent').find('#DELETE').prev().hide()
}
