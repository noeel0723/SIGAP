; installer_admin.iss
; Inno Setup script untuk membuat installer SIGAP Admin (.exe)
; Jalankan file ini dengan Inno Setup Compiler

[Setup]
AppName=SIGAP Admin
AppVersion=1.0.0
AppPublisher=SIGAP Team
DefaultDirName={autopf}\SIGAP_Admin
DefaultGroupName=SIGAP Admin
OutputDir=output
OutputBaseFilename=SIGAP_Admin_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; SetupIconFile=..\assets\icons\sigap_icon.ico

[Languages]
Name: "indonesian"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut:"; Flags: unchecked

[Files]
Source: "..\dist\SIGAP_Admin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SIGAP Admin"; Filename: "{app}\SIGAP_Admin.exe"
Name: "{autodesktop}\SIGAP Admin"; Filename: "{app}\SIGAP_Admin.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SIGAP_Admin.exe"; Description: "Jalankan SIGAP Admin"; Flags: nowait postinstall skipifsilent
