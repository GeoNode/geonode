import pytest
from pytest_bdd import scenario, then, when
from urlparse import urljoin

# Docs for the en_browser object: https://splinter.readthedocs.io/en/latest/index.html
# Also note that the browser is operating in a smaller resolution, so the site will be
# in the mobile version


@pytest.mark.django_db(transaction=True)
@scenario('search.feature', 'Search for something that doesn\'t exist')
def test_search_bar():
    pass


@when('I type a name that has no results')
def input_non_matching_name(en_browser):

    # Need this if we're running with phantomjs
    if not en_browser.is_element_visible_by_css('#search_input', 5):
        en_browser.find_by_css('.fa.fa-navicon.fa-lg').click()
        # Need this assert so we know that the css transition has finished before
        # we start manipulating the input (it has a built in delay that will wait
        # for the element to appear before continuing)
        assert en_browser.is_element_visible_by_css('#search_input', 5)

    search_input = en_browser.find_by_id('search_input')
    search_input.click()
    search_input.fill('nonmatchingname')


@when('I hit the enter key')
def search(en_browser):
    search_input = en_browser.find_by_id('search_input')
    search_input.click()
    search_input.type('\n')


@then('It brings me to an empty search results page')
def is_results_page(en_browser, bdd_server):
    assert urljoin(bdd_server.url, '/search/') in en_browser.url
    en_browser.screenshot('/Users/jmeyer/work-dev/geonode3/geonode/output.png')
    # This currently fails as Angular is throwing an $sce:insecurl when attempting to load
    # http://localhost:8000/static/geonode/js/templates/cart.html
    assert en_browser.is_text_present('0 found')

