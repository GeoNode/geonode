@login @backend @social
Feature: User can login using authentication

    Background:
        Given A global administrator named "admin"

    Scenario: User can access login page
        When I go to the "login" page
        Then I see "Log in"

    @successful
    Scenario: Admin user
        Given I have an admin account
        When I go to the "login" page
        And I fill in "Username" with "admin"
        And I fill in "Password" with "admin"
        And I press the "Log in" button
        Then I should see "admin"
