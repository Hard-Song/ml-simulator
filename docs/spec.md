下面我给你一份 **SPEC Driven Development 级别** 的设计方案。你照着它，几乎可以直接拆任务给自己或别人实现。

---

# 模型性能模拟与指标计算框架设计（SPEC）

## 0. 设计哲学（非常重要）

**核心原则**：

> 指标不是直接生成的，而是“预测行为 + 真实标签 → 指标函数”的自然结果。

所以：

* ❌ 不直接生成 Recall / AUC 数值
* ✅ 生成 **模型预测分布**（score / prob / logit / ranking）
* ✅ 用真实指标计算逻辑推导结果
* ✅ 所有异常现象（高 AUC 低 Recall、PRC 崩塌、过拟合）都能自然出现

你做的不是“假指标”，而是**可验证的指标生成机制**。

---

## 1. 系统总体结构

```text
┌──────────────┐
│ Task Config  │  ← 任务类型 / 类别数 / 样本量 / 标签比例
└──────┬───────┘
       ↓
┌──────────────┐
│ Difficulty   │  ← 学习难度 / 噪声 / 类间可分性 / 长尾
│ Controller   │
└──────┬───────┘
       ↓
┌──────────────┐
│ Model        │  ← SVM / RF / LGBM / DNN / CNN / RNN / Transformer
│ Behavior     │     （不是训练，是“行为模拟”）
└──────┬───────┘
       ↓
┌──────────────┐
│ Prediction   │  ← logits / prob / regression output
│ Generator    │
└──────┬───────┘
       ↓
┌──────────────┐
│ Metric       │  ← Accuracy / Recall / ROC / PRC / RMSE …
│ Calculator   │
└──────────────┘
```

---

## 2. 任务维度设计（Task Spec）

### 2.1 支持任务类型

| 任务  | 输出形式                     | 关键指标                               |
| --- | ------------------------ | ---------------------------------- |
| 二分类 | score ∈ ℝ / prob ∈ [0,1] | ROC-AUC, PR-AUC, Recall, Precision |
| 多分类 | logits ∈ ℝ^K             | Macro / Micro F1, Top-K Acc        |
| 回归  | ŷ ∈ ℝ                   | RMSE, MAE, R²                      |

---

### 2.2 样本与标签控制

**Config 示例**

```yaml
num_samples: 10000
label_distribution:
  type: imbalanced
  ratios: [0.9, 0.1]     # 二分类
```

支持：

* 均衡 / 极端不均衡
* 多分类长尾（Zipf / Pareto）
* 回归目标带异方差

---

## 3. 数据“学习难度”建模（关键）

你不生成数据，但你要生成 **“可被学习的程度”**。

### 3.1 难度不是一个数，而是一个向量

```yaml
difficulty:
  separability: 0.6        # 类间可分性
  label_noise: 0.1         # 标签翻转率
  feature_noise: 0.2       # 输入噪声
  nonlinearity: 0.7        # 非线性强度
  spurious_correlation: 0.3
```

---

### 3.2 概念解释（贴近真实）

* **separability**
  → 正负样本 score 均值差距
* **label_noise**
  → 一部分样本“永远学不会”
* **feature_noise**
  → 模型置信度下降（score 方差变大）
* **nonlinearity**
  → 线性模型天花板
* **spurious correlation**
  → 传统模型好，深度模型翻车（或反之）

---

## 4. 模型行为模拟（Model Behavior Layer）

### 4.1 关键思想

> 每个模型 = 一个 **概率生成器**，而不是一个训练器。

你要模拟的是：

* 偏差（bias）
* 方差（variance）
* 表达能力上限
* 对噪声的鲁棒性

---

### 4.2 模型能力参数化

| 模型          | 能力画像                           |
| ----------- | ------------------------------ |
| SVM         | 低方差 / 中等偏差 / 对 separability 敏感 |
| RF          | 抗噪声 / 概率不校准                    |
| LGBM        | 高非线性 / 对特征噪声敏感                 |
| DNN         | 高容量 / 易过拟合                     |
| CNN         | 局部模式强 / 全局弱                    |
| RNN         | 时序依赖 / 长程衰减                    |
| Transformer | 长程建模 / 小样本不稳                   |

---

### 4.3 统一预测生成公式（分类）

```text
score = μ(class, model, difficulty)
      + ε_sample
      + ε_model
```

其中：

* μ 控制“学到的信号”
* ε_sample：样本噪声
* ε_model：模型不稳定性

再过：

```text
prob = sigmoid(score)
```

---

### 4.4 让“奇怪但真实”的现象自然出现

| 现象                | 设计方式                   |
| ----------------- | ---------------------- |
| AUC 高但 Recall 低   | score 分布分离，但阈值偏移       |
| PRC 很差            | 极端类别不均衡                |
| 过拟合               | train / test noise 不一致 |
| Transformer 小数据翻车 | variance ↑             |

---

## 5. 多分类模拟策略

### 5.1 One-vs-Rest 逻辑

* 每个类别独立生成 score
* 正类 μ > 负类 μ
* 再 softmax

```text
logits_k = μ_k + ε_k
```

支持：

* 类间相似度矩阵
* 长尾类 recall 崩塌

---

## 6. 回归任务模拟

### 6.1 回归预测生成

```text
ŷ = f_model(x) + ε_noise
```

你不需要 x，只需：

* 目标函数复杂度
* 模型逼近误差

```yaml
regression:
  function_complexity: 0.8
  noise_level: 0.2
  heteroscedastic: true
```

---

### 6.2 指标自然变化

* MAE：受噪声线性影响
* RMSE：对极端误差敏感
* R²：低方差模型更稳

---

## 7. 指标计算模块（严格真实）

**硬约束**：

* 只用 sklearn-style 公式
* 不做任何“人为修正”

### 分类

* ROC-AUC
* PR-AUC
* Recall@Threshold
* Precision@K

### 回归

* RMSE
* MAE
* R²

---

## 8. 可视化设计（你后面会用得上）

### 8.1 核心图形

* ROC / PR 曲线（同任务多模型）
* 指标 vs 数据难度
* 指标 vs 样本量（learning curve）
* 模型稳定性（多次 seed）

---

## 9. 验证规则（防止“假模拟”）

你可以内置 **逻辑校验器**：

* separability ↑ ⇒ AUC 不应下降
* label_noise ↑ ⇒ 所有模型上限下降
* imbalance ↑ ⇒ PRC 比 ROC 更敏感
* linear model 在 nonlinearity ↑ 时提前饱和

违反就报警。


