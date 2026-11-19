[Setup]
AppName=Idle Alarm Timer
AppVersion=1.0.0
AppPublisher=Jayson Lonzon (Nasci Ph cosmos)
AppPublisherURL=https://github.com/iAmJay-cmd/idle-alarm-timer
DefaultDirName={autopf}\Idle Alarm Timer
DefaultGroupName=Idle Alarm Timer
UninstallDisplayIcon={app}\IdleAlarmTimer.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer_output
OutputBaseFilename=IdleAlarmTimer_Setup_v1.0.0
SetupIconFile=timer_icon.ico
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\IdleAlarmTimer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "timer_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Idle Alarm Timer"; Filename: "{app}\IdleAlarmTimer.exe"; IconFilename: "{app}\timer_icon.ico"
Name: "{group}\Uninstall Idle Alarm Timer"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Idle Alarm Timer"; Filename: "{app}\IdleAlarmTimer.exe"; IconFilename: "{app}\timer_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\IdleAlarmTimer.exe"; Description: "{cm:LaunchProgram,Idle Alarm Timer}"; Flags: nowait postinstall skipifsilent