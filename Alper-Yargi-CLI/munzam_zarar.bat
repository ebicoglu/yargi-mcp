@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

rem Kullanim: munzam_zarar.bat ["arama ifadesi"] [cikti.txt] [karar_sayisi]
set "PHRASE=%~1"
if "%PHRASE%"=="" set "PHRASE=munzam zarar"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=%~dp0munzam_zarar_maddeler.txt"
set "N=%~3"
if "%N%"=="" set "N=10"

where yargi >nul 2>nul
if errorlevel 1 (
  echo yargi bulunamadi. Once kurun: uv tool install "%~dp0."
  exit /b 1
)

echo Araniyor: %PHRASE%
yargi articles "\"%PHRASE%\"" -c yargitay -n %N% -o "%OUT%"
if errorlevel 1 exit /b 1
echo Bitti: %OUT%
endlocal
