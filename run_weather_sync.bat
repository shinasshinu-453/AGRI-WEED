@echo off
cd /d "c:\main project\Main-project-Wheat"
python sync_weather.py >> sync_log.txt 2>&1
echo Sync attempt finished at %date% %time% >> sync_log.txt
