<Include a few sentences describing the overall goals for this Pull Request>

## Checklist

> Reviewing is a process done by project maintainers, mostly on a volunteer basis. We try to keep the overhead as small as possible and appreciate if you help us to do so by completing the following items. Feel free to ask in a comment if you have troubles with any of them.

For all pull requests:

- [ ] Confirm you have read the [contribution guidelines](https://github.com/GeoNode/geonode/blob/master/CONTRIBUTING.md) 
- [ ] You have sent a Contribution Licence Agreement (CLA) as necessary (not required for small changes, e.g., fixing typos in the documentation)
- [ ] Make sure the first PR targets the master branch, eventual backports will be managed later. This can be ignored if the PR is fixing an issue that only happens in a specific branch, but not in newer ones.

The following are required only for core and extension modules (they are welcomed, but not required, for contrib modules):
- [ ] There is a ticket in https://github.com/GeoNode/geonode/issues describing the issue/improvement/feature (a notable exemption is, changes not visible to end-users)
- [ ] The issue connected to the PR must have Labels and Milestone assigned
- [ ] PR for bug fixes and small new features are presented as a single commit
- [ ] Commit message must be in the form "[Fixes #<issue_number>] Title of the Issue"
- [ ] New unit tests have been added covering the changes, unless there is an explanation on why the tests are not necessary/implemented
- [ ] This PR passes all existing unit tests (test results will be reported by travis-ci after opening this PR)
- [ ] This PR passes the QA checks: flake8 geonode
- [ ] Commits changing the **settings**, **UI**, **existing user workflows**, or adding **new functionality**, need to include documentation updates

**Submitting the PR does not require you to check all items, but by the time it gets merged, they should be either satisfied or inapplicable.**
