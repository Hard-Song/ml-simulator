# PowerShell 停止脚本
# 用法：右键 -> 使用 PowerShell 运行

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "停止 ML Simulator Web Server (端口 5000)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 查找占用端口 5000 的进程
$process = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1

if ($process) {
    $pid = $process.OwningProcess
    Write-Host "找到进程 PID: $pid" -ForegroundColor Yellow

    # 获取进程名称
    $processName = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($processName) {
        Write-Host "进程名称: $($processName.ProcessName)" -ForegroundColor Yellow
    }

    Write-Host "正在终止..." -ForegroundColor Yellow
    Stop-Process -Id $pid -Force
    Write-Host "成功终止进程 $pid" -ForegroundColor Green
} else {
    Write-Host "未找到占用端口 5000 的进程" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "按回车键退出"
