"""
机器学习模型性能模拟与指标计算框架
根据 SPEC Driven Development 设计实现

核心原则：
- 不直接生成指标数值，而是生成"预测行为 + 真实标签 → 指标函数"
- 所有异常现象（高AUC低Recall、PRC崩塌、过拟合）都能自然出现
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# 1. 任务类型定义
# =============================================================================

class TaskType(Enum):
    BINARY = "binary"
    MULTICLASS = "multiclass"
    REGRESSION = "regression"


# =============================================================================
# 2. 配置类
# =============================================================================

@dataclass
class TaskConfig:
    """任务配置"""
    task_type: TaskType
    num_samples: int = 10000
    n_classes: int = 2
    label_distribution: Optional[List[float]] = None  # 类别比例
    random_state: Optional[int] = None


@dataclass
class DifficultyConfig:
    """学习难度配置 - 控制数据可学习程度"""
    separability: float = 0.6          # 类间可分性 [0-1]
    label_noise: float = 0.1           # 标签翻转率 [0-1]
    feature_noise: float = 0.2         # 特征噪声 [0-1]
    nonlinearity: float = 0.7          # 非线性强度 [0-1]
    spurious_correlation: float = 0.3  # 伪相关性 [0-1]


@dataclass
class RegressionConfig:
    """回归任务专用配置"""
    function_complexity: float = 0.8
    noise_level: float = 0.2
    heteroscedastic: bool = True       # 异方差性


@dataclass
class ModelProfile:
    """模型能力画像"""
    # 基础能力参数
    bias: float = 0.5                  # 偏差（越高偏差越大）
    variance: float = 0.3              # 方差（越高越不稳定）
    capacity: float = 0.7              # 表达能力上限 [0-1]
    noise_tolerance: float = 0.5       # 噪声容忍度 [0-1]

    # 对难度因子的敏感度
    separability_sensitivity: float = 1.0
    nonlinearity_sensitivity: float = 1.0
    noise_sensitivity: float = 1.0

    # 支持的任务类型
    supported_tasks: List[str] = field(default_factory=lambda: ['binary', 'multiclass', 'regression'])


# =============================================================================
# 3. 预定义模型画像（从spec.md提取）
# =============================================================================

PREDEFINED_MODEL_PROFILES: Dict[str, ModelProfile] = {
    "svm": ModelProfile(
        bias=0.5, variance=0.2, capacity=0.6, noise_tolerance=0.4,
        separability_sensitivity=1.2, nonlinearity_sensitivity=0.3,
        supported_tasks=['binary']  # SVM主要支持二分类
    ),
    "rf": ModelProfile(
        bias=0.3, variance=0.4, capacity=0.7, noise_tolerance=0.8,
        separability_sensitivity=0.8, nonlinearity_sensitivity=0.6,
        supported_tasks=['binary', 'multiclass', 'regression']  # RF支持所有任务
    ),
    "lgbm": ModelProfile(
        bias=0.3, variance=0.3, capacity=0.8, noise_tolerance=0.6,
        separability_sensitivity=0.9, nonlinearity_sensitivity=0.9,
        noise_sensitivity=0.7,
        supported_tasks=['binary', 'multiclass', 'regression']  # LightGBM支持所有任务
    ),
    "dnn": ModelProfile(
        bias=0.2, variance=0.7, capacity=0.95, noise_tolerance=0.5,
        separability_sensitivity=1.0, nonlinearity_sensitivity=1.0,
        supported_tasks=['binary', 'multiclass', 'regression']  # DNN支持所有任务
    ),
    "cnn": ModelProfile(
        bias=0.3, variance=0.5, capacity=0.85, noise_tolerance=0.6,
        separability_sensitivity=0.8, nonlinearity_sensitivity=0.9,
        supported_tasks=['binary', 'multiclass', 'regression']  # CNN支持所有任务
    ),
    "rnn": ModelProfile(
        bias=0.4, variance=0.6, capacity=0.8, noise_tolerance=0.5,
        separability_sensitivity=0.9, nonlinearity_sensitivity=0.8,
        supported_tasks=['binary', 'multiclass', 'regression']  # RNN支持所有任务
    ),
    "transformer": ModelProfile(
        bias=0.2, variance=0.9, capacity=0.98, noise_tolerance=0.4,
        separability_sensitivity=1.0, nonlinearity_sensitivity=1.0,
        supported_tasks=['binary', 'multiclass', 'regression']  # Transformer支持所有任务
    ),
    "logreg": ModelProfile(
        bias=0.5, variance=0.1, capacity=0.5, noise_tolerance=0.5,
        separability_sensitivity=1.0, nonlinearity_sensitivity=0.1,
        supported_tasks=['binary', 'multiclass']  # Logistic Regression支持分类任务
    ),
    "xgboost": ModelProfile(
        bias=0.3, variance=0.3, capacity=0.8, noise_tolerance=0.7,
        separability_sensitivity=0.9, nonlinearity_sensitivity=0.9,
        supported_tasks=['binary', 'multiclass', 'regression']  # XGBoost支持所有任务
    ),
    "catboost": ModelProfile(
        bias=0.3, variance=0.25, capacity=0.78, noise_tolerance=0.75,
        separability_sensitivity=0.85, nonlinearity_sensitivity=0.85,
        supported_tasks=['binary', 'multiclass', 'regression']  # CatBoost支持所有任务
    ),
}


# =============================================================================
# 4. 标签生成器
# =============================================================================

def generate_labels(task_config: TaskConfig) -> np.ndarray:
    """
    生成标签，支持均衡/不均衡分布

    Parameters
    ----------
    task_config : TaskConfig
        任务配置对象

    Returns
    -------
    y : np.ndarray
        标签数组
    """
    rng = np.random.default_rng(task_config.random_state)

    if task_config.task_type == TaskType.REGRESSION:
        # 回归任务生成连续值
        y = rng.normal(0, 1, task_config.num_samples)
        return y

    # 分类任务
    if task_config.label_distribution is None:
        # 均衡分布
        y = rng.integers(0, task_config.n_classes, size=task_config.num_samples)
    else:
        # 不均衡分布
        class_probs = np.array(task_config.label_distribution, dtype=float)
        if len(class_probs) != task_config.n_classes:
            raise ValueError("label_distribution长度必须等于n_classes")
        class_probs = class_probs / class_probs.sum()
        y = rng.choice(task_config.n_classes, size=task_config.num_samples, p=class_probs)

    return y


# =============================================================================
# 5. 分类预测生成器
# =============================================================================

def generate_classification_predictions(
    y_true: np.ndarray,
    difficulty: DifficultyConfig,
    model_profile: ModelProfile,
    task_config: TaskConfig,
) -> np.ndarray:
    """
    生成分类预测概率

    核心公式：
        score = μ(class, model, difficulty) + ε_sample + ε_model
        prob = sigmoid(score) / softmax(scores)

    Parameters
    ----------
    y_true : np.ndarray
        真实标签
    difficulty : DifficultyConfig
        难度配置
    model_profile : ModelProfile
        模型能力画像
    task_config : TaskConfig
        任务配置

    Returns
    -------
    y_prob : np.ndarray
        预测概率 (n_samples, n_classes)
    """
    rng = np.random.default_rng(task_config.random_state)
    n_samples = len(y_true)
    n_classes = task_config.n_classes

    # 计算每个类别的难度（可分性）
    # separability越高，正负类均值差距越大
    class_means = np.zeros(n_classes)
    for c in range(n_classes):
        class_means[c] = difficulty.separability * (1.0 if c == 1 else -1.0)

    # 标签噪声：一部分样本"永远学不会"
    noisy_mask = rng.random(n_samples) < difficulty.label_noise

    # 为每个样本生成score
    logits = np.zeros((n_samples, n_classes))

    for i in range(n_samples):
        true_label = y_true[i]

        for c in range(n_classes):
            # μ：学习到的信号
            # 如果是真实类别，score更高
            if c == true_label:
                mu = difficulty.separability * model_profile.capacity
                # 模型非线性敏感度影响
                if difficulty.nonlinearity > 0.5:
                    mu *= (1 - model_profile.nonlinearity_sensitivity * (difficulty.nonlinearity - 0.5))
            else:
                mu = -difficulty.separability * 0.5

            # 样本级噪声
            eps_sample = rng.normal(0, difficulty.feature_noise)

            # 模型不稳定性
            eps_model = rng.normal(0, model_profile.variance)

            # 模型偏差影响
            bias_effect = model_profile.bias * (1 if c != true_label else 0)

            # 如果是噪声样本，降低信号
            if noisy_mask[i]:
                mu *= 0.1

            logits[i, c] = mu + eps_sample + eps_model + bias_effect

    # 转换为概率
    if n_classes == 2:
        # 二分类用sigmoid
        scores = logits[:, 1]  # 正类score
        prob_pos = 1 / (1 + np.exp(-scores))
        y_prob = np.column_stack([1 - prob_pos, prob_pos])
    else:
        # 多分类用softmax
        exp_logits = np.exp(logits - logits.max(axis=1, keepdims=True))
        y_prob = exp_logits / exp_logits.sum(axis=1, keepdims=True)

    return y_prob


# =============================================================================
# 6. 回归预测生成器
# =============================================================================

def generate_regression_predictions(
    y_true: np.ndarray,
    difficulty: DifficultyConfig,
    model_profile: ModelProfile,
    task_config: TaskConfig,
    reg_config: RegressionConfig,
) -> np.ndarray:
    """
    生成回归预测值

    核心公式：
        ŷ = f_model(x) + ε_noise

    Parameters
    ----------
    y_true : np.ndarray
        真实值
    difficulty : DifficultyConfig
        难度配置
    model_profile : ModelProfile
        模型能力画像
    task_config : TaskConfig
        任务配置
    reg_config : RegressionConfig
        回归专用配置

    Returns
    -------
    y_pred : np.ndarray
        预测值
    """
    rng = np.random.default_rng(task_config.random_state)

    # 模型对真实函数的逼近能力
    approximation_quality = model_profile.capacity * (1 - reg_config.function_complexity * 0.5)

    # 基础预测：模型学到的部分
    signal = y_true * approximation_quality

    # 添加噪声
    if reg_config.heteroscedastic:
        # 异方差：噪声随|y_true|增大
        noise_std = reg_config.noise_level * (1 + 0.5 * np.abs(y_true))
    else:
        # 同方差
        noise_std = reg_config.noise_level

    noise = rng.normal(0, noise_std, size=len(y_true))

    # 模型方差导致的不稳定性
    model_noise = rng.normal(0, model_profile.variance * 0.5, size=len(y_true))

    y_pred = signal + noise + model_noise

    return y_pred


# =============================================================================
# 7. 指标计算器（严格使用sklearn公式）
# =============================================================================

def _precision_recall_f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """计算二分类的Precision, Recall, F1"""
    tp = np.logical_and(y_true == 1, y_pred == 1).sum()
    fp = np.logical_and(y_true == 0, y_pred == 1).sum()
    fn = np.logical_and(y_true == 1, y_pred == 0).sum()

    precision = tp / (tp + fp + 1e-12)
    recall = tp / (tp + fn + 1e-12)
    f1 = 2 * precision * recall / (precision + recall + 1e-12)

    return float(precision), float(recall), float(f1)


def _binary_pr_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """计算二分类的PR-AUC（Precision-Recall曲线下面积）"""
    # 按score降序排序
    order = np.argsort(-y_score)
    y_true_sorted = y_true[order]

    # 计算累积的precision和recall
    tp_cumsum = np.cumsum(y_true_sorted)
    precision_curve = tp_cumsum / (np.arange(len(y_true_sorted)) + 1)
    recall_curve = tp_cumsum / (y_true_sorted.sum() + 1e-12)

    # 计算AUC（使用梯形法则）
    pr_auc = np.trapz(precision_curve, recall_curve)

    return float(np.clip(pr_auc, 0, 1))


def _log_loss_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """计算二分类的LogLoss"""
    # 避免log(0)
    y_prob = np.clip(y_prob, 1e-15, 1 - 1e-15)

    # LogLoss = -1/n * sum(y * log(p) + (1-y) * log(1-p))
    loss = -np.mean(y_true * np.log(y_prob) + (1 - y_true) * np.log(1 - y_prob))

    return float(loss)


def _binary_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """纯numpy实现的ROC AUC（用于二分类）"""
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score)

    pos = (y_true == 1)
    neg = (y_true == 0)
    n_pos = pos.sum()
    n_neg = neg.sum()

    if n_pos == 0 or n_neg == 0:
        return np.nan

    # 使用秩统计法计算AUC
    order = np.argsort(y_score)
    ranks = np.argsort(order) + 1
    sum_ranks_pos = ranks[pos].sum()
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)

    return float(auc)


def _precision_recall_f1_multiclass(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> Tuple[float, float, float]:
    """计算多分类的Macro Precision, Recall, F1"""
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    precisions = []
    recalls = []
    f1s = []
    support = []  # 每个类别的样本数

    for c in range(n_classes):
        tp = np.logical_and(y_true == c, y_pred == c).sum()
        fp = np.logical_and(y_true != c, y_pred == c).sum()
        fn = np.logical_and(y_true == c, y_pred != c).sum()
        support.append((y_true == c).sum())

        precision = tp / (tp + fp + 1e-12)
        recall = tp / (tp + fn + 1e-12)
        f1 = 2 * precision * recall / (precision + recall + 1e-12)

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1s))

    # Weighted average
    support = np.array(support)
    weighted_precision = float(np.average(precisions, weights=support))
    weighted_recall = float(np.average(recalls, weights=support))
    weighted_f1 = float(np.average(f1s, weights=support))

    return (macro_precision, macro_recall, macro_f1,
            weighted_precision, weighted_recall, weighted_f1)


def _top_k_accuracy(y_true: np.ndarray, y_prob: np.ndarray, k: int = 5) -> float:
    """计算Top-K准确率"""
    n_samples = y_true.shape[0]

    # 获取top-k预测
    top_k_pred = np.argsort(-y_prob, axis=1)[:, :k]

    # 检查真实标签是否在top-k中
    correct = 0
    for i in range(n_samples):
        if y_true[i] in top_k_pred[i]:
            correct += 1

    return float(correct / n_samples)


def _log_loss_multiclass(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """计算多分类的LogLoss"""
    n_samples = y_true.shape[0]

    # 避免log(0)
    y_prob = np.clip(y_prob, 1e-15, 1)

    # One-hot编码
    y_true_one_hot = np.zeros_like(y_prob)
    y_true_one_hot[np.arange(n_samples), y_true] = 1

    # LogLoss = -1/n * sum(sum(y_ij * log(p_ij)))
    loss = -np.sum(y_true_one_hot * np.log(y_prob)) / n_samples

    return float(loss)


def _multiclass_auc_ovr_macro(y_true: np.ndarray, y_prob: np.ndarray, n_classes: int) -> float:
    """多分类one-vs-rest AUC的macro平均"""
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob)

    aucs = []
    for c in range(n_classes):
        y_true_bin = (y_true == c).astype(int)
        auc_c = _binary_auc(y_true_bin, y_prob[:, c])
        if not np.isnan(auc_c):
            aucs.append(auc_c)

    if not aucs:
        return np.nan

    return float(np.mean(aucs))


def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """计算回归指标"""
    residuals = y_true - y_pred

    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    mae = float(np.mean(np.abs(residuals)))

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - ss_res / (ss_tot + 1e-12))

    return {
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
    }


def compute_classification_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_classes: int,
) -> Dict[str, float]:
    """
    计算分类指标（自动选择二分类/多分类）

    二分类指标：
    - Accuracy
    - Precision
    - Recall
    - F1
    - ROC-AUC
    - PR-AUC
    - LogLoss

    多分类指标：
    - Accuracy
    - Macro-F1
    - Weighted-F1
    - LogLoss
    - Top-K Accuracy (k=3)

    Parameters
    ----------
    y_true : np.ndarray
        真实标签
    y_prob : np.ndarray
        预测概率 (n_samples, n_classes)
    n_classes : int
        类别数

    Returns
    -------
    metrics : Dict[str, float]
        指标字典
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob)

    if y_prob.ndim == 1:
        y_prob = np.vstack([1 - y_prob, y_prob]).T

    y_pred = np.argmax(y_prob, axis=1)
    accuracy = float(np.mean(y_pred == y_true))

    if n_classes == 2:
        # 二分类指标
        roc_auc = _binary_auc(y_true, y_prob[:, 1])
        pr_auc = _binary_pr_auc(y_true, y_prob[:, 1])
        logloss = _log_loss_binary(y_true, y_prob[:, 1])
        precision, recall, f1 = _precision_recall_f1_binary(y_true, y_pred)

        return {
            "task_type": "binary",
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "logloss": logloss,
        }
    else:
        # 多分类指标
        (macro_precision, macro_recall, macro_f1,
         weighted_precision, weighted_recall, weighted_f1) = _precision_recall_f1_multiclass(
            y_true, y_pred, n_classes
        )

        logloss = _log_loss_multiclass(y_true, y_prob)
        top_3_acc = _top_k_accuracy(y_true, y_prob, k=3)

        return {
            "task_type": "multiclass",
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "logloss": logloss,
            "top_3_accuracy": top_3_acc,
        }


# =============================================================================
# 8. 主模拟器类
# =============================================================================

class MLSimulator:
    """机器学习结果模拟器"""

    def __init__(
        self,
        task_config: TaskConfig,
        difficulty: DifficultyConfig,
        model_profile: Union[str, ModelProfile],
        reg_config: Optional[RegressionConfig] = None,
    ):
        """
        Parameters
        ----------
        task_config : TaskConfig
            任务配置
        difficulty : DifficultyConfig
            难度配置
        model_profile : str or ModelProfile
            模型名称（预定义）或自定义模型画像
        reg_config : RegressionConfig, optional
            回归任务专用配置
        """
        self.task_config = task_config
        self.difficulty = difficulty

        if isinstance(model_profile, str):
            if model_profile not in PREDEFINED_MODEL_PROFILES:
                raise ValueError(f"未知模型: {model_profile}，可选: {list(PREDEFINED_MODEL_PROFILES.keys())}")
            self.model_profile = PREDEFINED_MODEL_PROFILES[model_profile]
        else:
            self.model_profile = model_profile

        self.reg_config = reg_config or RegressionConfig()

        # 生成标签
        self.y_true = generate_labels(task_config)

    def simulate(self) -> Dict[str, float]:
        """
        执行模拟并返回指标

        Returns
        -------
        metrics : Dict[str, float]
            计算得到的指标
        """
        if self.task_config.task_type == TaskType.REGRESSION:
            y_pred = generate_regression_predictions(
                self.y_true,
                self.difficulty,
                self.model_profile,
                self.task_config,
                self.reg_config,
            )
            metrics = compute_regression_metrics(self.y_true, y_pred)
        else:
            y_prob = generate_classification_predictions(
                self.y_true,
                self.difficulty,
                self.model_profile,
                self.task_config,
            )
            metrics = compute_classification_metrics(
                self.y_true,
                y_prob,
                self.task_config.n_classes,
            )

        return metrics

    def get_predictions(self) -> np.ndarray:
        """
        获取预测结果（用于可视化或进一步分析）

        Returns
        -------
        predictions : np.ndarray
            分类任务返回概率矩阵，回归任务返回预测值
        """
        if self.task_config.task_type == TaskType.REGRESSION:
            return generate_regression_predictions(
                self.y_true,
                self.difficulty,
                self.model_profile,
                self.task_config,
                self.reg_config,
            )
        else:
            return generate_classification_predictions(
                self.y_true,
                self.difficulty,
                self.model_profile,
                self.task_config,
            )


# =============================================================================
# 9. 学习曲线模拟器
# =============================================================================

def simulate_learning_curve(
    model_name: str,
    task_config: TaskConfig,
    difficulty: DifficultyConfig,
    train_sizes: np.ndarray = np.linspace(0.1, 1.0, 10),
    acc_10: float = 0.5,
    acc_100: float = 0.9,
    alpha: float = 3,
    noise_std_start: float = 0.03,
    noise_std_end: float = 0.002,
) -> pd.DataFrame:
    """
    模拟学习曲线（不同训练集大小下的性能）

    Parameters
    ----------
    model_name : str
        模型名称
    task_config : TaskConfig
        任务配置
    difficulty : DifficultyConfig
        难度配置
    train_sizes : np.ndarray
        训练集大小比例
    acc_10 : float
        10%数据时的准确率
    acc_100 : float
        100%数据时的准确率
    alpha : float
        学习速度
    noise_std_start : float
        小数据时的噪声标准差
    noise_std_end : float
        大数据时的噪声标准差

    Returns
    -------
    df : pd.DataFrame
        学习曲线数据框
    """
    rng = np.random.default_rng(task_config.random_state)

    # 生成固定验证集标签
    y_val = generate_labels(task_config)

    train_sizes = np.asarray(train_sizes, dtype=float)
    s_min, s_max = train_sizes.min(), train_sizes.max()

    records = []

    for s in train_sizes:
        # 归一化进度
        if s_max > s_min:
            t = (s - s_min) / (s_max - s_min)
        else:
            t = 1.0

        # 指数饱和学习曲线
        base_acc = acc_10 + (acc_100 - acc_10) * (1 - np.exp(-alpha * t))

        # 异方差噪声
        noise_std = noise_std_start * (1 - t) + noise_std_end
        noisy_acc = base_acc + rng.normal(0, noise_std)

        # 调整难度以匹配目标准确率
        adjusted_difficulty = DifficultyConfig(
            separability=max(0.1, min(0.99, noisy_acc)),
            label_noise=difficulty.label_noise,
            feature_noise=difficulty.feature_noise,
            nonlinearity=difficulty.nonlinearity,
            spurious_correlation=difficulty.spurious_correlation,
        )

        # 模拟
        simulator = MLSimulator(
            task_config=task_config,
            difficulty=adjusted_difficulty,
            model_profile=model_name,
        )
        metrics = simulator.simulate()

        metrics["train_ratio"] = float(s)
        metrics["target_accuracy"] = float(np.clip(noisy_acc, 0.0, 1.0))
        metrics["base_accuracy"] = base_acc

        records.append(metrics)

    df = pd.DataFrame(records)
    cols = (
        ["train_ratio", "base_accuracy", "target_accuracy"]
        + [c for c in df.columns if c not in ("train_ratio", "base_accuracy", "target_accuracy")]
    )

    return df[cols]


# =============================================================================
# 10. 批量模拟：多个模型对比
# =============================================================================

def compare_models(
    task_config: TaskConfig,
    difficulty: DifficultyConfig,
    model_names: List[str],
    reg_config: Optional[RegressionConfig] = None,
    custom_profiles: Optional[Dict[str, ModelProfile]] = None,
) -> pd.DataFrame:
    """
    批量模拟多个模型在同一任务上的表现

    Parameters
    ----------
    task_config : TaskConfig
        任务配置
    difficulty : DifficultyConfig
        难度配置
    model_names : List[str]
        模型名称列表
    reg_config : RegressionConfig, optional
        回归配置
    custom_profiles : Dict[str, ModelProfile], optional
        自定义模型画像 {model_name: ModelProfile}
        如果提供，将覆盖预定义画像

    Returns
    -------
    df : pd.DataFrame
        对比结果
    """
    results = []

    for model_name in model_names:
        # 确定使用哪个模型画像
        if custom_profiles and model_name in custom_profiles:
            profile = custom_profiles[model_name]
        else:
            profile = model_name

        simulator = MLSimulator(
            task_config=task_config,
            difficulty=difficulty,
            model_profile=profile,
            reg_config=reg_config,
        )
        metrics = simulator.simulate()
        metrics["model"] = model_name
        results.append(metrics)

    return pd.DataFrame(results)


# =============================================================================
# 11. 难度扫描：分析难度对性能的影响
# =============================================================================

def scan_difficulty(
    task_config: TaskConfig,
    model_name: str,
    difficulty_param: str,
    difficulty_values: np.ndarray,
    base_difficulty: Optional[DifficultyConfig] = None,
    n_runs: int = 5,
) -> pd.DataFrame:
    """
    扫描某个难度参数对模型性能的影响

    Parameters
    ----------
    task_config : TaskConfig
        任务配置
    model_name : str
        模型名称
    difficulty_param : str
        要扫描的参数名（如'separability'）
    difficulty_values : np.ndarray
        参数值范围
    base_difficulty : DifficultyConfig, optional
        基础难度配置（其他参数固定）
    n_runs : int
        每个参数值运行次数（取平均）

    Returns
    -------
    df : pd.DataFrame
        扫描结果
    """
    if base_difficulty is None:
        base_difficulty = DifficultyConfig()

    results = []

    for value in difficulty_values:
        # 更新难度参数
        difficulty = DifficultyConfig(
            **{**base_difficulty.__dict__, difficulty_param: value}
        )

        # 多次运行取平均
        for run in range(n_runs):
            # 创建新的task_config，修改random_state
            config_dict = task_config.__dict__.copy()
            config_dict['random_state'] = None if task_config.random_state is None else task_config.random_state + run
            task_config_run = TaskConfig(**config_dict)

            simulator = MLSimulator(
                task_config=task_config_run,
                difficulty=difficulty,
                model_profile=model_name,
            )
            metrics = simulator.simulate()
            metrics[difficulty_param] = value
            metrics["run"] = run
            results.append(metrics)

    df = pd.DataFrame(results)

    # 按参数值聚合（计算均值和标准差）
    numeric_cols = [c for c in df.columns if c not in [difficulty_param, "run"]]
    agg_mean = df.groupby(difficulty_param)[numeric_cols].mean()
    agg_std = df.groupby(difficulty_param)[numeric_cols].std()

    # 重命名列
    agg_mean.columns = [f"{c}_mean" for c in agg_mean.columns]
    agg_std.columns = [f"{c}_std" for c in agg_std.columns]

    result_df = pd.concat([agg_mean, agg_std], axis=1)
    result_df = result_df.sort_index()
    result_df.index.name = difficulty_param

    return result_df.reset_index()
