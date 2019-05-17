## Pull request guidelines

Your pull request must:

 * Follow MapStore 2's coding style.

 * The new components have to be tested.

 * Pass the integration tests run automatically by the Travis Continuous
   Integration system.

 * Address a single issue or add a single item of functionality.

 * Contain a clean history of small, incremental, logically separate commits,
   with no merge commits.

 * Use clear commit messages.

 * Be possible to merge automatically.


### Follow MapStore 2's coding style

MapStore 2 follows a strict coding style, enforced by [ESLint](http://eslint.org/) rules.

The set of used rules can be found in the [.eslintrc](https://github.com/geosolutions-it/MapStore2/blob/master/.eslintrc) file, in the root folder of the project.

You can run the linter locally on your machine before committing using the `lint`
target:

    $ npm lint

In addition, take care of adding the standard file header in each javascript / css added file, and update copyright years in modified ones.

This is the standard file header:

```
/*
 * Copyright <year>, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
```

### The components have to be tested

It is strongly recommended that you run

    $ npm test

before every commit.  This will catch many problems quickly, and it is much
faster than waiting for the Travis CI integration tests to run.

The `test` build target runs a number of quick tests on your code.  

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
