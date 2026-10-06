@echo off
title TJK At Yarisi Yapay Zeka Platformu v2.0
echo ======================================================================
echo   TJK AT YARISI YAPAY ZEKA TAHMIN PLATFORMU BASLATILIYOR...
echo ======================================================================
cd /d "%~dp0"
if exist "dist\TJK_RACING_AI_PRO_v2.exe" (
    start "" "dist\TJK_RACING_AI_PRO_v2.exe"
) else (
    python main.py
)
