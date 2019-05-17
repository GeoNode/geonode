Contributing to MapStore 2
==========================

 1. [Getting Involved](#getting-involved)
 2. [Reporting Bugs](#reporting-bugs)
 3. [Contributing Code](#contributing-code)
 4. [Improving Documentation](#improving-documentation)

## Getting Involved

There are several ways you can contribute to MapStore 2 development.
If you are a developer, you can contribute new features and bug fixes, using pull requests.
But you can also help by discovering and [reporting bugs](#reporting-bugs);
[improving documentation](#improving-documentation);
helping others on the [MapStore users mailing list](https://groups.google.com/d/forum/mapstore-users)
and [GitHub issues](https://github.com/geosolutions-it/MapStore2/issues).

## Reporting Bugs

Before reporting a bug on the project's [issues page](https://github.com/geosolutions-it/MapStore2/issues),
first make sure that your issue is caused by MapStore 2, not your application code
(e.g. passing incorrect arguments to methods, etc.).
Second, search the already reported issues for similar cases,
and if it's already reported, just add any additional details in the comments.

After you've made sure that you've found a new MapStore 2 bug,
here are some tips for creating a helpful report that will make fixing it much easier and quicker:

 * Write a **descriptive, specific title**. Bad: *Map does not show*. Good: *Doing X in IE9 causes Z*.
 * Include **browser, OS and MapStore 2 version** info in the description.
 * Create a **simple test case** that demonstrates the bug (e.g. using [JSFiddle](http://jsfiddle.net/) or [JS Bin](http://jsbin.com/)).
 * Check whether the bug can be reproduced in **other browsers**.
 * Check if the bug occurs in the stable version, master, or both.
 * *Bonus tip:* if the bug only appears in the master version but the stable version is fine,
   use `git bisect` to find the exact commit that introduced the bug.

If you just want some help with your project,
try asking [on the MapStore users mailing list](https://groups.google.com/d/forum/mapstore-users) instead.

## Contributing Code

### Considerations for Accepting Patches

While we happily accept patches, we're also committed to quality.
So bugfixes, performance optimizations and small improvements that don't add a lot of code
are much more likely to get accepted quickly.

Before sending a pull request with a new feature, check if it's been discussed before already
(either on [GitHub issues](https://github.com/geosolutions-it/MapStore2/issues)
or [on the MapStore developers mailing list](https://groups.google.com/d/forum/mapstore-developers)),
and ask yourself two questions:

 1. Are you sure that this new feature is important enough to justify its presence in the MapStore 2 core?
    Or will it look better as a plugin in a separate repository?
 2. Is it written in a simple, concise way that doesn't add bulk to the codebase?

If your feature did get merged into master,
please consider submitting another pull request with the corresponding [documentation update](#improving-documentation).

### Making Changes to MapStore 2 Source

If you're not yet familiar with the way GitHub works (forking, pull requests, etc.),
be sure to check out the awesome [article about forking](https://help.github.com/articles/fork-a-repo)
on the GitHub Help website &mdash; it will get you started quickly.

You should always write each batch of changes (feature, bugfix, etc.) in **its own topic branch**.
Please do not commit to the `master` branch, or your unrelated changes will go into the same pull request.

### Pull request guidelines

Your pull request must:

 * Follow MapStore 2's coding style.

 * Pass the integration tests run automatically by the Travis Continuous
   Integration system.

 * Address a single issue or add a single item of functionality. (Start the pull request title with the addressed issues if in case)

 * Contain a clean history of small, incremental, logically separate commits,
   with no merge commits.

 * Use clear commit messages.

 * Be possible to merge automatically.


### The `test` and `lint` build targets

It is strongly recommended that you run

    $ npm test

    $ npm run lint

before every commit.  This will catch many problems quickly, and it is much
faster than waiting for the Travis CI integration tests to run.

The `test` build target runs a number of quick tests on your code.  

The `lint` build target runs ESLint checks on your code.  


### File Naming Conventions

The test files should in a folder named `__tests__` in the module folder.

If you are testing a specific component follow the following convention:

* Component: `MyComponent.jsx`
* Test File: `MyComponent-test.jsx`

### Follow MapStore 2's coding style

MapStore 2 follows a strict coding style, enforced by [ESLint](http://eslint.org/) rules.

The set of used rules can be found in the [.eslintrc](https://github.com/geosolutions-it/MapStore2/blob/master/.eslintrc) file, in the root folder of the project.

You can run the linter locally on your machine before committing using the `lint`
target:

    $ npm lint

In addition, take care of adding the standard file header in each javascript / css added file, and update copyright years in modified ones.

This is the standard file header:

```
/**
 * Copyright <year>, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
```

### Configure your editor

If possible, configure your editor to follow the coding conventions of the
library.  A `.editorconfig` file is included at the root of the repository that
can be used to configure whitespace and charset handling in your editor.  See
that file for a description of the conventions.  The [EditorConfig](
http://editorconfig.org/#download) site links to plugins for various editors.

### Pass the integration tests run automatically by the Travis CI system

The integration tests contain a number of automated checks to ensure that the
code follows the MapStore 2 style and does not break tests or examples.  You
can run the integration tests locally using the `test` target:

    $ npm test


### Address a single issue or add a single item of functionality

Please submit separate pull requests for separate issues.  This allows each to
be reviewed on its own merits.


### Contain a clean history of small, incremental, logically separate commits, with no merge commits

The commit history explains to the reviewer the series of modifications to the
code that you have made and breaks the overall contribution into a series of
easily-understandable chunks.  Any individual commit should not add more than
one new class or one new function.  Do not submit commits that change thousands
of lines or that contain more than one distinct logical change.  Trivial
commits, e.g. to fix lint errors, should be merged into the commit that
introduced the error.  See the [Atomic Commit Convention on Wikipedia](http://en.wikipedia.org/wiki/Atomic_commit#Atomic_Commit_Convention) for more detail.

`git apply --patch` and `git rebase` can help you create a clean commit
history.
[Reviewboard.org](http://www.reviewboard.org/docs/codebase/dev/git/clean-commits/)
and [Pro GIT](http://git-scm.com/book/en/Git-Tools-Rewriting-History) have
explain how to use them.


### Use clear commit messages

Commit messages should be short, begin with a verb in the imperative, and
contain no trailing punctuation. We follow
http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
for the formatting of commit messages.

Git commit message should look like:

    Header line: explaining the commit in one line

    Body of commit message is a few lines of text, explaining things
    in more detail, possibly giving some background about the issue
    being fixed, etc etc.

    The body of the commit message can be several paragraphs, and
    please do proper word-wrap and keep columns shorter than about
    74 characters or so. That way "git log" will show things
    nicely even when it's indented.

    Further paragraphs come after blank lines.

Please keep the header line short, no more than 50 characters.

### Be possible to merge automatically

Occasionally other changes to `master` might mean that your pull request cannot
be merged automatically.  In this case you may need to rebase your branch on a
more recent `master`, resolve any conflicts, and `git push --force` to update
your branch so that it can be merged automatically.

## Improving Documentation

TBD

## Thank You

At the end, however you decide to contribute to the project, your help is very
welcome and we would like to thank you for doing it.
