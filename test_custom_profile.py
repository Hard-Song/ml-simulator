"""
测试自定义模型画像功能
"""

from ml_simulator import (
    TaskConfig,
    DifficultyConfig,
    ModelProfile,
    compare_models,
    TaskType,
)


def test_custom_profile():
    """测试自定义模型画像"""
    print("=" * 60)
    print("测试: 自定义模型画像")
    print("=" * 60)

    # 任务配置
    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=42,
    )

    # 难度配置
    difficulty = DifficultyConfig(
        separability=0.7,
        label_noise=0.05,
        feature_noise=0.1,
    )

    # 自定义模型画像：高方差、高表达能力（模拟深度模型）
    custom_profile = ModelProfile(
        bias=0.2,      # 低偏差
        variance=0.7,  # 高方差（容易过拟合）
        capacity=0.9,  # 高表达能力
        noise_tolerance=0.5,
    )

    # 使用自定义画像
    print("\n[测试 1] 使用自定义画像")
    print("自定义参数: bias=0.2, variance=0.7, capacity=0.9")

    custom_profiles = {
        'lgbm': custom_profile,
        'rf': custom_profile,
    }

    results_custom = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=['lgbm', 'rf'],
        custom_profiles=custom_profiles,
    )

    print("\n结果（自定义画像）:")
    print(results_custom[['model', 'accuracy', 'auc']].to_string(index=False))

    # 使用预定义画像
    print("\n" + "=" * 60)
    print("[测试 2] 使用预定义画像")

    results_predefined = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=['lgbm', 'rf'],
        custom_profiles=None,  # 使用预定义
    )

    print("\n结果（预定义画像）:")
    print(results_predefined[['model', 'accuracy', 'auc']].to_string(index=False))

    # 对比
    print("\n" + "=" * 60)
    print("[对比] 自定义 vs 预定义")

    comparison = pd.merge(
        results_custom[['model', 'accuracy', 'auc']],
        results_predefined[['model', 'accuracy', 'auc']],
        on='model',
        suffixes=('_custom', '_predefined')
    )

    print(comparison.to_string(index=False))

    # 检查是否有差异
    acc_diff = (comparison['accuracy_custom'] - comparison['accuracy_predefined']).abs().max()
    if acc_diff > 0.01:
        print(f"\n[成功] 自定义画像生效！准确率最大差异: {acc_diff:.4f}")
    else:
        print(f"\n[警告] 自定义画像可能未生效，差异很小: {acc_diff:.4f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import pandas as pd
    test_custom_profile()
