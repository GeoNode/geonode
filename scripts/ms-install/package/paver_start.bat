@ECHO off

REM get current directory
set PREFIX=%~dp0

call "%PREFIX%\prefix_env.bat"

cd geonode

paver start
