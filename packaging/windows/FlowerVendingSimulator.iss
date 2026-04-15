#define AppName "Flower Vending Simulator"
#define AppExeName "FlowerVendingSimulator-Windows-x64.exe"

[Setup]
AppId={{7A24A35B-BF4D-4D74-B5CF-5A8D822B6F92}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\Flower Vending Simulator
DefaultGroupName=Flower Vending Simulator
OutputDir={#OutputDir}
OutputBaseFilename=FlowerVendingSimulator-Setup-Windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion
Source: "{#SourceDocs}\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Flower Vending Simulator"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Flower Vending Simulator"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустить Flower Vending Simulator"; Flags: nowait postinstall skipifsilent
