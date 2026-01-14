"""
测试回归任务指标是否符合单调性规律
模型越强 → MAE/RMSE越小, R²越大
"""

import numpy as np
import pandas as pd
from ml_simulator import (
    TaskConfig, DifficultyConfig, ModelProfile,
    MLSimulator, TaskType, compare_models
)
from regression_config import RegressionDifficulty

def test_model_capacity_monotonicity():
    """测试不同capacity模型的指标单调性"""

    # 创建一系列能力递增的模型
    models = {
        "weak": ModelProfile(bias=0.7, variance=0.6, capacity=0.3, noise_tolerance=0.3),
        "medium": ModelProfile(bias=0.5, variance=0.4, capacity=0.5, noise_tolerance=0.5),
        "strong": ModelProfile(bias=0.3, variance=0.3, capacity=0.7, noise_tolerance=0.7),
        "very_strong": ModelProfile(bias=0.2, variance=0.2, capacity=0.9, noise_tolerance=0.8),
    }

    # 任务配置
    task_config = TaskConfig(
        task_type=TaskType.REGRESSION,
        num_samples=5000,
        random_state=42
    )

    # 简单难度
    reg_difficulty = RegressionDifficulty(
        signal_to_noise=1.0,
        function_complexity=0.3,
        noise_level=0.2,
        heteroscedastic=False,
        n_features=10,
        feature_noise=0.05
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.1,
        feature_noise=0.2,
        nonlinearity=0.5,
        spurious_correlation=0.3
    )

    # 运行模拟
    results = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=list(models.keys()),
        reg_difficulty=reg_difficulty,
        custom_profiles=models
    )

    print("=" * 80)
    print("回归任务 - 模型能力单调性测试")
    print("=" * 80)
    print(results[['model', 'mae', 'rmse', 'r2']].to_string(index=False))
    print()

    # 检查单调性
    mae_values = results['mae'].values
    rmse_values = results['rmse'].values
    r2_values = results['r2'].values

    print("Monotonicity Check:")
    print(f"  MAE decreasing: {all(mae_values[i] > mae_values[i+1] for i in range(len(mae_values)-1))}")
    print(f"  RMSE decreasing: {all(rmse_values[i] > rmse_values[i+1] for i in range(len(rmse_values)-1))}")
    print(f"  R2 increasing: {all(r2_values[i] < r2_values[i+1] for i in range(len(r2_values)-1))}")
    print()

    return results

def test_predefined_models():
    """测试预定义模型的回归指标"""

    # 预定义模型
    model_names = ['rf', 'lgbm', 'dnn', 'transformer']

    task_config = TaskConfig(
        task_type=TaskType.REGRESSION,
        num_samples=5000,
        random_state=42
    )

    reg_difficulty = RegressionDifficulty(
        signal_to_noise=1.0,
        function_complexity=0.5,
        noise_level=0.2,
        heteroscedastic=True,
        n_features=10,
        feature_noise=0.05
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.1,
        feature_noise=0.2,
        nonlinearity=0.5,
        spurious_correlation=0.3
    )

    results = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=model_names,
        reg_difficulty=reg_difficulty
    )

    print("=" * 80)
    print("回归任务 - 预定义模型对比")
    print("=" * 80)
    print(results[['model', 'mae', 'rmse', 'r2']].to_string(index=False))
    print()

    # 显示模型能力参数
    from ml_simulator import PREDEFINED_MODEL_PROFILES
    print("模型能力参数:")
    for name in model_names:
        profile = PREDEFINED_MODEL_PROFILES[name]
        print(f"  {name:12s}: capacity={profile.capacity:.2f}, bias={profile.bias:.2f}, "
              f"variance={profile.variance:.2f}, noise_tolerance={profile.noise_tolerance:.2f}")
    print()

    return results

def test_varying_difficulty():
    """测试不同难度下的单调性"""

    models = {
        "weak": ModelProfile(bias=0.7, variance=0.6, capacity=0.3, noise_tolerance=0.3),
        "strong": ModelProfile(bias=0.2, variance=0.2, capacity=0.9, noise_tolerance=0.8),
    }

    task_config = TaskConfig(
        task_type=TaskType.REGRESSION,
        num_samples=5000,
        random_state=42
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.1,
        feature_noise=0.2,
        nonlinearity=0.5,
        spurious_correlation=0.3
    )

    print("=" * 80)
    print("回归任务 - 不同难度下的单调性")
    print("=" * 80)

    complexities = [0.1, 0.3, 0.5, 0.7, 0.9]

    for complexity in complexities:
        reg_difficulty = RegressionDifficulty(
            signal_to_noise=1.0,
            function_complexity=complexity,
            noise_level=0.2,
            heteroscedastic=False,
            n_features=10,
            feature_noise=0.05
        )

        results = compare_models(
            task_config=task_config,
            difficulty=difficulty,
            model_names=list(models.keys()),
            reg_difficulty=reg_difficulty,
            custom_profiles=models
        )

        mae_weak, mae_strong = results.iloc[0]['mae'], results.iloc[1]['mae']
        r2_weak, r2_strong = results.iloc[0]['r2'], results.iloc[1]['r2']

        print(f"Complexity {complexity:.1f}: "
              f"weak MAE={mae_weak:.3f}, strong MAE={mae_strong:.3f} | "
              f"weak R2={r2_weak:.3f}, strong R2={r2_strong:.3f}")

    print()

if __name__ == "__main__":
    # 运行所有测试
    test_model_capacity_monotonicity()
    test_predefined_models()
    test_varying_difficulty()
