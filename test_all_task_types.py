"""
测试所有任务类型的指标计算
"""

from ml_simulator import (
    TaskConfig,
    DifficultyConfig,
    MLSimulator,
    TaskType,
)


def test_binary_classification():
    """测试二分类指标"""
    print("=" * 60)
    print("测试 1: 二分类任务")
    print("=" * 60)

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.7,
        label_noise=0.05,
        feature_noise=0.1,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="lgbm",
    )

    metrics = simulator.simulate()

    print("\n二分类指标:")
    print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
    print(f"  Precision: {metrics.get('precision', 'N/A')}")
    print(f"  Recall: {metrics.get('recall', 'N/A')}")
    print(f"  F1: {metrics.get('f1', 'N/A')}")
    print(f"  ROC-AUC: {metrics.get('roc_auc', 'N/A')}")
    print(f"  PR-AUC: {metrics.get('pr_auc', 'N/A')}")
    print(f"  LogLoss: {metrics.get('logloss', 'N/A')}")
    print(f"  Task Type: {metrics.get('task_type', 'N/A')}")

    # 验证指标存在
    required_metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc', 'logloss']
    missing = [m for m in required_metrics if m not in metrics]
    if missing:
        print(f"\n[错误] 缺少指标: {missing}")
        return False

    print("\n[成功] 所有二分类指标正常")
    return True


def test_multiclass_classification():
    """测试多分类指标"""
    print("\n" + "=" * 60)
    print("测试 2: 多分类任务")
    print("=" * 60)

    task_config = TaskConfig(
        task_type=TaskType.MULTICLASS,
        num_samples=5000,
        n_classes=5,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.08,
        feature_noise=0.15,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="rf",
    )

    metrics = simulator.simulate()

    print("\n多分类指标:")
    print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
    print(f"  Macro-F1: {metrics.get('macro_f1', 'N/A')}")
    print(f"  Weighted-F1: {metrics.get('weighted_f1', 'N/A')}")
    print(f"  LogLoss: {metrics.get('logloss', 'N/A')}")
    print(f"  Top-3 Accuracy: {metrics.get('top_3_accuracy', 'N/A')}")
    print(f"  Task Type: {metrics.get('task_type', 'N/A')}")

    # 验证指标存在
    required_metrics = ['accuracy', 'macro_f1', 'weighted_f1', 'logloss', 'top_3_accuracy']
    missing = [m for m in required_metrics if m not in metrics]
    if missing:
        print(f"\n[错误] 缺少指标: {missing}")
        return False

    print("\n[成功] 所有多分类指标正常")
    return True


def test_regression():
    """测试回归指标"""
    print("\n" + "=" * 60)
    print("测试 3: 回归任务")
    print("=" * 60)

    from ml_simulator import RegressionConfig

    task_config = TaskConfig(
        task_type=TaskType.REGRESSION,
        num_samples=3000,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        feature_noise=0.2,
    )

    reg_config = RegressionConfig(
        function_complexity=0.7,
        noise_level=0.3,
        heteroscedastic=True,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="dnn",
        reg_config=reg_config,
    )

    metrics = simulator.simulate()

    print("\n回归指标:")
    print(f"  MAE: {metrics.get('mae', 'N/A')}")
    print(f"  RMSE: {metrics.get('rmse', 'N/A')}")
    print(f"  R2: {metrics.get('r2', 'N/A')}")

    # 验证指标存在
    required_metrics = ['mae', 'rmse', 'r2']
    missing = [m for m in required_metrics if m not in metrics]
    if missing:
        print(f"\n[错误] 缺少指标: {missing}")
        return False

    print("\n[成功] 所有回归指标正常")
    return True


def test_imbalanced_multiclass():
    """测试不均衡多分类"""
    print("\n" + "=" * 60)
    print("测试 4: 不均衡多分类任务")
    print("=" * 60)

    task_config = TaskConfig(
        task_type=TaskType.MULTICLASS,
        num_samples=10000,
        n_classes=5,
        label_distribution=[0.5, 0.25, 0.15, 0.07, 0.03],  # 长尾
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.1,
        feature_noise=0.2,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="lgbm",
    )

    metrics = simulator.simulate()

    print("\n不均衡多分类指标:")
    print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
    print(f"  Macro-F1: {metrics.get('macro_f1', 'N/A')}")
    print(f"  Weighted-F1: {metrics.get('weighted_f1', 'N/A')}")

    # 在不均衡数据中，Weighted-F1通常高于Macro-F1
    macro_f1 = metrics.get('macro_f1', 0)
    weighted_f1 = metrics.get('weighted_f1', 0)

    print(f"\n对比:")
    print(f"  Macro-F1: {macro_f1:.4f}")
    print(f"  Weighted-F1: {weighted_f1:.4f}")
    print(f"  差异: {weighted_f1 - macro_f1:.4f}")

    if weighted_f1 > macro_f1:
        print(f"  [符合预期] Weighted-F1 > Macro-F1（长尾分布）")

    print("\n[成功] 不均衡多分类指标正常")
    return True


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "全任务类型指标测试" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    all_passed = True

    # 测试 1: 二分类
    if not test_binary_classification():
        all_passed = False

    # 测试 2: 多分类
    if not test_multiclass_classification():
        all_passed = False

    # 测试 3: 回归
    if not test_regression():
        all_passed = False

    # 测试 4: 不均衡多分类
    if not test_imbalanced_multiclass():
        all_passed = False

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("[成功] 所有任务类型的指标计算正常！")
    else:
        print("[失败] 部分测试失败，请检查")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
