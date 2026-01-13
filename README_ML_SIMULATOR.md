# ML Simulator - 机器学习模型性能模拟框架

一个基于 SPEC Driven Development 设计的机器学习结果模拟工具，能够生成逼真的模型预测行为并计算真实指标。

## 核心设计原则

> **指标不是直接生成的，而是"预测行为 + 真实标签 → 指标函数"的自然结果**

- ❌ 不直接生成 Recall / AUC 数值
- ✅ 生成 **模型预测分布**（score / prob / logit）
- ✅ 用真实指标计算逻辑推导结果
- ✅ 所有异常现象（高 AUC 低 Recall、PRC 崩塌、过拟合）都能自然出现

## 主要特性

### 1. 多任务类型支持
- **二分类**：ROC-AUC, PR-AUC, Recall, Precision, F1
- **多分类**：Macro/Micro F1, Top-K Acc, One-vs-Rest AUC
- **回归**：RMSE, MAE, R²

### 2. 学习难度建模
通过多个维度控制数据可学习程度：
- `separability`：类间可分性
- `label_noise`：标签翻转率
- `feature_noise`：特征噪声
- `nonlinearity`：非线性强度
- `spurious_correlation`：伪相关性

### 3. 模型行为模拟
预定义了10种常用模型的能力画像：
- 传统模型：`svm`, `rf`, `logreg`, `nb`, `dt`
- 集成模型：`lgbm`, `xgboost`, `catboost`
- 深度模型：`dnn`, `cnn`, `rnn`, `transformer`

每个模型有不同的：
- 偏差（bias）与方差（variance）
- 表达能力上限（capacity）
- 对难度因子的敏感度

### 4. 真实现象模拟
- 高 AUC 但低 Recall
- PRC 崩塌（极端类别不均衡）
- 过拟合（train/test 差异）
- Transformer 小数据翻车
- 线性模型在非线性任务上饱和

## 快速开始

### 基础使用

```python
from ml_simulator import (
    TaskConfig, DifficultyConfig, MLSimulator, TaskType
)

# 1. 配置任务
task_config = TaskConfig(
    task_type=TaskType.BINARY,
    num_samples=5000,
    n_classes=2,
    random_state=42,
)

# 2. 配置难度
difficulty = DifficultyConfig(
    separability=0.7,
    label_noise=0.05,
    feature_noise=0.1,
)

# 3. 创建模拟器
simulator = MLSimulator(
    task_config=task_config,
    difficulty=difficulty,
    model_profile="lgbm",  # 或使用预定义模型
)

# 4. 运行模拟
metrics = simulator.simulate()
print(f"Accuracy: {metrics['accuracy']:.4f}")
print(f"AUC: {metrics['auc']:.4f}")
```

### 多模型对比

```python
from ml_simulator import compare_models

models = ["logreg", "rf", "lgbm", "dnn"]
results = compare_models(
    task_config=task_config,
    difficulty=difficulty,
    model_names=models,
)
print(results)
```

### 学习曲线模拟

```python
from ml_simulator import simulate_learning_curve
import numpy as np

df = simulate_learning_curve(
    model_name="lgbm",
    task_config=task_config,
    difficulty=difficulty,
    train_sizes=np.linspace(0.1, 1.0, 10),
    acc_10=0.6,   # 10%数据时的准确率
    acc_100=0.85, # 100%数据时的准确率
)
```

### 难度扫描分析

```python
from ml_simulator import scan_difficulty

# 扫描类间可分性对性能的影响
df = scan_difficulty(
    task_config=task_config,
    model_name="lgbm",
    difficulty_param="separability",
    difficulty_values=np.linspace(0.1, 0.9, 9),
    n_runs=5,  # 每个点运行5次取平均
)
```

## 高级用法

### 不均衡分类

```python
task_config = TaskConfig(
    task_type=TaskType.BINARY,
    num_samples=10000,
    n_classes=2,
    label_distribution=[0.9, 0.1],  # 90% 负类, 10% 正类
)
```

### 多分类 + 长尾分布

```python
task_config = TaskConfig(
    task_type=TaskType.MULTICLASS,
    num_samples=10000,
    n_classes=5,
    label_distribution=[0.5, 0.25, 0.15, 0.07, 0.03],  # 长尾
)
```

### 回归任务

```python
from ml_simulator import RegressionConfig

task_config = TaskConfig(
    task_type=TaskType.REGRESSION,
    num_samples=3000,
)

difficulty = DifficultyConfig(
    separability=0.6,
    feature_noise=0.2,
)

reg_config = RegressionConfig(
    function_complexity=0.7,
    noise_level=0.3,
    heteroscedastic=True,  # 异方差
)

simulator = MLSimulator(
    task_config=task_config,
    difficulty=difficulty,
    model_profile="dnn",
    reg_config=reg_config,
)
```

### 自定义模型画像

```python
from ml_simulator import ModelProfile

custom_profile = ModelProfile(
    bias=0.4,
    variance=0.5,
    capacity=0.8,
    noise_tolerance=0.6,
    separability_sensitivity=1.0,
    nonlinearity_sensitivity=0.8,
)

simulator = MLSimulator(
    task_config=task_config,
    difficulty=difficulty,
    model_profile=custom_profile,  # 直接传入自定义画像
)
```

## 文件结构

```
mlplot/
├── ml_simulator.py          # 核心框架
├── example_ml_simulator.py  # 使用示例（7个场景）
├── test_ml_simulator.py     # 测试套件（9个测试）
└── README_ML_SIMULATOR.md   # 本文档
```

## 运行示例和测试

### 运行示例

```bash
python example_ml_simulator.py
```

示例包括：
1. 基础二分类模拟
2. 多分类 + 类别不均衡
3. 学习曲线模拟
4. 难度扫描
5. 回归任务模拟
6. 特殊场景：高AUC但低Recall
7. 模拟过拟合现象

### 运行测试

```bash
python test_ml_simulator.py
```

测试覆盖：
- 基础二分类、多分类、回归
- 不均衡分类
- 多模型对比
- 学习曲线
- 难度扫描
- 逻辑验证（高可分性→高AUC、高噪声→低性能）

## 与 simulate.py 的对比

| 特性 | simulate.py | ml_simulator.py |
|------|-------------|-----------------|
| 设计理念 | 基于目标准确率生成 | 基于预测行为生成 |
| 难度控制 | 单一参数 | 多维度难度向量 |
| 模型差异 | 仅acc_10/acc_100 | 完整的能力画像 |
| 任务支持 | 分类 | 分类 + 回归 |
| 真实现象 | 部分支持 | 完整支持 |
| 可扩展性 | 有限 | 高度可配置 |

## 设计哲学详解

### 为什么不直接生成指标？

直接生成AUC=0.85会导致：
- ❌ 无法保证与其他指标的一致性
- ❌ 无法模拟"奇怪但真实"的现象
- ❌ 难以验证结果的合理性

### 我们的方案

生成预测分布 → 真实指标计算 → 自然出现各种现象

例如：
- `separability` ↑ ⇒ 正负类score分布分离 ⇒ AUC ↑
- `label_noise` ↑ ⇒ 部分样本永远学不会 ⇒ Recall ↓
- `imbalance` ↑ ⇒ PRC比ROC更敏感

### 模型差异的真实性

不同模型有不同的参数：
- **SVM**：低方差，对separability敏感，对nonlinearity不敏感
- **RF**：抗噪声，概率不校准
- **Transformer**：高容量高方差，小样本不稳定

这些差异会导致：
- 线性模型在非线性任务上提前饱和
- Transformer小数据时翻车
- 深度模型容易过拟合

## 常见问题

### Q: 如何模拟特定的AUC值？

A: 不直接控制AUC，而是调整`separability`等难度参数，通过多次实验找到对应的参数值。

### Q: 为什么有时AUC高但Recall低？

A: 这是真实现象！通过以下配置可以模拟：
```python
# 极度不均衡 + 高可分性 + 标签噪声
task_config = TaskConfig(
    label_distribution=[0.95, 0.05],
)
difficulty = DifficultyConfig(
    separability=0.8,  # 高AUC
    label_noise=0.15,   # 低Recall
)
```

### Q: 如何模拟过拟合？

A: 使用高容量高方差模型（如DNN），并让训练集难度远低于测试集：
```python
# 训练集：低难度
difficulty_train = DifficultyConfig(separability=0.8, label_noise=0.02)
# 测试集：高难度
difficulty_test = DifficultyConfig(separability=0.6, label_noise=0.1)
```

## 贡献

欢迎提交问题和改进建议！

## 许可

MIT License
