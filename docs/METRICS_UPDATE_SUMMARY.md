# 指标系统重构总结

## 更新内容

已完全重构指标计算系统，为不同任务类型提供专门的指标集，并确保前后端一致。

## 新指标体系

### 1. 二分类指标 (Binary Classification)

| 指标 | 说明 | 返回字段 |
|------|------|----------|
| Accuracy | 准确率 | `accuracy` |
| Precision | 精确率 | `precision` |
| Recall | 召回率 | `recall` |
| F1 Score | F1分数 | `f1` |
| ROC-AUC | ROC曲线下面积 | `roc_auc` |
| PR-AUC | 精确率-召回率曲线下面积 | `pr_auc` |
| Log Loss | 对数损失 | `logloss` |

**特点**：
- 新增 PR-AUC（适用于不均衡数据）
- 新增 Log Loss（概率校准评估）
- ROC-AUC 改名为 `roc_auc`（更明确）

### 2. 多分类指标 (Multiclass Classification)

| 指标 | 说明 | 返回字段 |
|------|------|----------|
| Accuracy | 准确率 | `accuracy` |
| Macro-F1 | 宏平均F1 | `macro_f1` |
| Weighted-F1 | 加权F1（按样本数） | `weighted_f1` |
| Log Loss | 对数损失 | `logloss` |
| Top-3 Accuracy | Top-3准确率 | `top_3_accuracy` |

**特点**：
- Macro-F1：对所有类别平等对待
- Weighted-F1：按类别样本数加权（适合不均衡数据）
- Top-K 准确率：评估预测是否在前K个中

### 3. 回归指标 (Regression)

| 指标 | 说明 | 返回字段 |
|------|------|----------|
| MAE | 平均绝对误差 | `mae` |
| RMSE | 均方根误差 | `rmse` |
| R² | 决定系数 | `r2` |

**特点**：
- 保持不变，已是标准回归指标

## 代码变更

### 后端 (ml_simulator.py)

#### 新增函数

1. **`_binary_pr_auc(y_true, y_score)`**
   - 计算二分类 PR-AUC
   - 使用梯形法则积分

2. **`_log_loss_binary(y_true, y_prob)`**
   - 计算二分类 Log Loss
   - 防止 log(0) 情况

3. **`_top_k_accuracy(y_true, y_prob, k=3)`**
   - 计算 Top-K 准确率
   - 检查真实标签是否在top-k预测中

4. **`_log_loss_multiclass(y_true, y_prob)`**
   - 计算多分类 Log Loss
   - One-hot 编码 + 对数损失

#### 更新函数

1. **`_precision_recall_f1_multiclass()`**
   - 现在返回 6 个值（包含 weighted 版本）
   - 支持按样本数加权

2. **`compute_classification_metrics()`**
   - 完全重构，根据 `n_classes` 返回不同指标
   - 二分类返回 7 个指标
   - 多分类返回 5 个指标
   - 添加 `task_type` 字段

### 前端 (index.js)

#### 更新函数

1. **`updateTable(results)`**
   - 根据任务类型动态生成表头
   - 自动调整列数和指标显示
   - 处理缺失值（显示 N/A）

2. **`updateCharts(results)`**
   - 根据任务类型动态调整图表
   - 二分类：ROC-AUC vs PR-AUC
   - 多分类：Accuracy vs Macro-F1
   - 回归：MAE vs RMSE
   - 雷达图也相应调整

3. **`initCharts()`**
   - 使用通用图表 ID（chart1, chart2）
   - 支持动态更新标签和数据

### 前端 (index.html)

- 更新表格 ID 为 `resultsTableHead`
- 更新图表 ID 为 `chart1`, `chart2`
- 添加动态标题 `chart1Title`, `chart2Title`

## 测试结果

运行 `test_all_task_types.py` 验证：

```
============================================================
测试 1: 二分类任务
============================================================
二分类指标:
  Accuracy: 0.7216
  Precision: 0.6569
  Recall: 0.9133
  F1: 0.7642
  ROC-AUC: 0.8459
  PR-AUC: 0.8385
  LogLoss: 0.6021
[成功] 所有二分类指标正常

============================================================
测试 2: 多分类任务
============================================================
多分类指标:
  Accuracy: 0.4232
  Macro-F1: 0.4233
  Weighted-F1: 0.4230
  LogLoss: 1.4277
  Top-3 Accuracy: 0.8072
[成功] 所有多分类指标正常

============================================================
测试 3: 回归任务
============================================================
回归指标:
  MAE: 0.3088
  RMSE: 0.3967
  R2: 0.8449
[成功] 所有回归指标正常

============================================================
测试 4: 不均衡多分类任务
============================================================
对比:
  Macro-F1: 0.4142
  Weighted-F1: 0.5164
  差异: 0.1022
  [符合预期] Weighted-F1 > Macro-F1（长尾分布）
[成功] 不均衡多分类指标正常
```

## 前后端一致性

### API 返回格式示例

#### 二分类
```json
{
  "model": "lgbm",
  "task_type": "binary",
  "accuracy": 0.7216,
  "precision": 0.6569,
  "recall": 0.9133,
  "f1": 0.7642,
  "roc_auc": 0.8459,
  "pr_auc": 0.8385,
  "logloss": 0.6021
}
```

#### 多分类
```json
{
  "model": "rf",
  "task_type": "multiclass",
  "accuracy": 0.4232,
  "macro_f1": 0.4233,
  "weighted_f1": 0.4230,
  "logloss": 1.4277,
  "top_3_accuracy": 0.8072
}
```

#### 回归
```json
{
  "model": "dnn",
  "mae": 0.3088,
  "rmse": 0.3967,
  "r2": 0.8449
}
```

### 前端表格显示

| 任务类型 | 表头 | 数量 |
|----------|------|------|
| 二分类 | 模型, 准确率, Precision, Recall, F1, ROC-AUC, PR-AUC, LogLoss | 8列 |
| 多分类 | 模型, 准确率, Macro-F1, Weighted-F1, LogLoss, Top-3 Acc | 6列 |
| 回归 | 模型, MAE, RMSE, R² | 4列 |

### 前端图表

| 任务类型 | 图表1 | 图表2 | 雷达图 |
|----------|-------|-------|--------|
| 二分类 | ROC-AUC | PR-AUC | 6维指标 |
| 多分类 | Accuracy | Macro-F1 | 5维指标 |
| 回归 | MAE | RMSE | 3维指标 |

## 新增指标的意义

### PR-AUC vs ROC-AUC

- **ROC-AUC**：适用于均衡数据
- **PR-AUC**：对不均衡数据更敏感
- 在极端不均衡（如 1:99）时，PR-AUC 更能反映真实性能

### Weighted-F1 vs Macro-F1

- **Macro-F1**：所有类别平等
- **Weighted-F1**：按样本数加权
- 在不均衡数据中，Weighted-F1 通常 > Macro-F1

### Top-K Accuracy

- **Top-1**：传统准确率
- **Top-K**：真实标签在前K个预测中即算正确
- 更适合推荐系统、图像检索等场景

## 向后兼容性

### 破坏性变更

1. **字段名变更**
   - `auc` → `roc_auc` (二分类)
   - `auc_ovr_macro` 已移除
   - `macro_precision`, `macro_recall` 已移除

2. **返回结构变更**
   - 多分类不再返回 `macro_precision`, `macro_recall`
   - 改为返回 `macro_f1`, `weighted_f1`

### 迁移指南

如果你有依赖旧字段的代码：

```python
# 旧代码
auc = metrics['auc']  # 二分类
auc_macro = metrics['auc_ovr_macro']  # 多分类

# 新代码
if metrics.get('task_type') == 'binary':
    auc = metrics['roc_auc']
elif metrics.get('task_type') == 'multiclass':
    # 多分类不再提供单一AUC
    # 如需AUC，可计算macro average
    pass
```

## 未来改进

- [ ] 添加更多PR曲线相关指标（如AP@K）
- [ ] 支持自定义K值的Top-K准确率
- [ ] 添加更多回归指标（如MAPE, RMSLE）
- [ ] 支持类别级别的详细指标（混淆矩阵等）

## 相关文件

- `ml_simulator.py` - 核心指标计算
- `templates/index.html` - 前端表格和图表
- `static/js/index.js` - 前端交互逻辑
- `test_all_task_types.py` - 测试脚本

## 使用建议

### 选择合适的指标

**二分类**：
- 均衡数据：Accuracy, ROC-AUC
- 不均衡数据：PR-AUC, F1, LogLoss
- 概率预测：LogLoss

**多分类**：
- 均衡数据：Accuracy, Macro-F1
- 不均衡数据：Weighted-F1, LogLoss
- 推荐：Top-K Accuracy

**回归**：
- 综合评估：RMSE, R²
- 对异常值敏感：MAE
- 模型拟合：R²
