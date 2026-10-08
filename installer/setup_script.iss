; Script generated for PicBoard WebStudio v2.4.0 Inno Setup Installer
#define MyAppName "Minos 사진대지 Studio"
#define MyAppVersion "2.4.0"
#define MyAppPublisher "직책만 부장님을 위한 맞춤형 제작"
#define MyAppURL "https://github.com"
#define MyAppExeName "PicBoard_WebStudio_v2.4.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{C7B6D742-5B4B-4E3E-8164-942C10141FD0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\PicBoard
DisableProgramGroupPage=yes
; Lowest privilege allows non-admin one-click install into local appdata
PrivilegesRequired=lowest
CloseApplications=force
RestartApplications=no
OutputDir=..
OutputBaseFilename=PicBoard_Setup_v2.4.0
SetupIconFile=..\app_icon.ico
UninstallDisplayIcon={app}\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\PicBoard_WebStudio_v2.4\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName} v{#MyAppVersion}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{autoprograms}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} v{#MyAppVersion}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // 이전 실행 중인 프로세스가 있다면 조용히 자동 강제 종료하여 확인 창 원천 차단
  Exec('taskkill.exe', '/F /T /IM PicBoard_WebStudio_v2.4.exe /IM PicBoard_WebStudio_v2.3.exe /IM PicBoard_WebStudio_v2.2.exe /IM PicBoard_WebStudio_v2.1.exe /IM PicBoard_WebStudio_v2.0.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
