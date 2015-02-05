Instructions for building Windows Install Package
============

It is best to do this in a clean install of Windows, so your working python install is not disturbed.


Requirements for Build
------------
 
 - [NSIS](http://prdownloads.sourceforge.net/nsis/nsis-2.46-setup.exe?download)
 - Git
 - Python 2.7.x 32 bit - Fresh install with pip installed and located in the PATH environment variable 


Requirements to Install Package
-------------
 
 - Installed Java
 - Python 2.7.x 32 bit


Step by Step
------------

 - Copy the "ms-installer" directory to another location outside of Geonode
 - In the new ms-installer directory, copy the geonode repo to the package folder
   - It must be named "geonode" and is case sensitive  
 - Use this geonode directory to do the [Windows Quick Install Instructions](http://geonode.readthedocs.org/en/master/tutorials/admin/install/quick_install.html)
   - Do not use the virtualenv.  Just use your standard Python
   - Test the install with paver start.  If all is well move, to the next step.  Otherwise, troubleshoot the error before proceeding.
 - Now copy the whole python directory (C:\Python27) to the package folder alongside geonode
 
```
  --package
    |
    --geonode
    |
    --Python27
```
 - The batch files should be working now from your package/Python27 directory
 - Finally, right click on the Geonode.nsi file and click "Compile NSIS Script".  The output will be Geonode_Dev_2.4.exe in the same folder.
