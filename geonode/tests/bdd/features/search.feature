@search
Feature: User can search

    @successful
    Scenario: Search for something that doesn't exist
        When I type a name that has no results
        And I hit the enter key
        Then It brings me to an empty search results page
