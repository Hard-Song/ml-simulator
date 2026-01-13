# ML Simulator - 机器学习模型性能模拟与对比工具

一个基于 Web 的机器学习模型性能模拟工具，支持多种任务类型（二分类、多分类、回归），通过调整模型能力和数据难度参数，实时模拟和对比不同模型的性能表现。

## 功能特性

### 核心功能

- **多任务类型支持**
  - 二分类（Binary Classification）
  - 多分类（Multiclass Classification）
  - 回归（Regression）

- **10+ 预定义模型**
  - SVM, Random Forest, LightGBM, DNN
  - CNN, RNN, Transformer
  - Logistic Regression, XGBoost, CatBoost

- **自定义模型**
  - 创建自定义命名模型
  - 独立配置每个模型的能力参数

- **模型能力画像**
  - Bias（偏差）：欠拟合风险
  - Variance（方差）：过拟合风险
  - Capacity（能力）：学习能力上限
  - Noise Tolerance（容错）：抗噪声能力

- **数据难度控制**
  - 类间可分性（Separability）
  - 标签噪声（Label Noise）
  - 特征噪声（Feature Noise）
  - 非线性强度（Nonlinearity）

- **任务特定指标**
  - 二分类：Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, LogLoss
  - 多分类：Accuracy, Macro-F1, Weighted-F1, LogLoss, Top-3 Accuracy
  - 回归：MAE, RMSE, R²

- **交互式可视化**
  - 动态结果表格
  - 多维度对比图表（柱状图、雷达图）
  - 实时参数调整
  - 一键导出 CSV

## 技术栈

### 后端
- **Flask** - Web 框架
- **NumPy** - 数值计算
- **Pandas** - 数据处理

### 前端
- **Bootstrap 5** - UI 框架
- **Chart.js** - 数据可视化
- **Vanilla JavaScript** - 交互逻辑

## 安装与运行

### 环境要求
- Python 3.8+
- uv（推荐的 Python 包管理器）

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/mlplot.git
cd mlplot
```

2. **使用 uv 创建虚拟环境并安装依赖**
```bash
# 如果已安装 uv
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

uv pip install -r requirements.txt
```

3. **启动服务**
```bash
python app.py
```

4. **访问应用**
```
打开浏览器访问：http://localhost:8080
```

## 使用指南

### 1. 配置任务参数

在左侧面板设置：
- 任务类型（二分类/多分类/回归）
- 样本量
- 类别数和分布（多分类任务）
- 学习难度参数

### 2. 配置模型能力

在右侧模型卡片区域：
- 勾选要对比的模型
- 展开卡片调整每个模型的 4 个能力参数
- 点击"添加自定义模型"创建自定义模型

### 3. 运行模拟

点击"▶ 运行模拟"按钮：
- 系统会根据配置生成预测行为
- 计算各模型的性能指标
- 显示对比结果和可视化图表

### 4. 导出结果

点击"📥 导出 CSV"保存模拟结果。

## 项目架构

```
mlplot/
├── app.py                      # Flask 后端服务器
├── ml_simulator.py             # 核心模拟引擎
├── requirements.txt            # Python 依赖
├── uv.toml                     # uv 配置（中国镜像）
├── templates/
│   ├── index.html              # 主页面
│   ├── learning_curve.html     # 学习曲线页面
│   └── difficulty_scan.html    # 难度扫描页面
├── static/
│   ├── css/
│   │   └── style.css           # 样式文件
│   └── js/
│       └── index.js            # 前端交互逻辑
└── README.md                   # 项目说明
```

## 核心原理

### SPEC Driven Development

本项目采用 SPEC（Simulation-based Performance Estimation by Capability）方法：

**核心思想**：不是直接生成指标，而是生成"预测行为"，然后通过指标函数计算真实指标。

**公式**：
```
prediction_score = μ(class, model_capability, data_difficulty) + ε

final_prediction = f(prediction_score, model_variance, noise_tolerance)

metrics = g(final_prediction, true_labels)
```

**优势**：
- 指标之间保持一致性
- 反映真实的模型-数据交互
- 支持细粒度的参数调整

## API 文档

### POST /api/simulate

执行单次模型对比模拟。

**请求体**：
```json
{
  "task_type": "binary",
  "num_samples": 5000,
  "n_classes": 2,
  "models": ["lgbm", "rf", "svm"],
  "difficulty": {
    "separability": 0.7,
    "label_noise": 0.05,
    "feature_noise": 0.1,
    "nonlinearity": 0.3
  },
  "models_config": {
    "lgbm": {
      "bias": 0.3,
      "variance": 0.3,
      "capacity": 0.8,
      "noise_tolerance": 0.6
    }
  }
}
```

**响应**：
```json
{
  "success": true,
  "results": [
    {
      "model": "lgbm",
      "task_type": "binary",
      "accuracy": 0.85,
      "precision": 0.83,
      "recall": 0.87,
      "f1": 0.85,
      "roc_auc": 0.92,
      "pr_auc": 0.91,
      "logloss": 0.42
    }
  ]
}
```

### GET /api/models

获取所有预定义模型及其能力画像。

## 使用场景

1. **教学演示**
   - 展示不同算法在相同数据上的性能差异
   - 可视化 Bias-Variance Tradeoff

2. **算法选型**
   - 快速对比多个候选模型
   - 评估模型在不同数据难度下的表现

3. **参数调优实验**
   - 研究单个参数对性能的影响
   - 设计系统的参数扫描实验

4. **特征工程评估**
   - 评估特征噪声对模型的影响
   - 对比模型的鲁棒性

## 常见问题

### Q: 为什么模拟结果与真实训练不一致？

A: 这是一个基于理论模型的模拟器，目的是展示模型能力参数与数据难度的相对关系，而非精确预测实际训练结果。真实训练还受数据质量、特征工程、超参数调优等多重因素影响。

### Q: 如何理解 4 个能力参数？

A:
- **Bias**：越高越容易欠拟合（对真实分布的预测偏移）
- **Variance**：越高越容易过拟合（对训练数据敏感）
- **Capacity**：越高学习能力越强（能学习更复杂的模式）
- **Noise Tolerance**：越高对噪声越不敏感（更鲁棒）

### Q: 类别分布如何设置？

A: 用逗号分隔的概率值，如 `0.7, 0.3` 表示第一类占 70%，第二类占 30%。留空则默认均衡分布。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License

## 致谢

- Flask Web Framework
- Bootstrap UI Framework
- Chart.js Visualization Library
- NumPy & Pandas for Data Science

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**Made with ❤️ for ML Education and Research**
