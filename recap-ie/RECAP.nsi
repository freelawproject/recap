; RECAP.nsi
;
; TODO: Add script to detect .NET directory before running `RegAsm.exe`.

;--------------------------------

; The name of the installer
Name "RECAP"

; The file to write
OutFile "RECAP.exe"

; The default installation directory
InstallDir $PROGRAMFILES\RECAP

; Request application privileges
RequestExecutionLevel user

;--------------------------------

; Pages

Page directory
Page instfiles

;--------------------------------

; The stuff to install
Section "" ; No components page, name is not important

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put file there
  File RECAP.dll

SectionEnd

; Exec 'RegAsm.exe /s /c "$INSTDIR\RECAP.dll"'
; Exec 'RegAsm.exe /s /u "$INSTDIR\RECAP.dll"'
