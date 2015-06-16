@ECHO off

REM get current directory
set PREFIX=%~dp0

REM set paths to our standalone
set PATH=%PREFIX%Python27\;%PREFIX%Python27\Scripts\;%PATH%

set LD_LIBRARY_PATH=%PREFIX%Python27\Lib;%LD_LIBRARY_PATH%

set PYTHONPATH=%PREFIX%Python27\Lib;%PREFIX%Python27\Lib\site-packages;%PYTHONPATH%


REM set our other paths while we are at it

set GDAL_LIBRARY_PATH=%PREFIX%Python27\Lib\site-packages\osgeo\gdal111.dll

set GEOS_LIBRARY_PATH=%PREFIX%Python27\Lib\site-packages\osgeo\geos_c.dll
