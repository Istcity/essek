@echo off
chcp 65001 > nul
title TJK AI At Yarisi Tahmin Platformu
echo ==========================================================
echo 🏇 TJK AI At Yarisi Tahmin ve Analiz Platformu Baslatiliyor...
echo 🌐 Web Arayuzu: http://localhost:8080
echo 📱 iOS Safari: Ana Ekrana Ekle Destekli
echo ==========================================================
python backend\app.py 8080
pause
