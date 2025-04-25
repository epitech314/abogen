@echo off
setlocal
set "target=%~dp0..\..\python_embedded\Scripts\abogen.exe"
set "icon=%~dp0icon.ico"
set "shortcut=%USERPROFILE%\Desktop\abogen.lnk"
set "shortcutParent=%~dp0..\..\abogen.lnk"

set "create_desktop_shortcut=true"

:parse_args
if "%~1"=="" goto continue
if /i "%~1"=="--no-create-desktop-shortcut" (
    set "create_desktop_shortcut=false"
) else if /i "%~1"=="true" (
    set "create_desktop_shortcut=true"
) else if /i "%~1"=="false" (
    set "create_desktop_shortcut=false"
)
shift
goto parse_args

:continue
if /i "%create_desktop_shortcut%"=="true" (
    echo Creating desktop shortcut...
    :: Try PowerShell method
    powershell -NoProfile -Command ^
        "$s = New-Object -ComObject WScript.Shell; " ^
        "$sc = $s.CreateShortcut('%shortcut%'); " ^
        "$sc.TargetPath = '%target%'; " ^
        "$sc.IconLocation = '%icon%'; " ^
        "$sc.Save()" 
    if errorlevel 1 (
        echo PowerShell method failed. Trying another method...
        goto vbscript
    ) else (
        echo Shortcut created successfully.
        goto createParent
    )

    :vbscript
    echo Creating desktop shortcut...
    echo Set oWS = WScript.CreateObject("WScript.Shell") > "%temp%\create_shortcut.vbs"
    echo Set oLink = oWS.CreateShortcut("%shortcut%") >> "%temp%\create_shortcut.vbs"
    echo oLink.TargetPath = "%target%" >> "%temp%\create_shortcut.vbs"
    echo oLink.IconLocation = "%icon%" >> "%temp%\create_shortcut.vbs"
    echo oLink.Save >> "%temp%\create_shortcut.vbs"
    cscript //nologo "%temp%\create_shortcut.vbs"
    del "%temp%\create_shortcut.vbs"

    if exist "%shortcut%" (
        echo Shortcut created successfully.
    ) else (
        echo Failed to create shortcut.
    )
) else (
    echo Desktop shortcut creation skipped.
)

:createParent
echo Creating shortcut in parent parent folder...
:: Try PowerShell method
powershell -NoProfile -Command ^
    "$s = New-Object -ComObject WScript.Shell; " ^
    "$sc = $s.CreateShortcut('%shortcutParent%'); " ^
    "$sc.TargetPath = '%target%'; " ^
    "$sc.IconLocation = '%icon%'; " ^
    "$sc.Save()" 
if errorlevel 1 (
    echo PowerShell method failed. Trying another method...
    goto vbscriptParent
) else (
    echo Shortcut created successfully.
    goto end
)

:vbscriptParent
echo Creating shortcut in parent parent folder...
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%temp%\create_shortcut_parent.vbs"
echo Set oLink = oWS.CreateShortcut("%shortcutParent%") >> "%temp%\create_shortcut_parent.vbs"
echo oLink.TargetPath = "%target%" >> "%temp%\create_shortcut_parent.vbs"
echo oLink.IconLocation = "%icon%" >> "%temp%\create_shortcut_parent.vbs"
echo oLink.Save >> "%temp%\create_shortcut_parent.vbs"
cscript //nologo "%temp%\create_shortcut_parent.vbs"
del "%temp%\create_shortcut_parent.vbs"

if exist "%shortcutParent%" (
    echo Shortcut created successfully.
) else (
    echo Failed to create shortcut.
)

:end
echo.
exit /b