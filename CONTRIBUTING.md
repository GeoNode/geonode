# Contributing

When submitting pull request:

* **Small Contribution / Single Source Code File:** For a small change to a single source file a project committer can review and apply the change on your behalf. This is a quick workaround allowing us to correct spelling mistakes in the documentation, clarify a doc, or accept a very small fix.

  We understand that fixing a single source file may require changes to several test case files to verify the fix addresses its intended problem.

* **Large Contributions / Multiple Files / New Files:** To contribute a new file, or if your change effects several files, sign a [Code Contribution License](https://raw.githubusercontent.com/GeoNode/geonode/master/CLA_INDIVIDUAL.md). It does not take long and you can send it via email.

The process of getting community commit access is as follows:

1. Email the developer list.

   This first step is all about communication. In order to grant commit access the other developers on the project must first know what the intention is. Therefore any developer looking for commit access must first describe what they want to commit (usually a community module), and what it does.

2. Sign up for a GitHub account.

   GeoNode source code is hosted on Github and you’ll need an account in order to access it. You can sign-up [here](https://github.com/signup/).

3. Print, sign, scan and send the contributor agreement
[CLA_INDIVIDUAL](https://raw.githubusercontent.com/GeoNode/geonode/master/CLA_INDIVIDUAL.md).

   Scanned assignment agreement can be emailed info@osgeo.org at OSGeo.

4. Notify the developer list.

   After a developer has signed up on Github they must notify the developer list. A project despot will then add them to the group of GeoNode committers and grant write access to the canonical repository.

5. Fork the canonical GeoNode repository.

   All committers maintain a fork of the GeoNode repository that they work from. Fork the canonical repository into your own account.

6. Configure your local setup

## Pull Requests

Issuing a pull request requires that you [fork the GeoNode git repository](https://github.com/GeoNode/geonode) into
your own account.

Assuming that `origin` points to your GitHub repository then the workflow becomes:

1. Make the change.

```
   git checkout -b my_bugfix master
   git add .
   git commit -m "fixed bug xyz"
```
2. Push the change up to your GitHub repository.
```
   git push origin my_bugfix
```
3. Visit your GitHub repository page and issue the pull request.

4. At this point the core developers will be notified of the pull request and review it at the earliest convenience. Core developers will review the patch and might require changes or improvements to it; it will be up to the submitter to amend the pull request and keep it alive until it gets merged.

> Please be patient, pull requests are often reviewed in spare time so turn-around can be a little slow. If a pull request becomes stale with no feedback from the submitter for a couple of months, it will linked to from a Github issue (to avoid losing the partial work) and then be closed.

## Pull Request Guidelines

The following guidelines are meant to ensure that your pull request is as easy as possible to  review.

* Ensure your IDE/editor is properly configured

  Ensure that your development environment is properly configured for GeoNode development. A common issue is a text editor is configured to use tabs rather than spaces.

* Include only relevant changes

  Ensure the patch only contains changes relevant to the issue you are trying to fix. A common mistake is to include whitespace and formatting changes along with the relevant changes. These changes, while they may seem harmless, make the patch much harder to read.

* Fix one thing at a time

  Do not batch up multiple unrelated changes into a single patch. If you want to fix multiple issues work on them separately and submit separate patches for them.

* Always add a test

  Given a large code base, the large number of external contributors, and the fast evolution of the code base, tests are really the only line of defense against accidental breakage of the contributed functionality. That is why we always demand to have at least one test, it's not a "punishment", but a basic guarantee your changes will still be there, and working, in future releases.

* Referer to a GitHub ticket from the commit message

  Release managers generate a changelog by checking the tickets resolved for a given target version, if there is none, your contribution won't show up. So always create a ticket associated to your commits, and refer to it from your commit message.

* Be patient

  The core developers review community patches in spare time. Be cognizant of this and realize that just as you are contributing your own free time to the project, so is the developer who is reviewing and applying your patch.

* Tips

  Include a test case that shows your patch fixes an issue (or adds new functionality). If you do not include a test case the developer reviewing your work will need to create one.

  [Github Issue](https://github.com/GeoNode/geonode/issues) are used to list your fix in the release notes each release. You can link to the Issue number in your pull request description.

## Commit Guidelines

GeoNode does not have much in the way of strict commit policies. Our current conventions are:

1. **Add copyright headers:**
   * Remember to add a copyright header with the year of creation to any new file. As an example, if you are adding a file in 2016 the copyright header would be:

   ```
   # -*- coding: utf-8 -*-
   #########################################################################
   #
   # Copyright (C) 2019 Open Source Geospatial Foundation - all rights reserved
   #
   # This program is free software: you can redistribute it and/or modify
   # it under the terms of the GNU General Public License as published by
   # the Free Software Foundation, either version 3 of the License, or
   # (at your option) any later version.
   #
   # This program is distributed in the hope that it will be useful,
   # but WITHOUT ANY WARRANTY; without even the implied warranty of
   # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   # GNU General Public License for more details.
   #
   # You should have received a copy of the GNU General Public License
   # along with this program. If not, see <http://www.gnu.org/licenses/>.
   #
   #########################################################################
   ```

   * If you are modifying an existing file that does not have a copyright header, add one as above.

   * Updates to existing files with copyright headers do not require updates to the copyright year.

   * When adding content from another organisation maintain copyright history and original license. Only add Open Source Geospatial Foundation if you have made modifications to the file for GeoNode:

   ```
   # -*- coding: utf-8 -*-
   #########################################################################
   #
   # Copyright (C) 2016 Open Source Geospatial Foundation - all rights reserved
   # Copyright (C) 2014 OpenPlans
   # Copyright (C) 2008-2010 GeoSolutions
   #
   # This program is free software: you can redistribute it and/or modify
   # it under the terms of the GNU General Public License as published by
   # the Free Software Foundation, either version 3 of the License, or
   # (at your option) any later version.
   #
   # This program is distributed in the hope that it will be useful,
   # but WITHOUT ANY WARRANTY; without even the implied warranty of
   # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   # GNU General Public License for more details.
   #
   # You should have received a copy of the GNU General Public License
   # along with this program. If not, see <http://www.gnu.org/licenses/>.
   #
   #########################################################################
   ```

2. **Do not commit large amounts of binary data:** In general do not commit any binary data to the repository. There are cases where it is appropriate like some data for a test case, but in these cases the files should be kept as small as possible.

3. **Do not commit archives or libs, use PyPi instead:** In general never commit a depending library directly into the repository, this is what we use PyPi for. If you have a jar that is not present in any PyPi repositories, ask on the developer list to get it uploaded to one of the project repositories.

4. **Ensure code is properly formatted:** We use Flake8 and PEP-8 to check automatically that the code have been correctly formatted.

