@echo off
chcp 65001 >nul
echo ============================================================
echo 停止 ML Simulator Web Server (端口 5000)
echo ============================================================
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo 找到进程 PID: %%a
    echo 正在终止...
    taskkill /PID %%a /F
    echo.
)

echo ============================================================
echo 完成！
echo ============================================================
pause
