"""
ML Simulator Web Application
Flask 后端服务 - 提供 RESTful API
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from typing import Dict, List, Any
import json

from ml_simulator import (
    TaskConfig,
    DifficultyConfig,
    RegressionConfig,
    MLSimulator,
    simulate_learning_curve,
    compare_models,
    scan_difficulty,
    TaskType,
    PREDEFINED_MODEL_PROFILES,
)

app = Flask(__name__)
CORS(app)  # 允许跨域请求


# =============================================================================
# 路由：页面
# =============================================================================

@app.route('/')
def index():
    """首页 - 主界面"""
    return render_template('index.html')


@app.route('/learning_curve')
def learning_curve():
    """学习曲线页面"""
    return render_template('learning_curve.html')


@app.route('/difficulty_scan')
def difficulty_scan():
    """难度扫描页面"""
    return render_template('difficulty_scan.html')


# =============================================================================
# API：获取配置信息
# =============================================================================

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取所有可用的模型列表及其能力画像"""
    models_info = {}
    for name, profile in PREDEFINED_MODEL_PROFILES.items():
        models_info[name] = {
            'bias': profile.bias,
            'variance': profile.variance,
            'capacity': profile.capacity,
            'noise_tolerance': profile.noise_tolerance,
            'supported_tasks': profile.supported_tasks,  # 添加支持的任务类型
        }
    return jsonify({
        'success': True,
        'models': models_info
    })


@app.route('/api/task_types', methods=['GET'])
def get_task_types():
    """获取支持的任务类型"""
    return jsonify({
        'success': True,
        'task_types': [
            {'value': 'binary', 'label': '二分类'},
            {'value': 'multiclass', 'label': '多分类'},
            {'value': 'regression', 'label': '回归'},
        ]
    })


# =============================================================================
# API：核心模拟功能
# =============================================================================

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    执行模拟（支持单次运行和交叉验证）

    请求体：
    {
        "task_type": "binary",
        "num_samples": 5000,
        "n_classes": 2,
        "label_distribution": null,
        "models": ["lgbm", "rf", "logreg"],
        "difficulty": {
            "separability": 0.7,
            "label_noise": 0.05,
            "feature_noise": 0.1,
            "nonlinearity": 0.3,
            "spurious_correlation": 0.3
        },
        "custom_profile": {  // 可选：自定义模型画像
            "bias": 0.3,
            "variance": 0.3,
            "capacity": 0.8,
            "noise_tolerance": 0.6
        },
        "random_state": 42,
        "experiment_config": {  // 实验方案配置
            "type": "single" | "cv" | "learning_curve",
            "n_folds": 5,  // 交叉验证折数
            "train_sizes": [0.1, 0.2, 0.3, 0.5, 0.7, 1.0],  // 学习曲线训练集比例
            "n_runs": 3  // 学习曲线每个点重复次数
        }
    }
    """
    try:
        data = request.get_json()

        # 解析任务类型
        task_type_str = data.get('task_type', 'binary')
        task_type = TaskType(task_type_str)

        # 获取实验方案配置
        experiment_config = data.get('experiment_config', {})
        experiment_type = experiment_config.get('type', 'single')

        # 创建任务配置
        base_random_state = int(data.get('random_state', 42))

        task_config = TaskConfig(
            task_type=task_type,
            num_samples=int(data.get('num_samples', 5000)),
            n_classes=int(data.get('n_classes', 2)),
            label_distribution=data.get('label_distribution'),
            random_state=base_random_state,
        )

        # 创建难度配置
        difficulty_data = data.get('difficulty', {})
        difficulty = DifficultyConfig(
            separability=float(difficulty_data.get('separability', 0.6)),
            label_noise=float(difficulty_data.get('label_noise', 0.1)),
            feature_noise=float(difficulty_data.get('feature_noise', 0.2)),
            nonlinearity=float(difficulty_data.get('nonlinearity', 0.7)),
            spurious_correlation=float(difficulty_data.get('spurious_correlation', 0.3)),
        )

        # 获取模型列表
        model_names = data.get('models', ['lgbm'])

        # 处理模型配置
        models_config = data.get('models_config', {})
        custom_profile_data = data.get('custom_profile')
        model_profiles = {}

        from ml_simulator import ModelProfile

        if models_config:
            for model_name in model_names:
                if model_name in models_config:
                    config = models_config[model_name]
                    profile = ModelProfile(
                        bias=float(config.get('bias', 0.5)),
                        variance=float(config.get('variance', 0.3)),
                        capacity=float(config.get('capacity', 0.7)),
                        noise_tolerance=float(config.get('noise_tolerance', 0.5)),
                    )
                    model_profiles[model_name] = profile
        elif custom_profile_data:
            custom_profile = ModelProfile(
                bias=float(custom_profile_data.get('bias', 0.5)),
                variance=float(custom_profile_data.get('variance', 0.3)),
                capacity=float(custom_profile_data.get('capacity', 0.7)),
                noise_tolerance=float(custom_profile_data.get('noise_tolerance', 0.5)),
            )
            for model_name in model_names:
                model_profiles[model_name] = custom_profile

        # 根据实验方案类型执行不同的逻辑
        if experiment_type == 'cv':
            # 交叉验证：运行多次，返回统计结果
            n_folds = int(experiment_config.get('n_folds', 5))
            all_results = []

            for fold in range(n_folds):
                # 每折使用不同的random_state
                fold_task_config = TaskConfig(
                    task_type=task_config.task_type,
                    num_samples=task_config.num_samples,
                    n_classes=task_config.n_classes,
                    label_distribution=task_config.label_distribution,
                    random_state=base_random_state + fold,
                )

                fold_results = compare_models(
                    task_config=fold_task_config,
                    difficulty=difficulty,
                    model_names=model_names,
                    custom_profiles=model_profiles if model_profiles else None,
                )
                fold_results['fold'] = fold
                all_results.append(fold_results)

            # 合并所有折的结果
            all_df = pd.concat(all_results, ignore_index=True)

            # 计算统计量（均值和标准差）
            numeric_cols = [c for c in all_df.columns if c not in ['model', 'fold', 'task_type']]

            stats = all_df.groupby('model')[numeric_cols].agg(['mean', 'std'])
            stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
            stats = stats.reset_index()

            # 保留单次结果用于详细查看
            single_results = all_df.to_dict('records')

            return jsonify({
                'success': True,
                'experiment_type': 'cv',
                'n_folds': n_folds,
                'results': stats.to_dict('records'),  # 统计结果
                'single_results': single_results,  # 所有折的详细结果
            })

        elif experiment_type == 'learning_curve':
            # 学习曲线：不同训练集大小下的性能
            train_sizes_data = experiment_config.get('train_sizes', [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
            train_sizes = np.array(train_sizes_data)
            n_runs = int(experiment_config.get('n_runs', 3))

            # 获取用户自定义的学习曲线参数（如果有）
            lc_params = experiment_config.get('lc_params', {})

            # 学习曲线参数（用户自定义或默认值）
            alpha = float(lc_params.get('alpha', 2.5))  # 学习速度
            user_acc_10 = lc_params.get('acc_10')  # 用户指定的10%准确率
            user_acc_100 = lc_params.get('acc_100')  # 用户指定的100%准确率
            noise_std_start = float(lc_params.get('noise_std_start', 0.02))  # 小数据时的噪声
            noise_std_end = 0.005  # 大数据时的噪声

            all_results = []
            rng = np.random.default_rng(base_random_state)

            # 获取训练集大小的归一化范围
            s_min, s_max = train_sizes.min(), train_sizes.max()

            for model_name in model_names:
                profile = model_profiles.get(model_name) if model_profiles else model_name

                # 如果用户没有指定准确率，则根据模型能力估算
                if user_acc_10 is None or user_acc_100 is None:
                    # 获取模型能力参数
                    if isinstance(profile, str):
                        model_profile_obj = PREDEFINED_MODEL_PROFILES[profile]
                    else:
                        model_profile_obj = profile

                    base_capacity = model_profile_obj.capacity
                    base_variance = model_profile_obj.variance
                    base_bias = model_profile_obj.bias

                    # 估算10%和100%数据时的性能
                    acc_10 = user_acc_10 if user_acc_10 is not None else (0.35 + base_capacity * 0.25 - base_variance * 0.15)
                    acc_100 = user_acc_100 if user_acc_100 is not None else (0.45 + base_capacity * 0.50 - base_bias * 0.1)
                else:
                    # 使用用户指定的值
                    acc_10 = user_acc_10
                    acc_100 = user_acc_100

                # 确保在合理范围内
                acc_10 = np.clip(acc_10, 0.2, 0.8)
                acc_100 = np.clip(acc_100, 0.4, 0.99)

                # 确保大数据性能更好
                if acc_100 <= acc_10:
                    acc_100 = acc_10 + 0.15

                for train_size in train_sizes:
                    # 归一化进度（0到1）
                    if s_max > s_min:
                        t = (train_size - s_min) / (s_max - s_min)
                    else:
                        t = 1.0

                    for run in range(n_runs):
                        # 指数饱和学习曲线
                        base_acc = acc_10 + (acc_100 - acc_10) * (1 - np.exp(-alpha * t))

                        # 添加噪声（小数据时噪声更大，结果更不稳定）
                        noise_std = noise_std_start * (1 - t) + noise_std_end
                        noisy_acc = base_acc + rng.normal(0, noise_std)
                        noisy_acc = np.clip(noisy_acc, 0.2, 0.98)

                        # 调整多个难度参数以匹配目标准确率
                        # separability: 主要控制可分性
                        # label_noise: 小数据时标签噪声影响更大
                        # feature_noise: 小数据时特征噪声影响更大
                        label_noise_factor = 1.0 + (1.0 - t) * 0.5  # 小数据时增加50%噪声影响
                        feature_noise_factor = 1.0 + (1.0 - t) * 0.3

                        adjusted_difficulty = DifficultyConfig(
                            separability=float(noisy_acc),
                            label_noise=min(0.5, difficulty.label_noise * label_noise_factor),
                            feature_noise=min(0.5, difficulty.feature_noise * feature_noise_factor),
                            nonlinearity=difficulty.nonlinearity,
                            spurious_correlation=difficulty.spurious_correlation,
                        )

                        # 使用完整的样本量（性能变化通过难度调整实现）
                        simulator = MLSimulator(
                            task_config=task_config,
                            difficulty=adjusted_difficulty,
                            model_profile=profile,
                        )
                        metrics = simulator.simulate()
                        metrics['model'] = model_name
                        metrics['train_size'] = float(train_size)
                        metrics['run'] = run
                        all_results.append(metrics)

            lc_df = pd.DataFrame(all_results)

            # 计算统计量
            numeric_cols = [c for c in lc_df.columns if c not in ['model', 'train_size', 'run', 'task_type']]
            lc_stats = lc_df.groupby(['model', 'train_size'])[numeric_cols].agg(['mean', 'std'])
            lc_stats.columns = ['_'.join(col).strip() for col in lc_stats.columns.values]
            lc_stats = lc_stats.reset_index()

            return jsonify({
                'success': True,
                'experiment_type': 'learning_curve',
                'results': lc_stats.to_dict('records'),
                'single_results': lc_df.to_dict('records'),
            })

        else:
            # 单次运行
            results = compare_models(
                task_config=task_config,
                difficulty=difficulty,
                model_names=model_names,
                custom_profiles=model_profiles if model_profiles else None,
            )

            results_dict = results.to_dict('records')

            return jsonify({
                'success': True,
                'experiment_type': 'single',
                'results': results_dict,
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@app.route('/api/learning_curve', methods=['POST'])
def api_learning_curve():
    """
    生成学习曲线

    请求体：
    {
        "task_type": "binary",
        "models": {
            "lgbm": {"acc_10": 0.67, "acc_100": 0.82},
            "dnn": {"acc_10": 0.60, "acc_100": 0.85}
        },
        "difficulty": {...},
        "train_sizes": [0.1, 0.2, ..., 1.0],
        "alpha": 3,
        "noise_std_start": 0.03,
        "noise_std_end": 0.002
    }
    """
    try:
        data = request.get_json()

        # 解析任务类型
        task_type_str = data.get('task_type', 'binary')
        task_type = TaskType(task_type_str)

        # 创建任务配置
        task_config = TaskConfig(
            task_type=task_type,
            num_samples=int(data.get('num_samples', 5000)),
            n_classes=int(data.get('n_classes', 2)),
            label_distribution=data.get('label_distribution'),
            random_state=int(data.get('random_state', 42)),
        )

        # 创建难度配置
        difficulty_data = data.get('difficulty', {})
        difficulty = DifficultyConfig(
            separability=float(difficulty_data.get('separability', 0.6)),
            label_noise=float(difficulty_data.get('label_noise', 0.1)),
            feature_noise=float(difficulty_data.get('feature_noise', 0.2)),
            nonlinearity=float(difficulty_data.get('nonlinearity', 0.7)),
            spurious_correlation=float(difficulty_data.get('spurious_correlation', 0.3)),
        )

        # 获取模型配置
        models_config = data.get('models', {})
        train_sizes = np.array(data.get('train_sizes', np.linspace(0.1, 1.0, 10)))

        alpha = float(data.get('alpha', 3))
        noise_std_start = float(data.get('noise_std_start', 0.03))
        noise_std_end = float(data.get('noise_std_end', 0.002))

        # 为每个模型生成学习曲线
        all_results = []
        for model_name, model_params in models_config.items():
            df = simulate_learning_curve(
                model_name=model_name,
                task_config=task_config,
                difficulty=difficulty,
                train_sizes=train_sizes,
                acc_10=float(model_params.get('acc_10', 0.6)),
                acc_100=float(model_params.get('acc_100', 0.8)),
                alpha=alpha,
                noise_std_start=noise_std_start,
                noise_std_end=noise_std_end,
            )
            df['model'] = model_name
            all_results.append(df)

        result_df = pd.concat(all_results, ignore_index=True)

        # 转换为 JSON 友好格式
        results_dict = result_df.to_dict('records')

        return jsonify({
            'success': True,
            'results': results_dict,
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@app.route('/api/scan_difficulty', methods=['POST'])
def api_scan_difficulty():
    """
    扫描难度参数对性能的影响

    请求体：
    {
        "task_type": "binary",
        "model": "lgbm",
        "difficulty_param": "separability",
        "difficulty_values": [0.1, 0.2, ..., 0.9],
        "base_difficulty": {...},
        "n_runs": 3
    }
    """
    try:
        data = request.get_json()

        # 解析任务类型
        task_type_str = data.get('task_type', 'binary')
        task_type = TaskType(task_type_str)

        # 创建任务配置
        task_config = TaskConfig(
            task_type=task_type,
            num_samples=int(data.get('num_samples', 5000)),
            n_classes=int(data.get('n_classes', 2)),
            label_distribution=data.get('label_distribution'),
            random_state=int(data.get('random_state', 42)),
        )

        # 获取参数
        model_name = data.get('model', 'lgbm')
        difficulty_param = data.get('difficulty_param', 'separability')
        difficulty_values = np.array(data.get('difficulty_values', np.linspace(0.1, 0.9, 9)))
        base_difficulty_data = data.get('base_difficulty', {})
        n_runs = int(data.get('n_runs', 3))

        # 创建基础难度配置
        base_difficulty = DifficultyConfig(
            separability=float(base_difficulty_data.get('separability', 0.6)),
            label_noise=float(base_difficulty_data.get('label_noise', 0.1)),
            feature_noise=float(base_difficulty_data.get('feature_noise', 0.2)),
            nonlinearity=float(base_difficulty_data.get('nonlinearity', 0.7)),
            spurious_correlation=float(base_difficulty_data.get('spurious_correlation', 0.3)),
        )

        # 执行扫描
        df = scan_difficulty(
            task_config=task_config,
            model_name=model_name,
            difficulty_param=difficulty_param,
            difficulty_values=difficulty_values,
            base_difficulty=base_difficulty,
            n_runs=n_runs,
        )

        # 转换为 JSON 友好格式
        results_dict = df.to_dict('records')

        return jsonify({
            'success': True,
            'results': results_dict,
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# =============================================================================
# API：数据导出
# =============================================================================

@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """
    导出结果为 CSV

    请求体：同 /api/simulate
    """
    try:
        data = request.get_json()

        # 执行模拟（复用逻辑）
        task_type_str = data.get('task_type', 'binary')
        task_type = TaskType(task_type_str)

        task_config = TaskConfig(
            task_type=task_type,
            num_samples=int(data.get('num_samples', 5000)),
            n_classes=int(data.get('n_classes', 2)),
            label_distribution=data.get('label_distribution'),
            random_state=int(data.get('random_state', 42)),
        )

        difficulty_data = data.get('difficulty', {})
        difficulty = DifficultyConfig(
            separability=float(difficulty_data.get('separability', 0.6)),
            label_noise=float(difficulty_data.get('label_noise', 0.1)),
            feature_noise=float(difficulty_data.get('feature_noise', 0.2)),
            nonlinearity=float(difficulty_data.get('nonlinearity', 0.7)),
            spurious_correlation=float(difficulty_data.get('spurious_correlation', 0.3)),
        )

        model_names = data.get('models', ['lgbm'])
        results = compare_models(
            task_config=task_config,
            difficulty=difficulty,
            model_names=model_names,
        )

        # 转换为 CSV
        csv = results.to_csv(index=False)

        return jsonify({
            'success': True,
            'csv': csv,
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# =============================================================================
# 启动服务器
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("ML Simulator Web Server")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=8080)
