"""
快速测试脚本 - 验证 Flask 应用依赖和基本功能
"""

import sys

def test_imports():
    """测试所有必要的导入"""
    print("=" * 60)
    print("测试 1: 导入必要的模块")
    print("=" * 60)

    modules = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'numpy': 'NumPy',
        'pandas': 'Pandas',
    }

    failed = []
    for module_name, display_name in modules.items():
        try:
            __import__(module_name)
            print(f"[OK] {display_name}")
        except ImportError:
            print(f"[FAIL] {display_name} - 未安装")
            failed.append(display_name)

    if failed:
        print(f"\n[错误] 缺少以下模块: {', '.join(failed)}")
        print("请运行: pip install -r requirements.txt")
        return False

    print("[SUCCESS] 所有模块导入成功\n")
    return True


def test_ml_simulator():
    """测试 ml_simulator 模块"""
    print("=" * 60)
    print("测试 2: 导入 ml_simulator")
    print("=" * 60)

    try:
        from ml_simulator import (
            TaskConfig, DifficultyConfig, MLSimulator,
            compare_models, TaskType
        )
        print("[OK] ml_simulator 导入成功")

        # 快速功能测试
        print("\n运行快速功能测试...")
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
        print(f"[OK] 模拟运行成功")
        print(f"     Accuracy: {metrics['accuracy']:.4f}")
        print(f"     AUC: {metrics['auc']:.4f}")
        print("\n[SUCCESS] ml_simulator 工作正常\n")
        return True

    except Exception as e:
        print(f"[FAIL] ml_simulator 测试失败: {e}\n")
        return False


def test_flask_app():
    """测试 Flask 应用"""
    print("=" * 60)
    print("测试 3: 检查 Flask 应用文件")
    print("=" * 60)

    import os

    required_files = [
        ('app.py', 'Flask 应用'),
        ('templates/index.html', '主页模板'),
        ('static/js/index.js', '主页脚本'),
        ('static/css/style.css', '样式文件'),
    ]

    missing = []
    for file_path, description in required_files:
        if os.path.exists(file_path):
            print(f"[OK] {description}: {file_path}")
        else:
            print(f"[FAIL] {description} 缺失: {file_path}")
            missing.append(file_path)

    if missing:
        print(f"\n[错误] 缺少文件: {', '.join(missing)}\n")
        return False

    print("\n[SUCCESS] 所有文件存在\n")
    return True


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Flask 应用测试套件" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    all_passed = True

    # 测试 1: 模块导入
    if not test_imports():
        all_passed = False

    # 测试 2: ml_simulator
    if not test_ml_simulator():
        all_passed = False

    # 测试 3: Flask 文件
    if not test_flask_app():
        all_passed = False

    # 总结
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] 所有测试通过！")
        print("")
        print("现在可以启动 Flask 服务器：")
        print("  Windows: 双击 start_web.bat")
        print("  Linux/Mac: bash start_web.sh")
        print("  或直接运行: python app.py")
    else:
        print("[FAIL] 部分测试失败，请修复后再启动服务器")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
