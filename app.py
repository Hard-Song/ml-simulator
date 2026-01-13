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
    执行单次模拟

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
        "random_state": 42
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

        # 获取模型列表
        model_names = data.get('models', ['lgbm'])

        # 处理模型配置
        models_config = data.get('models_config', {})  # 每个模型的独立配置
        custom_profile_data = data.get('custom_profile')  # 全局自定义配置（兼容旧版）
        model_profiles = {}

        from ml_simulator import ModelProfile

        # 优先使用models_config（每个模型独立配置）
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
            # 兼容旧版：全局自定义配置
            custom_profile = ModelProfile(
                bias=float(custom_profile_data.get('bias', 0.5)),
                variance=float(custom_profile_data.get('variance', 0.3)),
                capacity=float(custom_profile_data.get('capacity', 0.7)),
                noise_tolerance=float(custom_profile_data.get('noise_tolerance', 0.5)),
            )
            for model_name in model_names:
                model_profiles[model_name] = custom_profile

        # 执行多模型对比
        results = compare_models(
            task_config=task_config,
            difficulty=difficulty,
            model_names=model_names,
            custom_profiles=model_profiles if model_profiles else None,
        )

        # 转换为 JSON 友好格式
        results_dict = results.to_dict('records')

        return jsonify({
            'success': True,
            'results': results_dict,
        })

    except Exception as e:
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
