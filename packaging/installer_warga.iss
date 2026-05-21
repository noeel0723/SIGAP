; installer_warga.iss
; Inno Setup script untuk membuat installer SIGAP Warga (.exe)
; Jalankan file ini dengan Inno Setup Compiler

[Setup]
AppName=SIGAP Warga
AppVersion=1.0.0
AppPublisher=SIGAP Team
DefaultDirName={autopf}\SIGAP_Warga
DefaultGroupName=SIGAP Warga
OutputDir=output
OutputBaseFilename=SIGAP_Warga_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; SetupIconFile=..\assets\icons\sigap_icon.ico

[Languages]
Name: "indonesian"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut:"; Flags: unchecked

[Files]
Source: "..\dist\SIGAP_Warga\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SIGAP Warga"; Filename: "{app}\SIGAP_Warga.exe"
Name: "{autodesktop}\SIGAP Warga"; Filename: "{app}\SIGAP_Warga.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SIGAP_Warga.exe"; Description: "Jalankan SIGAP Warga"; Flags: nowait postinstall skipifsilent
