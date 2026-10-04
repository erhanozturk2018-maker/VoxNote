; Inno Setup script for the VoxNote installer.
;
; Build the application first (pyinstaller VoxNote.spec), then compile this
; script with Inno Setup 6:
;
;     ISCC.exe /DAppVersion=0.4.0 installer\VoxNote.iss
;
; or run tools\build_release.ps1, which does both. The installer is written
; to dist\installer. See docs\RELEASE.md.

#ifndef AppVersion
  #define AppVersion "0.5.1"
#endif
#define AppName "VoxNote"
#define AppExe "VoxNote.exe"
#define AppUrl "https://github.com/erhanozturk2018-maker/VoxNote"

[Setup]
; Do not change AppId between versions: it is how an update finds the
; existing installation.
AppId={{6B0C2F4E-5C0A-4B55-9A77-3E1E1B0C7D21}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Erhan
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Setup
; Installs for the current user only, so no administrator rights are needed.
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile=..\LICENSE
SetupIconFile=..\assets\voxnote.ico
WizardStyle=modern
WizardImageFile=..\assets\installer-side.bmp
WizardSmallImageFile=..\assets\installer-small.bmp
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=..\dist\installer
OutputBaseFilename=VoxNote-Setup-{#AppVersion}
Compression=lzma2/normal
SolidCompression=no
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\VoxNote\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; HotKey: "ctrl+alt+v"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Settings, transcripts, logs and the downloaded speech model belong to the
; user and are intentionally left in place when the application is removed.
