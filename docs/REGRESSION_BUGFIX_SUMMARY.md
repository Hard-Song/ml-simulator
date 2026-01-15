# 回归任务按钮无响应问题修复总结

## 问题描述

**发现时间**: 2025-01-14

在切换到"回归任务"标签页后，点击"运行模拟"、"导出CSV"等按钮没有任何反应，控制台无错误提示。

## 根本原因

回归任务的HTML界面和模型配置已经实现，但**JavaScript代码中缺少回归任务相关的事件监听器和处理函数**。具体包括：

1. 回归任务的按钮没有绑定事件监听器
2. 回归任务的图表没有初始化
3. 显示结果的函数不支持回归任务
4. 实验方案切换的UI更新函数缺失

## 问题分析

### 缺失的事件监听器

以下按钮在HTML中定义了，但没有绑定事件：

- `regressionRunBtn` - 运行模拟按钮
- `regressionExportBtn` - 导出CSV按钮
- `regressionExpandAllBtn` - 展开全部按钮
- `regressionCollapseAllBtn` - 收起全部按钮
- `regressionResetAllBtn` - 重置参数按钮
- `regressionExperimentType` - 实验方案类型下拉框

### 缺失的JavaScript函数

以下函数未实现：

- `initRegressionCharts()` - 初始化回归图表
- `updateRegressionUIForExperimentType()` - 更新实验方案UI
- `updateRegressionBarCharts()` - 更新柱状图
- `updateRegressionLearningCurveCharts()` - 更新学习曲线图表

### 函数参数不完整

以下函数需要支持回归任务但缺少参数：

- `runSimulation()` - 只支持分类任务的按钮
- `displayResults()` - 只更新分类任务的表格和图表
- `updateTable()` - 只处理分类任务表格
- `updateCharts()` - 只处理分类任务图表

## 修复方案

### 1. 添加事件监听器

在 `bindEvents()` 函数中添加：

```javascript
// 运行按钮（回归任务）
document.getElementById('regressionRunBtn').addEventListener('click', runSimulation);

// 导出按钮（回归任务）
document.getElementById('regressionExportBtn').addEventListener('click', exportCSV);

// 展开全部（回归任务）
document.getElementById('regressionExpandAllBtn').addEventListener('click', function() {
    document.querySelectorAll('#regressionModelCardsContainer .collapse').forEach(collapse => {
        new bootstrap.Collapse(collapse, { show: true });
    });
});

// 收起全部（回归任务）
document.getElementById('regressionCollapseAllBtn').addEventListener('click', function() {
    document.querySelectorAll('#regressionModelCardsContainer .collapse').forEach(collapse => {
        new bootstrap.Collapse(collapse, { hide: true });
    });
});

// 重置所有（回归任务）
document.getElementById('regressionResetAllBtn').addEventListener('click', function() {
    if (confirm('确定要重置所有模型参数吗？')) {
        for (const modelName of Object.keys(modelProfiles)) {
            if (!customModels.includes(modelName)) {
                resetModelProfile(modelName);
            }
        }
        showAlert('所有模型参数已重置', 'success');
    }
});

// 实验方案类型切换（回归任务）
document.getElementById('regressionExperimentType').addEventListener('change', function() {
    updateRegressionUIForExperimentType(this.value);
});
```

### 2. 添加图表初始化函数

```javascript
function initRegressionCharts() {
    // 柱状图1 (MAE)
    const ctx1 = document.getElementById('regressionChart1').getContext('2d');
    charts.regressionChart1 = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'MAE',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                errorBars: null
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        },
        plugins: [{
            id: 'errorBars',
            afterDatasetsDraw: (chart) => drawErrorBars(chart)
        }]
    });

    // 柱状图2 (RMSE)
    const ctx2 = document.getElementById('regressionChart2').getContext('2d');
    charts.regressionChart2 = new Chart(ctx2, {
        // ... 类似配置
    });

    // 雷达图
    const radarCtx = document.getElementById('regressionRadarChart').getContext('2d');
    charts.regressionRadar = new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: ['1-MAE', '1-RMSE', 'R²'],
            datasets: []
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });
}
```

### 3. 修改运行模拟函数

```javascript
async function runSimulation() {
    // 根据当前任务模式选择对应的按钮
    const isRegression = currentTaskMode === 'regression';
    const runBtnId = isRegression ? 'regressionRunBtn' : 'runBtn';
    const runBtnTextId = isRegression ? 'regressionRunBtnText' : 'runBtnText';
    const runBtnSpinnerId = isRegression ? 'regressionRunBtnSpinner' : 'runBtnSpinner';

    const runBtn = document.getElementById(runBtnId);
    const runBtnText = document.getElementById(runBtnTextId);
    const runBtnSpinner = document.getElementById(runBtnSpinnerId);

    // ... 后续逻辑保持不变
}
```

### 4. 添加UI更新函数

```javascript
function updateRegressionUIForExperimentType(experimentType) {
    const cvConfig = document.getElementById('regressionCvConfig');
    const lcConfigSimple = document.getElementById('regressionLcConfigSimple');
    const lcConfig = document.getElementById('regressionLcConfig');

    // 隐藏所有配置
    cvConfig.style.display = 'none';
    lcConfigSimple.style.display = 'none';
    lcConfig.style.display = 'none';

    // 根据类型显示对应配置
    if (experimentType === 'cv') {
        cvConfig.style.display = 'block';
    } else if (experimentType === 'learning_curve') {
        lcConfigSimple.style.display = 'block';
        lcConfig.style.display = 'block';
    }
}
```

### 5. 修改结果显示函数

```javascript
function displayResults(results, experimentType) {
    const isRegression = currentTaskMode === 'regression';
    updateTable(results, experimentType, isRegression);
    updateCharts(results, experimentType, isRegression);
}

function updateTable(results, experimentType, isRegression = false) {
    // 根据任务类型选择对应的表格元素
    const tableId = isRegression ? 'regressionResultsTable' : 'resultsTable';
    const theadId = isRegression ? 'regressionResultsTableHead' : 'resultsTableHead';

    const taskType = isRegression ? 'regression' : document.getElementById('taskType').value;
    const thead = document.querySelector(`#${theadId} tr`);
    const tbody = document.querySelector(`#${tableId} tbody`);

    // ... 后续逻辑
}
```

### 6. 添加回归图表更新函数

```javascript
function updateRegressionBarCharts(results, isStatistical, colors) {
    const models = results.map(r => r.model.toUpperCase());

    const getValue = (row, metric) => {
        if (isStatistical) {
            return row[metric + '_mean'];
        }
        return row[metric];
    };

    const getError = (row, metric) => {
        if (isStatistical) {
            return row[metric + '_std'];
        }
        return 0;
    };

    document.getElementById('regressionChart1Title').textContent = 'MAE 对比';
    document.getElementById('regressionChart2Title').textContent = 'RMSE 对比';

    // Chart 1: MAE
    charts.regressionChart1.data.labels = models;
    charts.regressionChart1.data.datasets[0].label = 'MAE';
    charts.regressionChart1.data.datasets[0].data = results.map(r => getValue(r, 'mae'));
    charts.regressionChart1.data.datasets[0].backgroundColor = colors[0];
    charts.regressionChart1.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'mae')) : null;
    charts.regressionChart1.update();

    // Chart 2: RMSE
    charts.regressionChart2.data.labels = models;
    charts.regressionChart2.data.datasets[0].label = 'RMSE';
    charts.regressionChart2.data.datasets[0].data = results.map(r => getValue(r, 'rmse'));
    charts.regressionChart2.data.datasets[0].backgroundColor = colors[1];
    charts.regressionChart2.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'rmse')) : null;
    charts.regressionChart2.update();

    // Radar chart
    charts.regressionRadar.data.labels = ['1-MAE', '1-RMSE', 'R²'];
    charts.regressionRadar.data.datasets = results.map((r, i) => ({
        label: r.model.toUpperCase(),
        data: [1 - getValue(r, 'mae'), 1 - getValue(r, 'rmse'), getValue(r, 'r2')],
        backgroundColor: colors[i % colors.length],
    }));
    charts.regressionRadar.update();
}

function updateRegressionLearningCurveCharts(results, colors) {
    // 按模型分组
    const modelGroups = {};
    results.forEach(r => {
        if (!modelGroups[r.model]) {
            modelGroups[r.model] = [];
        }
        modelGroups[r.model].push(r);
    });

    // 获取训练集大小
    const trainSizes = [...new Set(results.map(r => r.train_size))].sort((a, b) => a - b);
    const labels = trainSizes.map(s => (s * 100).toFixed(0) + '%');

    // 使用MAE和RMSE作为主要指标
    const metric1 = 'mae_mean';
    const metric2 = 'rmse_mean';

    document.getElementById('regressionChart1Title').textContent = 'MAE 学习曲线';
    document.getElementById('regressionChart2Title').textContent = 'RMSE 学习曲线';

    // 创建数据集
    const datasets1 = Object.keys(modelGroups).map((model, i) => ({
        label: model.toUpperCase(),
        data: trainSizes.map(size => {
            const row = modelGroups[model].find(r => r.train_size === size);
            return row ? row[metric1] : null;
        }),
        borderColor: colors[i % colors.length].replace('0.6', '1'),
        backgroundColor: colors[i % colors.length],
        tension: 0.3,
        fill: false,
    }));

    const datasets2 = Object.keys(modelGroups).map((model, i) => ({
        label: model.toUpperCase(),
        data: trainSizes.map(size => {
            const row = modelGroups[model].find(r => r.train_size === size);
            return row ? row[metric2] : null;
        }),
        borderColor: colors[i % colors.length].replace('0.6', '1'),
        backgroundColor: colors[i % colors.length],
        tension: 0.3,
        fill: false,
    }));

    // 更新图表类型为折线图
    charts.regressionChart1.config.type = 'line';
    charts.regressionChart1.data.labels = labels;
    charts.regressionChart1.data.datasets = datasets1;
    charts.regressionChart1.update();

    charts.regressionChart2.config.type = 'line';
    charts.regressionChart2.data.labels = labels;
    charts.regressionChart2.data.datasets = datasets2;
    charts.regressionChart2.update();

    // 雷达图不适用于学习曲线
    charts.regressionRadar.data.labels = [];
    charts.regressionRadar.data.datasets = [];
    charts.regressionRadar.update();
}
```

## 测试验证

修复后，回归任务的以下功能应该正常工作：

1. ✅ 点击"运行模拟"按钮，按钮显示加载状态
2. ✅ 发送请求到后端，获取模拟结果
3. ✅ 表格正确显示回归指标（MAE, RMSE, R²）
4. ✅ 图表正确更新（柱状图或学习曲线折线图）
5. ✅ 雷达图显示综合性能
6. ✅ 点击"导出CSV"按钮，下载结果文件
7. ✅ 展开/收起全部模型卡片
8. ✅ 重置模型参数
9. ✅ 切换实验方案类型（单次运行/交叉验证/学习曲线）

## 代码变更统计

### 修改的文件

- `static/js/index.js` - 主要修改文件

### 新增代码

- 新增函数：6个
  - `initRegressionCharts()`
  - `updateRegressionUIForExperimentType()`
  - `updateRegressionBarCharts()`
  - `updateRegressionLearningCurveCharts()`

### 修改的函数

- 修改函数：5个
  - `bindEvents()` - 添加回归任务事件监听器
  - `runSimulation()` - 支持回归任务按钮
  - `displayResults()` - 添加isRegression参数
  - `updateTable()` - 添加isRegression参数
  - `updateCharts()` - 添加isRegression参数

### 新增事件监听器

- 6个按钮/选择框的事件监听器

## 经验教训

### 问题根源

这是一个典型的**前后端实现不完整**问题：

1. HTML界面已经实现（回归任务面板）
2. 后端API已经支持回归任务
3. 但前端JavaScript缺少对应的处理逻辑

### 预防措施

1. **功能完整性检查**
   - 新增功能时，确保HTML、CSS、JavaScript、后端API都完整实现
   - 使用功能清单逐一验证

2. **事件绑定检查**
   - 每个按钮都应该有对应的事件监听器
   - 在`bindEvents()`函数中集中管理所有事件绑定

3. **图表初始化检查**
   - 每个canvas元素都应该有对应的图表初始化代码
   - 在`DOMContentLoaded`时初始化所有图表

4. **单元测试**
   - 为关键功能添加测试用例
   - 特别是任务切换、结果显示等场景

### 代码组织建议

将回归任务和分类任务的代码更好地组织：

```javascript
// 建议的代码结构
const TaskUI = {
    classification: {
        init: () => { /* 初始化分类任务UI */ },
        updateCharts: () => { /* 更新分类任务图表 */ },
        // ...
    },
    regression: {
        init: () => { /* 初始化回归任务UI */ },
        updateCharts: () => { /* 更新回归任务图表 */ },
        // ...
    }
};
```

## 相关文档

- [METRICS_UPDATE_SUMMARY.md](./METRICS_UPDATE_SUMMARY.md) - 指标系统重构
- [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - 项目整体架构
- [README_WEB.md](./README_WEB.md) - Web界面使用说明

## 修复时间

- **问题发现**: 2025-01-14
- **问题诊断**: 2025-01-14
- **修复完成**: 2025-01-14
- **文档更新**: 2025-01-14

---

## 补充修复 (2025-01-15)

### 问题描述

在`export_csv`函数中发现了未定义的`reg_difficulty`变量问题。

### 根本原因

`/api/export/csv`函数中缺少了回归难度配置的创建代码，导致在交叉验证和单次运行导出时使用了未定义的`reg_difficulty`变量。

### 修复方案

在`export_csv`函数的第634-645行添加回归难度配置创建代码：

```python
# 创建回归难度配置（如果需要）
reg_difficulty = None
if task_type == TaskType.REGRESSION:
    reg_data = data.get('regression_difficulty', {})
    reg_difficulty = RegressionDifficulty(
        signal_to_noise=float(reg_data.get('signal_to_noise', 1.0)),
        function_complexity=float(reg_data.get('function_complexity', 0.5)),
        noise_level=float(reg_data.get('noise_level', 0.2)),
        heteroscedastic=bool(reg_data.get('heteroscedastic', True)),
        n_features=int(reg_data.get('n_features', 10)),
        feature_noise=float(reg_data.get('feature_noise', 0.05)),
    )
```

同时在单次运行导出分支（第818-829行）添加`reg_difficulty`参数传递。

### 影响范围

- 修复文件: `app.py`
- 修复位置: `export_csv`函数
- 影响功能: 回归任务的CSV导出功能

### 验证方法

```bash
python -m py_compile app.py  # 语法检查通过
```

### 相关问题

这个问题与之前在`/api/simulate`函数中修复的问题类似，表明在添加回归任务支持时，需要确保所有使用`compare_models`函数的地方都传递了`reg_difficulty`参数。
