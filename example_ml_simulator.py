"""
ML Simulator 使用示例
展示如何使用 ml_simulator 模拟各种机器学习场景
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ml_simulator import (
    # 类
    TaskConfig,
    DifficultyConfig,
    RegressionConfig,
    MLSimulator,

    # 函数
    simulate_learning_curve,
    compare_models,
    scan_difficulty,

    # 预定义模型
    PREDEFINED_MODEL_PROFILES,

    # 枚举
    TaskType,
)


# =============================================================================
# 示例 1: 基础二分类模拟
# =============================================================================

def example_1_basic_binary_classification():
    """基础二分类模拟"""
    print("=" * 60)
    print("示例 1: 基础二分类模拟")
    print("=" * 60)

    # 配置任务
    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=42,
    )

    # 配置难度
    difficulty = DifficultyConfig(
        separability=0.7,      # 类间可分性
        label_noise=0.05,       # 标签噪声
        feature_noise=0.1,      # 特征噪声
        nonlinearity=0.3,       # 非线性
    )

    # 选择模型
    model_name = "lgbm"

    # 创建模拟器并运行
    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile=model_name,
    )

    metrics = simulator.simulate()

    print(f"\n模型: {model_name}")
    print(f"指标:")
    for key, value in metrics.items():
        if key != "n_classes":
            print(f"  {key}: {value:.4f}")

    return metrics


# =============================================================================
# 示例 2: 多分类 + 类别不均衡
# =============================================================================

def example_2_imbalanced_multiclass():
    """多分类任务 + 类别不均衡"""
    print("\n" + "=" * 60)
    print("示例 2: 多分类 + 类别不均衡")
    print("=" * 60)

    # 配置任务（长尾分布）
    task_config = TaskConfig(
        task_type=TaskType.MULTICLASS,
        num_samples=10000,
        n_classes=5,
        label_distribution=[0.5, 0.25, 0.15, 0.07, 0.03],  # 长尾分布
        random_state=42,
    )

    # 高难度配置
    difficulty = DifficultyConfig(
        separability=0.5,
        label_noise=0.1,
        feature_noise=0.2,
        nonlinearity=0.7,
    )

    # 对比不同模型
    models = ["logreg", "rf", "lgbm", "dnn"]

    print("\n对比不同模型在不均衡多分类任务上的表现：")
    print("-" * 60)

    results = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=models,
    )

    print(results.to_string(index=False))

    return results


# =============================================================================
# 示例 3: 学习曲线模拟
# =============================================================================

def example_3_learning_curves():
    """学习曲线：对比不同模型的数据效率"""
    print("\n" + "=" * 60)
    print("示例 3: 学习曲线模拟")
    print("=" * 60)

    # 配置任务
    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=42,
    )

    # 中等难度
    difficulty = DifficultyConfig(
        separability=0.6,
        label_noise=0.08,
        feature_noise=0.15,
        nonlinearity=0.5,
    )

    # 定义模型及其在10%/100%数据下的表现
    models_acc = {
        "logreg": (0.62, 0.75),
        "rf": (0.65, 0.78),
        "lgbm": (0.67, 0.82),
        "dnn": (0.60, 0.85),  # DNN小数据差，大数据强
        "transformer": (0.55, 0.88),  # Transformer小数据更差
    }

    all_results = []

    for model_name, (acc_10, acc_100) in models_acc.items():
        print(f"\n模拟 {model_name} 学习曲线...")
        df = simulate_learning_curve(
            model_name=model_name,
            task_config=task_config,
            difficulty=difficulty,
            train_sizes=np.linspace(0.1, 1.0, 10),
            acc_10=acc_10,
            acc_100=acc_100,
        )
        df["model"] = model_name
        all_results.append(df)

    result_df = pd.concat(all_results, ignore_index=True)

    # 打印关键点
    print("\n学习曲线关键点（10%, 50%, 100% 数据）：")
    print("-" * 60)
    key_points = result_df[result_df["train_ratio"].isin([0.1, 0.5, 1.0])]
    pivot = key_points.pivot(index="model", columns="train_ratio", values="accuracy")
    print(pivot.to_string())

    return result_df


# =============================================================================
# 示例 4: 难度扫描 - 类间可分性对性能的影响
# =============================================================================

def example_4_separability_scan():
    """扫描类间可分性对模型性能的影响"""
    print("\n" + "=" * 60)
    print("示例 4: 类间可分性扫描")
    print("=" * 60)

    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=42,
    )

    base_difficulty = DifficultyConfig(
        label_noise=0.05,
        feature_noise=0.1,
        nonlinearity=0.3,
    )

    # 扫描可分性从 0.1 到 0.9
    separability_values = np.linspace(0.1, 0.9, 9)

    models = ["svm", "rf", "lgbm", "dnn"]

    all_results = []

    for model_name in models:
        print(f"\n扫描 {model_name}...")
        df = scan_difficulty(
            task_config=task_config,
            model_name=model_name,
            difficulty_param="separability",
            difficulty_values=separability_values,
            base_difficulty=base_difficulty,
            n_runs=3,
        )
        df["model"] = model_name
        all_results.append(df)

    result_df = pd.concat(all_results, ignore_index=True)

    # 打印关键结果
    print("\n不同可分性下的模型准确率：")
    print("-" * 60)
    pivot_df = result_df.pivot(index="separability", columns="model", values="accuracy_mean")
    print(pivot_df.to_string())

    return result_df


# =============================================================================
# 示例 5: 回归任务模拟
# =============================================================================

def example_5_regression():
    """回归任务模拟"""
    print("\n" + "=" * 60)
    print("示例 5: 回归任务模拟")
    print("=" * 60)

    task_config = TaskConfig(
        task_type=TaskType.REGRESSION,
        num_samples=3000,
        random_state=42,
    )

    difficulty = DifficultyConfig(
        separability=0.6,      # 在回归中影响信号强度
        feature_noise=0.2,
    )

    reg_config = RegressionConfig(
        function_complexity=0.7,
        noise_level=0.3,
        heteroscedastic=True,  # 异方差
    )

    models = ["logreg", "rf", "dnn"]

    print("\n对比不同模型在回归任务上的表现：")
    print("-" * 60)

    results = compare_models(
        task_config=task_config,
        difficulty=difficulty,
        model_names=models,
        reg_config=reg_config,
    )

    print(results.to_string(index=False))

    return results


# =============================================================================
# 示例 6: 极端场景 - 高AUC但低Recall
# =============================================================================

def example_6_high_auc_low_recall():
    """模拟一个特殊场景：AUC很高但Recall很低"""
    print("\n" + "=" * 60)
    print("示例 6: 特殊场景 - 高AUC低Recall")
    print("=" * 60)
    print("场景说明：通过阈值偏移和类别不均衡，模拟AUC高但Recall低的情况")
    print("-" * 60)

    # 极度不均衡
    task_config = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=10000,
        n_classes=2,
        label_distribution=[0.95, 0.05],  # 95% 负类, 5% 正类
        random_state=42,
    )

    # 高可分性但有标签噪声
    difficulty = DifficultyConfig(
        separability=0.8,  # 高可分性 → 高AUC
        label_noise=0.15,  # 但正类样本容易预测错误 → 低Recall
        feature_noise=0.1,
    )

    simulator = MLSimulator(
        task_config=task_config,
        difficulty=difficulty,
        model_profile="lgbm",
    )

    metrics = simulator.simulate()

    print(f"\n指标:")
    for key, value in metrics.items():
        if key != "n_classes":
            print(f"  {key}: {value:.4f}")

    print("\n现象解释：")
    print("  - 高可分性 → AUC高（排序能力好）")
    print("  - 标签噪声 + 不均衡 → 正类容易被预测为负类 → Recall低")
    print("  - 这是真实场景中常见的现象！")

    return metrics


# =============================================================================
# 示例 7: 模拟"过拟合"现象
# =============================================================================

def example_7_overfitting():
    """模拟过拟合：训练集表现好，测试集表现差"""
    print("\n" + "=" * 60)
    print("示例 7: 模拟过拟合现象")
    print("=" * 60)

    # 相同任务，但训练集和测试集的难度不同
    task_config_train = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=42,
    )

    task_config_test = TaskConfig(
        task_type=TaskType.BINARY,
        num_samples=5000,
        n_classes=2,
        random_state=43,
    )

    # 训练集：低难度（模型能学好）
    difficulty_train = DifficultyConfig(
        separability=0.8,
        label_noise=0.02,
        feature_noise=0.05,
        nonlinearity=0.3,
    )

    # 测试集：高难度（有更多噪声）
    difficulty_test = DifficultyConfig(
        separability=0.6,
        label_noise=0.1,
        feature_noise=0.2,
        nonlinearity=0.5,
    )

    # 使用高容量、高方差模型（如DNN）
    model_name = "dnn"

    # 训练集性能
    simulator_train = MLSimulator(
        task_config=task_config_train,
        difficulty=difficulty_train,
        model_profile=model_name,
    )
    metrics_train = simulator_train.simulate()

    # 测试集性能
    simulator_test = MLSimulator(
        task_config=task_config_test,
        difficulty=difficulty_test,
        model_profile=model_name,
    )
    metrics_test = simulator_test.simulate()

    print(f"\n模型: {model_name}")
    print("\n训练集指标:")
    for key, value in metrics_train.items():
        if key != "n_classes":
            print(f"  {key}: {value:.4f}")

    print("\n测试集指标:")
    for key, value in metrics_test.items():
        if key != "n_classes":
            print(f"  {key}: {value:.4f}")

    print(f"\n过拟合程度:")
    print(f"  Accuracy下降: {metrics_train['accuracy'] - metrics_test['accuracy']:.4f}")
    print(f"  AUC下降: {metrics_train['auc'] - metrics_test['auc']:.4f}")

    return metrics_train, metrics_test


# =============================================================================
# 主函数
# =============================================================================

def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "ML Simulator 使用示例" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")

    # 运行示例（可以选择性注释掉某些示例）
    example_1_basic_binary_classification()
    example_2_imbalanced_multiclass()
    example_3_learning_curves()
    example_4_separability_scan()
    example_5_regression()
    example_6_high_auc_low_recall()
    example_7_overfitting()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
