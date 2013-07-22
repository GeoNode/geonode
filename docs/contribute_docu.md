
How to contribute to GeoNode Documentation
==========================================


If you feel like adding or changing something in the GeoNode documentation you are very welcome to do so. The documentation always needs improvement as the development of the software is going quite fast.

In order to be able to contribute to GeoNode documentation the following steps have to be done:

* Create an account on GitHub
* Fork our repository
* Edit the files in the */docs* directory
* Make pull requests


In the following part the steps will be explained more detailed.

Create an account on GitHub
---------------------------

The first step for you will be to create an account on GitHub. Just go to https://github.com/, find a username that suits you, enter your email and a password and hit Sign up for GitHub. 
Now you've signed in, you can type *geonode* into the searching area at the top of the website. On top of the search results you will find the repository *GeoNode/geonode*. By clicking on it you will be entering the repository and will be able to see all the folders and files that are needed for geonode. 
The files needed for the documentation can be found in */docs*. 

Fork a repository
------------------

In order to make changes to these files, you have to first fork this repository. On the top of the website you should be able to see the following:
  >> picture
Is this necessary??
Now just click the Fork button. You have now successfully forked the geonode repository. (But until now it only exists on GitHub and not on your local machine! In order to be able to work on the project on your local machine you have to clone it first. To do so, open a terminal and go to the folder where you want the project to be. 

To clone your fork of the repository into the current directory type the following line into your terminal

       git clone https://github.com/GeoNode/geonode.git

Now change the active directory to the newly cloned geonode directory using

       cd geonode
       
To keep track of the original repository (the geonode repository where you forked from), you need to add a remote named ``upstream``. Therefore type

       git remote add upstream https://github.com/GeoNode/geonode.git
       
By typing

       git fetch upstream
       
changes not present in your local repository will be pulled in without modifying your files.)	

If you want to read more about how to fork a repository go to https://help.github.com/articles/fork-a-repo.


Edit files
----------

To make some changes to already exiting files or to create new files, go to your GitHub account. Under *repositories* you will find the geonode repository that you have forked. Click on it and you will again see all the folders and files geonode needs. 

	>> picture

Click on the folder *docs* and search for the file that you want to edit. If you found it (we now suggest you were looking for the file *index.txt*), click on it and you will be able to see the content of this file.

	>> picture

To make changes to this file, hit the button edit on the right top.
	>> picture …

....some text..... By hitting the *preview* button you will be able to see how it is going to look like. In order to save your changes, click on *Commit Changes* at the bottom of the site. Now you've saved the changes in your repository, but the original geonode repository still doesn't know anything about that!
In order to tell them that you have made some changes you have to send a *pull request* (as descriped below).


**Create a new folder/file**
If you want to add a completely new issue to the documentation, you have to create a new file (and maybe even folder).
Here you can subdirect to existing folders and files or create new ones.

  >> picture

Type the name of the folder you want to create, e.g new_docs, followed by '/'. 

  >> picture

To create a new file in this folder just type *filename.md* into the box and hit enter. Now the same black box will appear where you can put your contents in. To save it, hit the green *Commit Changes* button at the bottom.

A short example on how to manage this is given here http://i.stack.imgur.com/n3Wg3.gif.

**Create a branch**
If you are planning bigger changes on the structure of the documentation it is recommended to create a new branch and make your edits here. 
A new branch can be created by clicking on the button branch: master as you can see in the following picture. 

>> picture

Just type the name of your new branch, hit enter and your branch will be created.

*Remark*: Before you start editing make sure that you are in the right branch!



Pull Request
------------

If you are done with your changes, you can send a pull request. This means, that you let the core developers know that you have done some changes and you would like them to review. They can hit accept and your changes will go in to the main line.
