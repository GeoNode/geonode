;NSIS Modern User Interface
;Start Menu Folder Selection Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "GeoNode 2.4"
  OutFile "Geonode_Dev_2.4.exe"

  ;Default installation folder
  InstallDir "C:\Geonode"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\Geonode" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

;--------------------------------
;Variables

  Var StartMenuFolder

;--------------------------------
;Interface Settings

  !define MUI_ICON ".\Docs\logo.ico"
  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP ".\Docs\logo.png" ; optional
  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE ".\Docs\license.txt"
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Geonode" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
  
  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
  
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section

  SetOutPath "$INSTDIR"
  
  ;Add files
 
  File /r ".\package\*"
  
  ;Store installation folder
  WriteRegStr HKCU "Software\Geonode" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Paver Start.lnk" "$INSTDIR\paver_start.bat" "" "$INSTDIR\logo.ico"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Paver Stop.lnk" "$INSTDIR\paver_stop.bat" "" "$INSTDIR\logo.ico" 
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Django Shell.lnk" "$INSTDIR\django_shell.bat" "" "$INSTDIR\logo.ico" 
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\GeoNode Command.lnk" "$INSTDIR\commandprompt.bat" "" "$INSTDIR\logo.ico" 
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecDummy ${LANG_ENGLISH} "A test section."

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END
 
;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...


  RMDir /r "$INSTDIR"
  
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\$StartMenuFolder\Paver Start.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Paver Stop.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Django Shell.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\GeoNode Command.lnk" 
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  
  DeleteRegKey /ifempty HKCU "Software\Geonode"

SectionEnd