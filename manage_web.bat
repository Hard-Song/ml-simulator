@echo off
chcp 65001 >nul

:MENU
cls
echo ============================================================
echo           ML Simulator Web Server 管理工具
echo ============================================================
echo.
echo [1] 启动服务器
echo [2] 停止服务器
echo [3] 查看服务器状态
echo [4] 重启服务器
echo [0] 退出
echo.
echo ============================================================
set /p choice="请选择操作 [0-4]: "

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto STATUS
if "%choice%"=="4" goto RESTART
if "%choice%"=="0" goto EXIT
goto MENU

:START
echo.
echo [启动服务器]
echo.

REM 检查是否已经在运行
netstat -ano | findstr :5000 | findstr LISTENING >nul
if %errorlevel%==0 (
    echo [错误] 端口 5000 已被占用！
    echo 请先选择 [2] 停止服务器
    pause
    goto MENU
)

echo 正在启动服务器...
echo.
call start_web.bat
goto MENU

:STOP
echo.
echo [停止服务器]
echo.

netstat -ano | findstr :5000 | findstr LISTENING >nul
if %errorlevel%==1 (
    echo [提示] 服务器未运行
    pause
    goto MENU
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo 找到进程 PID: %%a
    taskkill /PID %%a /F
    echo 成功终止进程 %%a
)

echo.
echo 服务器已停止
pause
goto MENU

:STATUS
echo.
echo [服务器状态]
echo.

netstat -ano | findstr :5000 | findstr LISTENING >nul
if %errorlevel%==1 (
    echo 状态: 未运行
) else (
    echo 状态: 正在运行
    echo.
    echo 占用端口 5000 的进程:
    netstat -ano | findstr :5000 | findstr LISTENING
    echo.
    echo 进程详情:
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        tasklist /FI "PID eq %%a" /FO TABLE /NH
    )
)

echo.
pause
goto MENU

:RESTART
echo.
echo [重启服务器]
echo.

REM 先停止
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    echo 停止旧进程...
    taskkill /PID %%a /F >nul 2>&1
)

REM 等待端口释放
timeout /t 2 /nobreak >nul

REM 启动新进程
echo 启动新进程...
echo.
call start_web.bat
goto MENU

:EXIT
echo.
exit
