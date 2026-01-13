import numpy as np
import pandas as pd

# ---------------------------------------
# 1. 基础：标签与概率模拟（支持二分类 / 多分类）
# ---------------------------------------

def _binary_auc(y_true, y_score):
    """
    纯 numpy 实现 ROC AUC（用于二分类）。
    y_true: 0/1
    y_score: 预测为正类的概率
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score)

    # 正负样本数
    pos = (y_true == 1)
    neg = (y_true == 0)
    n_pos = pos.sum()
    n_neg = neg.sum()
    if n_pos == 0 or n_neg == 0:
        return np.nan

    # 使用秩统计法计算 AUC
    order = np.argsort(y_score)
    ranks = np.argsort(order) + 1  # 1 ~ n
    sum_ranks_pos = ranks[pos].sum()
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)

def _multiclass_auc_ovr_macro(y_true, y_prob, n_classes):
    """
    多分类 one-vs-rest AUC 的 macro 平均。
    """
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



def _precision_recall_f1_multiclass(y_true, y_pred, n_classes):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    precisions = []
    recalls = []
    f1s = []
    for c in range(n_classes):
        tp = np.logical_and(y_true == c, y_pred == c).sum()
        fp = np.logical_and(y_true != c, y_pred == c).sum()
        fn = np.logical_and(y_true == c, y_pred != c).sum()

        precision = tp / (tp + fp + 1e-12)
        recall = tp / (tp + fn + 1e-12)
        f1 = 2 * precision * recall / (precision + recall + 1e-12)

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1s))
    return macro_precision, macro_recall, macro_f1
def generate_labels(n_samples=5000, n_classes=2, random_state=None, class_probs=None):
    """
    生成多分类标签，0 ~ n_classes-1。
    如果 class_probs 为 None，则均匀分布；否则根据给定的类别比例生成不均衡标签。
    """
    rng = np.random.default_rng(random_state)
    if class_probs is None:
        # 原始行为：各类均匀
        y = rng.integers(0, n_classes, size=n_samples)
    else:
        class_probs = np.asarray(class_probs, dtype=float)
        if class_probs.size != n_classes:
            raise ValueError("class_probs 长度必须等于 n_classes")
        class_probs = class_probs / class_probs.sum()
        y = rng.choice(n_classes, size=n_samples, p=class_probs)
    return y



def simulate_probabilities(
    y_true,
    n_classes=None,
    target_accuracy=0.7,
    random_state=None,
    class_difficulty_scale=0.02,
):
    """
    根据目标 accuracy 来模拟预测概率，支持二分类 / 多分类。

    参数
    ----
    y_true : 1D array-like, shape (n_samples,)
        真实标签，取值 0 ~ n_classes-1
    n_classes : int or None
        类别数，默认从 y_true 的最大值 + 1 推断
    target_accuracy : float
        希望得到的整体准确率（0~1），用于控制预测对错比例
    class_difficulty_scale : float
        控制"类别难度"的波动幅度，不同类别的 recall 会不同，更贴近真实情况。
    """
    y_true = np.asarray(y_true).astype(int)
    if n_classes is None:
        n_classes = int(np.max(y_true)) + 1

    n_samples = len(y_true)
    rng = np.random.default_rng(random_state)

    # -------- 控制整体 accuracy：设定 per-class recall，而不是全局统一精度 --------
    target_accuracy = float(target_accuracy)
    target_accuracy = max(0.0, min(1.0, target_accuracy))

    # 为每个类别生成一个难度偏移，使得 recall 在不同类别之间存在差异
    raw_offsets = rng.normal(0.0, class_difficulty_scale, size=n_classes)
    # 保证整体平均仍然绕 target_accuracy 摇摆
    raw_offsets -= raw_offsets.mean()
    recall_per_class = target_accuracy + raw_offsets
    recall_per_class = np.clip(recall_per_class, 0.01, 0.99)

    # -------- 非对称混淆矩阵：错误时更容易混成某些特定类别 --------
    confusion_matrix = np.zeros((n_classes, n_classes), dtype=float)
    for c in range(n_classes):
        # Dirichlet 采样得到倾向分布，降低对自身的概率（错误时不会预测为自己）
        alpha = np.ones(n_classes)
        alpha[c] = 0.1
        conf = rng.dirichlet(alpha)
        conf[c] = 0.0
        conf /= conf.sum()
        confusion_matrix[c] = conf

    # -------- 按类别 recall 决定每个样本是否预测正确 --------
    correct_mask = np.zeros(n_samples, dtype=bool)
    for c in range(n_classes):
        idx = np.where(y_true == c)[0]
        if idx.size == 0:
            continue
        r_c = recall_per_class[c]
        rand_vals = rng.random(idx.size)
        correct_idx = idx[rand_vals < r_c]
        correct_mask[correct_idx] = True

    # -------- 构造预测标签（包含系统性混淆）--------
    y_pred = np.empty(n_samples, dtype=int)
    for i, true_label in enumerate(y_true):
        if correct_mask[i]:
            y_pred[i] = true_label
        else:
            probs_wrong = confusion_matrix[true_label]
            y_pred[i] = rng.choice(n_classes, p=probs_wrong)

    # -------- 再根据预测标签构造概率分布 --------
    probs = np.empty((n_samples, n_classes), dtype=float)

    # 基础置信度依然随 target_accuracy 提升，但不再是固定值
    base_p_main = 0.55 + 0.3 * target_accuracy  # 约在 [0.55, 0.85]
    base_p_main = max(0.5, min(0.9, base_p_main))

    # 类别层面的置信度差异
    class_conf_offset = rng.normal(0.0, 0.05, size=n_classes)

    for i in range(n_samples):
        pred = y_pred[i]
        # 引入类别差异 + 样本级微小噪声
        p_main = base_p_main + class_conf_offset[pred] + rng.normal(0.0, 0.02)
        p_main = float(np.clip(p_main, 0.35, 0.98))

        # 将其余概率质量随机分配给其他类别，避免完全对称
        other_classes = [c for c in range(n_classes) if c != pred]
        alpha = np.ones(len(other_classes))
        other_probs = rng.dirichlet(alpha)

        probs[i, :] = 0.0
        probs[i, other_classes] = (1.0 - p_main) * other_probs
        probs[i, pred] = p_main

    return probs



def compute_metrics(y_true, y_prob, n_classes=2):
    """
    根据类别数自动选择二分类 / 多分类指标并返回一个 dict。

    二分类：
        - accuracy
        - auc
        - precision
        - recall
        - f1

    多分类：
        - accuracy
        - auc_ovr_macro  (one-vs-rest macro AUC)
        - macro_precision
        - macro_recall
        - macro_f1
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob)
    if y_prob.ndim == 1:
        # 如果只给了正类概率，自动构造两列
        y_prob = np.vstack([1 - y_prob, y_prob]).T

    n_classes = int(n_classes)
    if n_classes <= 1:
        raise ValueError("n_classes 必须 >= 2")

    y_pred = np.argmax(y_prob, axis=1)
    accuracy = float(np.mean(y_pred == y_true))

    if n_classes == 2:
        auc = _binary_auc(y_true, y_prob[:, 1])
        precision, recall, f1 = _precision_recall_f1_binary(y_true, y_pred)
        return {
            "n_classes": 2,
            "accuracy": accuracy,
            "auc": auc,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    else:
        macro_precision, macro_recall, macro_f1 = _precision_recall_f1_multiclass(
            y_true, y_pred, n_classes
        )
        auc_ovr_macro = _multiclass_auc_ovr_macro(y_true, y_prob, n_classes)
        return {
            "n_classes": n_classes,
            "accuracy": accuracy,
            "auc_ovr_macro": auc_ovr_macro,
            "macro_precision": macro_precision,
            "macro_recall": macro_recall,
            "macro_f1": macro_f1,
        }


# ---------------------------------------
#  学习曲线模拟（10% ~ 100%）
# ---------------------------------------

def simulate_learning_curve(
    model_name,
    n_classes=2,
    n_samples_val=3000,
    train_sizes=np.linspace(0.1, 1.0, 10),
    acc_10=0.5,
    acc_100=0.9,
    alpha=3,              # 学习速度（第一刀）
    noise_std_start=0.03,   # 小数据噪声（第二刀）
    noise_std_end=0.002,
    random_state=None,
):
    """
    模拟更真实的学习曲线（10% ~ 100%）：
    - 使用指数饱和而非线性增长
    - 小数据噪声大，大数据噪声小
    - accuracy 是软目标而非绝对控制
    """
    rng = np.random.default_rng(random_state)

    # 固定验证集，且引入类别不均衡，使 macro 指标与 accuracy 产生差异
    class_probs = rng.dirichlet(alpha=np.linspace(1.0, 1.1, n_classes))
    y_val = generate_labels(
        n_samples=n_samples_val,
        n_classes=n_classes,
        random_state=rng.integers(1e9),
        
        # class_probs=class_probs,
    )

    train_sizes = np.asarray(train_sizes, dtype=float)
    s_min, s_max = train_sizes.min(), train_sizes.max()

    records = []

    for s in train_sizes:
        # ---------- 归一化进度 ----------
        if s_max > s_min:
            t = (s - s_min) / (s_max - s_min)
        else:
            t = 1.0

        # ---------- 第一刀：指数饱和学习曲线 ----------
        base_acc = acc_10 + (acc_100 - acc_10) * (1 - np.exp(-alpha * t))

        # ---------- 第二刀：异方差噪声 ----------
        noise_std = noise_std_start * (1 - t) + noise_std_end
        noisy_acc = base_acc + rng.normal(0, noise_std)

        # 约束到合法区间
        target_accuracy = float(np.clip(noisy_acc, 0.0, 1.0))

        # ---------- 第三刀（轻量）：accuracy 只是“期望表现” ----------
        probs_val = simulate_probabilities(
            y_val,
            n_classes=n_classes,
            target_accuracy=target_accuracy,
            random_state=rng.integers(1e9),
        )

        metrics = compute_metrics(y_val, probs_val, n_classes=n_classes)
        metrics["train_ratio"] = float(s)
        metrics["target_accuracy"] = target_accuracy
        metrics["base_accuracy"] = base_acc  # 可选：方便你画“真实趋势 vs 观测值”

        records.append(metrics)

    df = pd.DataFrame(records)
    cols = (
        ["train_ratio", "base_accuracy", "target_accuracy"]
        + [c for c in df.columns if c not in ("train_ratio", "base_accuracy", "target_accuracy")]
    )
    return df[cols]



# ---------------------------------------
# 5. 示例：如何使用
# ---------------------------------------
# 这里仍然用“模型画像”来给出在 100% 训练数据下的大致 accuracy（数值越大越好）

EMB_MODEL_PROFILES = {
    "dnn": {"acc_10": 0.6865,"acc_100": 0.7989},
    "catboost": {"acc_10": 0.6571,"acc_100": 0.7516},
    "logreg": {"acc_10": 0.6558,"acc_100": 0.7189},
    "nb": {"acc_10": 0.5812,"acc_100": 0.64},
    "dt": {"acc_10": 0.5322,"acc_100": 0.6124},
    "rf": {"acc_10": 0.653,"acc_100": 0.721},
    "xgboost": {"acc_10": 0.672,"acc_100": 0.7553},
    "lgbm": {"acc_10": 0.677,"acc_100": 0.7613},
}

import os
NORM_MODEL_PROFILES = {
    "dnn": {"acc_10": 0.6265,"acc_100": 0.7289},
    "catboost": {"acc_10": 0.6571,"acc_100": 0.7116},
    "logreg": {"acc_10": 0.6128,"acc_100": 0.7198},
    "nb": {"acc_10": 0.5212,"acc_100": 0.6124},
    "dt": {"acc_10": 0.5422,"acc_100": 0.6007},
    "rf": {"acc_10": 0.5953,"acc_100": 0.651},
    "xgboost": {"acc_10": 0.612,"acc_100": 0.7153},
    "lgbm": {"acc_10": 0.6657,"acc_100": 0.6923},
}
target_name = ["embedding_1280","norm_200"][0]
for target_name in ["embedding_1280","norm_200"]:

    if target_name == "embedding_1280":
        target_profiles = EMB_MODEL_PROFILES
    else:
        target_profiles = NORM_MODEL_PROFILES    
    total_results = {}
    for model in target_profiles:
        model_profile = target_profiles[model]
        df_lc_multi = simulate_learning_curve(
            model,
            n_classes=3,
            n_samples_val=4000,
            acc_10=model_profile["acc_10"],
            acc_100=model_profile["acc_100"],
            random_state=42,
        )
        total_results[model]=df_lc_multi

    dfs = []
    for model_name, df in total_results.items():
        df = df.copy()  # 防止原地修改
        df.insert(0, "model_name", model_name)  # 在第0列插入
        dfs.append(df)

    # 如果只有一个模型，其实 concat 也没问题
    final_df = pd.concat(dfs, ignore_index=True)
    os.makedirs("sim_data",exist_ok=True)
    # 保存为 csv
    final_df.to_csv(f"sim_data/{target_name}_learning_curve.csv", index=False, encoding="utf-8-sig")