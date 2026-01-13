"""
快速测试脚本 - 验证 ml_simulator 的基本功能
"""

import numpy as np
from ml_simulator import (
    TaskConfig,
    DifficultyConfig,
    RegressionConfig,
    MLSimulator,
    simulate_learning_curve,
    compare_models,
    scan_difficulty,
    TaskType,
)


def test_basic_binary_classification():
    """测试基础二分类"""
    print("测试 1: 基础二分类...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=1000,
        n_classes=2,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.7,
        label_noise=0.05,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="lgbm",
    )

    metrics = simulator.simulate()

    assert 0 <= metrics["accuracy"] <= 1, "accuracy 应该在 [0, 1] 之间"
    assert 0 <= metrics["auc"] <= 1, "auc 应该在 [0, 1] 之间"
    assert metrics["n_classes"] == 2, "类别数应该是 2"

    print(f"  [OK] accuracy: {metrics['accuracy']:.4f}")
    print(f"  [OK] auc: {metrics['auc']:.4f}")
    print("  [OK] 测试通过\n")


def test_multiclass_classification():
    """测试多分类"""
    print("测试 2: 多分类...")

    task_config = TaskConfig(
        task_type=TaskType.MULTICLASS,
        num_samples=2000,
        n_classes=5,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.1,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="rf",
    )

    metrics = simulator.simulate()

    assert 0 <= metrics["accuracy"] <= 1, "accuracy 应该在 [0, 1] 之间"
    assert 0 <= metrics["auc_ovr_macro"] <= 1, "auc_ovr_macro 应该在 [0, 1] 之间"
    assert metrics["n_classes"] == 5, "类别数应该是 5"

    print(f"  [OK] accuracy: {metrics['accuracy']:.4f}")
    print(f"  [OK] auc_ovr_macro: {metrics['auc_ovr_macro']:.4f}")
    print(f"  [OK] macro_f1: {metrics['macro_f1']:.4f}")
    print("  [OK] 测试通过\n")


def test_imbalanced_classification():
    """测试不均衡分类"""
    print("测试 3: 不均衡分类...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        label_distribution=[0.9, 0.1],
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.7,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="xgboost",
    )

    metrics = simulator.simulate()

    print(f"  [OK] accuracy: {metrics['accuracy']:.4f}")
    print(f"  [OK] auc: {metrics['auc']:.4f}")
    print("  [OK] 测试通过\n")


def test_regression():
    """测试回归"""
    print("测试 4: 回归任务...")

    task_config = TaskConfig(
        task_type=TaskType.REGRESSION,
        num_samples=1000,
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

    assert metrics["rmse"] >= 0, "rmse 应该 >= 0"
    assert metrics["mae"] >= 0, "mae 应该 >= 0"
    assert metrics["r2"] <= 1, "r2 应该 <= 1"

    print(f"  [OK] rmse: {metrics['rmse']:.4f}")
    print(f"  [OK] mae: {metrics['mae']:.4f}")
    print(f"  [OK] r2: {metrics['r2']:.4f}")
    print("  [OK] 测试通过\n")


def test_compare_models():
    """测试多模型对比"""
    print("测试 5: 多模型对比...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=2000,
        n_classes=2,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.7,
    )

    models = ["logreg", "rf", "lgbm"]
    results = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=models,
    )

    assert len(results) == len(models), "结果数量应该等于模型数量"
    assert "model" in results.columns, "结果应该包含 model 列"

    print(f"  [OK] 对比了 {len(models)} 个模型")
    print("  [OK] 结果预览:")
    for _, row in results.iterrows():
        print(f"    {row['model']}: accuracy={row['accuracy']:.4f}, auc={row['auc']:.4f}")
    print("  [OK] 测试通过\n")


def test_learning_curve():
    """测试学习曲线"""
    print("测试 6: 学习曲线...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=3000,
        n_classes=2,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.6,
    )

    df = simulate_learning_curve(
        model_name="lgbm",
        task_config=task_config,
        difficulty=difficulty,
        train_sizes=np.array([0.2, 0.5, 1.0]),
        acc_10=0.6,
        acc_100=0.8,
    )

    assert len(df) == 3, "应该有 3 个训练点"
    assert "train_ratio" in df.columns, "结果应该包含 train_ratio"
    assert "accuracy" in df.columns, "结果应该包含 accuracy"

    print(f"  [OK] 生成了 {len(df)} 个训练点")
    print("  [OK] 学习曲线预览:")
    for _, row in df.iterrows():
        print(f"    train_ratio={row['train_ratio']:.2f}, accuracy={row['accuracy']:.4f}")
    print("  [OK] 测试通过\n")


def test_difficulty_scan():
    """测试难度扫描"""
    print("测试 7: 难度扫描...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=2000,
        n_classes=2,
        random_state=42,
    )

    base_difficulty = DifficultyConfig(
        label_noise=0.05,
        feature_noise=0.1,
    )

    separability_values = np.array([0.3, 0.5, 0.7])

    df = scan_difficulty(
        task_config=task_config,
        model_name="lgbm",
        difficulty_param="separability",
        difficulty_values=separability_values,
        base_difficulty=base_difficulty,
        n_runs=2,
    )

    assert len(df) == len(separability_values), "结果数量应该等于参数值数量"
    assert "separability" in df.columns, "结果应该包含 separability 列"

    print(f"  [OK] 扫描了 {len(separability_values)} 个可分性值")
    print("  [OK] 扫描结果预览:")
    for _, row in df.iterrows():
        print(f"    separability={row['separability']:.1f}, accuracy_mean={row['accuracy_mean']:.4f}")
    print("  [OK] 测试通过\n")


def test_high_separability_high_auc():
    """验证逻辑：高可分性 → 高AUC"""
    print("测试 8: 验证逻辑 - 高可分性应该导致高AUC...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=3000,
        n_classes=2,
        random_state=42,
    )

    # 低可分性
    difficulty_low = DifficultyConfig(separability=0.3)
    simulator_low = MLSimulator(task_config, difficulty_low, "rf")
    metrics_low = simulator_low.simulate()

    # 高可分性
    difficulty_high = DifficultyConfig(separability=0.8)
    simulator_high = MLSimulator(task_config, difficulty_high, "rf")
    metrics_high = simulator_high.simulate()

    print(f"  低可分性 (0.3): auc={metrics_low['auc']:.4f}")
    print(f"  高可分性 (0.8): auc={metrics_high['auc']:.4f}")

    assert metrics_high['auc'] > metrics_low['auc'], "高可分性应该导致更高的AUC"
    print("  [OK] 逻辑验证通过\n")


def test_label_noise_decreases_performance():
    """验证逻辑：高标签噪声 → 性能下降"""
    print("测试 9: 验证逻辑 - 高标签噪声应该降低性能...")

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=3000,
        n_classes=2,
        random_state=42,
    )

    # 低噪声
    difficulty_low = DifficultyConfig(
        separability=0.7,
        label_noise=0.01,
    )
    simulator_low = MLSimulator(task_config, difficulty_low, "lgbm")
    metrics_low = simulator_low.simulate()

    # 高噪声
    difficulty_high = DifficultyConfig(
        separability=0.7,
        label_noise=0.3,
    )
    simulator_high = MLSimulator(task_config, difficulty_high, "lgbm")
    metrics_high = simulator_high.simulate()

    print(f"  低标签噪声 (0.01): accuracy={metrics_low['accuracy']:.4f}")
    print(f"  高标签噪声 (0.3): accuracy={metrics_high['accuracy']:.4f}")

    assert metrics_low['accuracy'] > metrics_high['accuracy'], "高标签噪声应该降低准确率"
    print("  [OK] 逻辑验证通过\n")


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "ML Simulator 测试套件" + " " * 24 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    try:
        test_basic_binary_classification()
        test_multiclass_classification()
        test_imbalanced_classification()
        test_regression()
        test_compare_models()
        test_learning_curve()
        test_difficulty_scan()
        test_high_separability_high_auc()
        test_label_noise_decreases_performance()

        print("=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
