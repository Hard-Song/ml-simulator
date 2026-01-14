"""
回归任务专用配置和数据生成模块

与分类任务的主要区别：
1. 需要生成特征矩阵 X 和目标值 y
2. y = f(X) + noise，其中 f 是未知的真实函数
3. 难度参数的含义不同：信噪比、函数复杂度、异方差性等
"""

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass
class RegressionDifficulty:
    """回归任务难度配置

    Parameters
    ----------
    signal_to_noise : float
        信噪比 [0.1-2.0]
        越高表示信号越强，模型越容易学习
        SNR = var(signal) / var(noise)

    function_complexity : float
        真实函数 f(X) 的复杂度 [0-1]
        0: 线性函数 y = w*X + b
        1: 高度非线性（多项式、交互项等）

    noise_level : float
        基础噪声标准差 [0-1]
        控制整体的噪声强度

    heteroscedastic : bool
        是否异方差
        True: 噪声随 |y| 增大而增大
        False: 同方差噪声

    n_features : int
        特征数量 [2-20]
        特征越多，高维空间越复杂

    feature_noise : float
        特征噪声 [0-0.5]
        特征 X 本身的噪声水平
    """
    signal_to_noise: float = 1.0
    function_complexity: float = 0.5
    noise_level: float = 0.2
    heteroscedastic: bool = True
    n_features: int = 10
    feature_noise: float = 0.05


def generate_regression_data(
    num_samples: int,
    difficulty: RegressionDifficulty,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成回归数据集 (X, y)

    数据生成流程：
        1. 生成特征矩阵 X (n_samples, n_features)
        2. 计算真实信号 signal = f(X)
        3. 添加噪声 y = signal + noise

    Parameters
    ----------
    num_samples : int
        样本数量

    difficulty : RegressionDifficulty
        回归难度配置

    random_state : int
        随机种子

    Returns
    -------
    X : np.ndarray
        特征矩阵 (n_samples, n_features)

    y : np.ndarray
        目标值 (n_samples,)
    """
    rng = np.random.default_rng(random_state)

    # 1. 生成特征矩阵 X
    # 每个特征从标准正态分布采样
    X_clean = rng.standard_normal((num_samples, difficulty.n_features))

    # 添加特征噪声
    if difficulty.feature_noise > 0:
        X_noise = rng.normal(0, difficulty.feature_noise, X_clean.shape)
        X = X_clean + X_noise
    else:
        X = X_clean

    # 2. 计算真实信号 signal = f(X)
    signal = _compute_true_function(X, difficulty.function_complexity, rng)

    # 标准化 signal，使其均值为0，标准差为1
    signal = (signal - signal.mean()) / (signal.std() + 1e-12)

    # 3. 根据信噪比调整噪声水平
    # SNR = var(signal) / var(noise) = 1 / var(noise) （因为signal已标准化）
    # 所以 noise_std = 1 / sqrt(SNR)
    if difficulty.signal_to_noise > 0:
        target_noise_std = 1.0 / np.sqrt(difficulty.signal_to_noise)
    else:
        target_noise_std = difficulty.noise_level

    # 4. 生成噪声
    if difficulty.heteroscedastic:
        # 异方差：噪声随 |signal| 增大
        # 使用 log(1 + |signal|) 作为调制因子
        modulation = np.log1p(np.abs(signal))
        noise_std = target_noise_std * (1 + modulation)
    else:
        # 同方差
        noise_std = target_noise_std

    noise = rng.normal(0, noise_std)

    # 5. 生成最终的目标值
    y = signal + noise

    # 再次标准化 y，确保输出范围合理
    y = (y - y.mean()) / (y.std() + 1e-12)

    return X, y


def _compute_true_function(
    X: np.ndarray,
    complexity: float,
    rng: np.random.Generator
) -> np.ndarray:
    """
    计算真实函数 f(X)

    根据 complexity 参数控制函数的复杂度：
    - 0.0: 纯线性
    - 0.3: 线性 + 少量二次项
    - 0.5: 线性 + 二次项 + 少量交互项
    - 0.7: 二次 + 多项交互项
    - 1.0: 高度非线性（三角函数、高次多项式等）

    Parameters
    ----------
    X : np.ndarray
        特征矩阵 (n_samples, n_features)

    complexity : float
        函数复杂度 [0-1]

    rng : np.random.Generator
        随机数生成器

    Returns
    -------
    y : np.ndarray
        函数值 (n_samples,)
    """
    n_samples, n_features = X.shape

    # 基础：线性项
    # 随机生成权重
    linear_weights = rng.standard_normal(n_features)
    y = X @ linear_weights

    if complexity < 0.2:
        # 几乎纯线性
        return y

    # 添加二次项
    if complexity >= 0.2:
        # 选择部分特征添加二次项
        n_quadratic = int(n_features * min(complexity * 2, 1.0))
        if n_quadratic > 0:
            quad_features = rng.choice(n_features, n_quadratic, replace=False)
            quad_weights = rng.standard_normal(n_quadratic)
            for i, feat_idx in enumerate(quad_features):
                y += quad_weights[i] * (X[:, feat_idx] ** 2) * 0.3

    if complexity < 0.5:
        return y

    # 添加交互项
    if complexity >= 0.5:
        n_interactions = int(n_features * min((complexity - 0.3) * 2, 1.0))
        if n_interactions > 0:
            for _ in range(n_interactions):
                feat1, feat2 = rng.choice(n_features, 2, replace=False)
                interaction_weight = rng.standard_normal()
                y += interaction_weight * (X[:, feat1] * X[:, feat2]) * 0.2

    if complexity < 0.7:
        return y

    # 添加非线性变换（三角函数、指数等）
    if complexity >= 0.7:
        # 选择部分特征进行非线性变换
        n_nonlinear = int(n_features * min((complexity - 0.5) * 2, 1.0))
        if n_nonlinear > 0:
            nonlinear_features = rng.choice(n_features, n_nonlinear, replace=False)
            for feat_idx in nonlinear_features:
                # 随机选择变换类型
                transform_type = rng.integers(3)

                if transform_type == 0:
                    # sin 变换
                    y += 0.5 * np.sin(X[:, feat_idx])
                elif transform_type == 1:
                    # exp 变换（截断以避免爆炸）
                    y += 0.3 * np.exp(np.clip(X[:, feat_idx], -3, 3))
                else:
                    # tanh 变换
                    y += 0.4 * np.tanh(X[:, feat_idx])

    return y


def compute_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> dict:
    """
    计算回归评估指标

    Parameters
    ----------
    y_true : np.ndarray
        真实值

    y_pred : np.ndarray
        预测值

    Returns
    -------
    metrics : dict
        包含 MAE, RMSE, R² 的字典
    """
    residuals = y_true - y_pred

    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - ss_res / (ss_tot + 1e-12))

    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2
    }
