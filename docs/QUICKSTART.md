# ML Simulator Web 快速启动指南

## 环境准备

### 1. 安装 uv（如果还没安装）

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 启动 Web 服务器

**方法 1: 使用启动脚本（推荐）**

Windows:
```bash
双击 start_web.bat
```

Linux/Mac:
```bash
chmod +x start_web.sh
./start_web.sh
```

**方法 2: 手动启动**

```bash
# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt

# 启动服务器
uv run python app.py
```

## 访问应用

启动成功后，在浏览器中打开：

- **主页（多模型对比）**: http://localhost:5000/
- **学习曲线**: http://localhost:5000/learning_curve（开发中）
- **难度扫描**: http://localhost:5000/difficulty_scan（开发中）

## 功能演示

### 多模型对比

1. **配置任务**
   - 选择任务类型（二分类/多分类/回归）
   - 调整样本量
   - 设置类别分布（可选）

2. **调整难度**
   - 类间可分性：控制正负类区分难度
   - 标签噪声：模拟标签错误
   - 特征噪声：增加特征不确定性
   - 非线性强度：测试模型对非线性适应能力

3. **选择模型**
   - 勾选要对比的模型
   - 支持同时选择多个模型

4. **运行模拟**
   - 点击"运行模拟"按钮
   - 查看表格和图表结果

5. **导出数据**
   - 点击"导出 CSV"下载结果

## 常见问题

### Q: 端口被占用怎么办？
修改 `app.py` 最后一行，将 `port=5000` 改为其他端口。

### Q: 页面显示异常？
清除浏览器缓存后刷新页面（Ctrl+F5）。

### Q: 如何停止服务器？
在命令行窗口按 `Ctrl+C`。

## 项目文件说明

```
mlplot/
├── app.py                    # Flask 后端服务
├── ml_simulator.py           # 核心模拟引擎
├── uv.toml                   # UV 配置（镜像）
├── requirements.txt          # Python 依赖
│
├── templates/                # HTML 模板
│   └── index.html           # 主页
│
├── static/                   # 静态资源
│   ├── css/style.css        # 样式
│   └── js/index.js          # 交互逻辑
│
├── start_web.bat            # Windows 启动脚本
├── start_web.sh             # Linux/Mac 启动脚本
└── test_dependencies.py     # 依赖测试脚本
```

## 技术栈

- **后端**: Flask + Flask-CORS
- **前端**: Bootstrap 5 + Chart.js
- **核心**: ml_simulator（NumPy + Pandas）
- **工具**: uv（Python 包管理）

## 下一步

- [ ] 尝试不同的难度参数组合
- [ ] 对比传统模型与深度模型
- [ ] 模拟不均衡数据场景
- [ ] 分析模型鲁棒性

祝你使用愉快！
