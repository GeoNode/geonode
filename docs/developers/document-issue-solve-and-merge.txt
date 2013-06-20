

Document: issue report, solve and merge to dev
----------------------------------------------


#. Identify an issue. Bugs, imperfect designs, outdated information, or
inaccurate descriptions are occasionally found on webpage or during data
processing. Successful development of GeoNode web application needs to
solve those issues through a systematic procedure, which will be described
below.

#. Report your issue. Report a new issue in Github. Click on Issues tab (note
the red arrow) and then click New Issue button (the purple arrow).

.. image:: images/new-issue.png

figure 1


#. Create a new branch to work on the issue. Now switch to the geonode folder
on your laptop. Assume that git is already installed; otherwise you can
download it from http://git-scm.com/downloads and follow documentation
to set it up. Once git is set up and the dev branch is in sync with remote
geonode dev branch, you can branch out a branch to specifically deal with
one issue. Say the issue number is 101. So you name a new branch “issue-101”
using the syntax below.
git checkout ‐b issue‐101 

#. Check if you are on the new branch. Normally once you create a new branch,
you will automatically switch to it. But to make sure, you can check which
branch you are by the command below. It will tell you the branch you are
currently working on. git status 

It should look like:

# On branch issue‐101 
#. Fix the bug. Once you are on the designated branch, you can start to solve
the issue. Use vi, gedit or other text edit tools to make changes on the
source code, and save the changes.

#. Commit your changes. Assume you have fixed the bug and tested it well on
your local machine. Before you submit to online repository, there is
another important step: commit your changes to the local repository. That
approach will protect you from losing any change when you switch to another
branch. It permanently saves your changes and will bring them up next time
when you switch back to this branch.
git commit –a –m “your message for this commit” 

#. Push changes to your own remote repository. Now you are confident that
you have solved the problem, and want to merge your contribution to the
main code repository on Github, using the syntax below. This syntax will
allow you to upload changes to your own remote repository. Note that the
remote repository will be a mirror of your local repository so all branches
on your local repository will be copied there. Here you upload to the
issue-101 remote branch. Authentication information may show up and
please type in your username and password if required.
git push origin issue‐101 

#. Make a pull request(PR). Congratulations! You are almost done. The last
step is to make a pull request from the issue-101 branch of your own remote
repository to the main geonode dev branch. You need to do that from Github.
First, make sure you on are the right branch (note the red arrow). By
clicking the Pull Request button (the purple arrow), you are led to a new
page (figure 2) where you need to specify that you are merging to geonode
dev branch (the red arrow) and mention issue #101 (with ‘#’

#. Check travis

#. Check Jenkins
