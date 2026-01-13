#!/bin/bash

echo "============================================================"
echo "ML Simulator Web Server - 启动脚本"
echo "============================================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "[提示] 虚拟环境不存在，正在创建..."
    uv venv
    echo "[完成] 虚拟环境创建完成"
fi

# 安装/更新依赖
echo "[提示] 检查依赖..."
uv pip install -q -r requirements.txt

# 启动服务器
echo ""
echo "============================================================"
echo "服务器即将启动..."
echo ""
echo "访问地址:"
echo "  主页: http://localhost:5000/"
echo "  学习曲线: http://localhost:5000/learning_curve"
echo "  难度扫描: http://localhost:5000/difficulty_scan"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "============================================================"
echo ""

uv run python app.py
