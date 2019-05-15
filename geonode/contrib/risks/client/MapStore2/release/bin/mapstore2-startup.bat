@echo off
rem -----------------------------------------------------------------------------
rem Startup Script for MapStore2
rem -----------------------------------------------------------------------------

cls
echo Welcome to MapStore2!
echo.
set error=0

set "CURRENT_DIR=%cd%"
set "CATALINA_HOME=%CURRENT_DIR%"

set "EXECUTABLE=%CATALINA_HOME%\bin\catalina.bat"
set CMD_LINE_ARGS=
set CMD_LINE_ARGS=%CMD_LINE_ARGS% %1

rem JAVA_HOME not defined
if "%JAVA_HOME%" == "" goto nativeJava

echo JAVA_HOME: %JAVA_HOME%
echo.

rem No errors
goto run

:nativeJava
  set "JAVA_HOME=%CURRENT_DIR%\jre\win"

rem JAVA_HOME defined incorrectly
:checkJava
  if not exist "%JAVA_HOME%\bin\java.exe" goto badJava
goto run

:badJava
  echo The JAVA_HOME environment variable is not defined correctly.
goto JavaFail

:JavaFail
  echo Java 7 is needed to run MapStore2.
  echo.
  echo Install it from:
  echo    http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1880261.html
  echo.
  set error=1
goto end


:run
  echo Please wait while loading MapStore2...
  echo.
  call "%EXECUTABLE%" start %CMD_LINE_ARGS%
  echo Point you browser to: http://localhost:8082/mapstore
  echo.
  echo Enjoy MapStore2!
goto end


:end
  if %error% == 1 echo Startup of MapStore2 was unsuccessful.
  echo.
  pause
