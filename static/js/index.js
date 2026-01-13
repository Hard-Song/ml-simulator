// 全局变量
let charts = {};
let lastResults = null;
let modelProfiles = {};  // 存储每个模型的能力参数
let customModels = [];  // 存储自定义模型名称

// 预定义模型能力画像
const DEFAULT_PROFILES = {
    'svm': { bias: 0.5, variance: 0.2, capacity: 0.6, noise_tolerance: 0.4 },
    'rf': { bias: 0.3, variance: 0.4, capacity: 0.7, noise_tolerance: 0.8 },
    'lgbm': { bias: 0.3, variance: 0.3, capacity: 0.8, noise_tolerance: 0.6 },
    'dnn': { bias: 0.2, variance: 0.7, capacity: 0.95, noise_tolerance: 0.5 },
    'cnn': { bias: 0.3, variance: 0.5, capacity: 0.85, noise_tolerance: 0.6 },
    'rnn': { bias: 0.4, variance: 0.6, capacity: 0.8, noise_tolerance: 0.5 },
    'transformer': { bias: 0.2, variance: 0.9, capacity: 0.98, noise_tolerance: 0.4 },
    'logreg': { bias: 0.5, variance: 0.1, capacity: 0.5, noise_tolerance: 0.5 },
    'xgboost': { bias: 0.3, variance: 0.3, capacity: 0.8, noise_tolerance: 0.7 },
    'catboost': { bias: 0.3, variance: 0.25, capacity: 0.78, noise_tolerance: 0.75 },
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化模型卡片
    initializeModelCards();

    // 绑定事件
    bindEvents();

    // 初始化图表
    initCharts();
});

// 初始化模型卡片
function initializeModelCards() {
    const container = document.getElementById('modelCardsContainer');
    container.innerHTML = '';

    // 首先添加预定义模型
    for (const [modelName, defaultProfile] of Object.entries(DEFAULT_PROFILES)) {
        modelProfiles[modelName] = { ...defaultProfile };
        const col = document.createElement('div');
        col.className = 'col-lg-4 col-md-6';
        col.innerHTML = generateModelCardHTML(modelName, defaultProfile, false);
        container.appendChild(col);
    }

    // 然后添加自定义模型
    customModels.forEach(modelName => {
        const col = document.createElement('div');
        col.className = 'col-lg-4 col-md-6';
        col.innerHTML = generateModelCardHTML(modelName, modelProfiles[modelName], true);
        container.appendChild(col);
    });

    // 重新绑定事件
    bindCardEvents();
}

// 生成模型卡片HTML
function generateModelCardHTML(modelName, profile, isCustom) {
    const modelId = `model_${modelName}`;
    const deleteBtn = isCustom ? `
        <button class="btn btn-sm btn-outline-danger float-end"
                onclick="deleteCustomModel('${modelName}')"
                title="删除模型">
            🗑️ 删除
        </button>
    ` : '';

    return `
        <div class="model-card" id="${modelId}_card">
            <div class="model-card-header" id="${modelId}_header">
                <div class="d-flex align-items-center w-100">
                    <div class="me-3" style="cursor: pointer;" onclick="toggleModelSelection('${modelName}')">
                        <input class="form-check-input model-select-checkbox"
                               type="checkbox"
                               value="${modelName}"
                               id="${modelId}_checkbox"
                               onclick="event.stopPropagation()">
                    </div>
                    <span class="fw-bold" style="cursor: pointer;" onclick="toggleModelSelection('${modelName}')">
                        ${modelName.toUpperCase()}
                        ${isCustom ? ' <span class="badge bg-warning text-dark">自定义</span>' : ''}
                    </span>
                </div>
                <div class="d-flex align-items-center">
                    ${deleteBtn}
                    <span class="collapse-button ms-2" data-bs-toggle="collapse" data-bs-target="#${modelId}_body">
                        ▼
                    </span>
                </div>
            </div>
            <div class="collapse" id="${modelId}_body">
                <div class="model-card-body">
                    <div class="row">
                        <div class="col-6">
                            <div class="param-slider">
                                <label>
                                    Bias (偏差)
                                    <span class="param-value" id="${modelId}_biasValue">${profile.bias}</span>
                                </label>
                                <input type="range" class="form-range"
                                       id="${modelId}_bias"
                                       min="0" max="1" step="0.05"
                                       value="${profile.bias}"
                                       oninput="updateModelParam('${modelName}', 'bias', this.value)">
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="param-slider">
                                <label>
                                    Variance (方差)
                                    <span class="param-value" id="${modelId}_varianceValue">${profile.variance}</span>
                                </label>
                                <input type="range" class="form-range"
                                       id="${modelId}_variance"
                                       min="0" max="1" step="0.05"
                                       value="${profile.variance}"
                                       oninput="updateModelParam('${modelName}', 'variance', this.value)">
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="param-slider">
                                <label>
                                    Capacity (能力)
                                    <span class="param-value" id="${modelId}_capacityValue">${profile.capacity}</span>
                                </label>
                                <input type="range" class="form-range"
                                       id="${modelId}_capacity"
                                       min="0" max="1" step="0.05"
                                       value="${profile.capacity}"
                                       oninput="updateModelParam('${modelName}', 'capacity', this.value)">
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="param-slider">
                                <label>
                                    Noise Tol (容错)
                                    <span class="param-value" id="${modelId}_noise_toleranceValue">${profile.noise_tolerance}</span>
                                </label>
                                <input type="range" class="form-range"
                                       id="${modelId}_noise_tolerance"
                                       min="0" max="1" step="0.05"
                                       value="${profile.noise_tolerance}"
                                       oninput="updateModelParam('${modelName}', 'noise_tolerance', this.value)">
                            </div>
                        </div>
                    </div>
                    <div class="text-center mt-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="resetModelProfile('${modelName}')">
                            🔄 重置为默认值
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 绑定卡片事件（在DOM插入后）
function bindCardEvents() {
    // 卡片头部点击事件已经在HTML中通过onclick绑定
    // 这里不需要额外绑定
}

// 切换模型选择状态
function toggleModelSelection(modelName) {
    const checkbox = document.getElementById(`model_${modelName}_checkbox`);
    const card = document.getElementById(`model_${modelName}_card`);
    const header = document.getElementById(`model_${modelName}_header`);

    checkbox.checked = !checkbox.checked;

    if (checkbox.checked) {
        card.classList.add('selected');
        header.style.backgroundColor = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        header.style.color = 'white';
    } else {
        card.classList.remove('selected');
        header.style.backgroundColor = '';
        header.style.color = '';
    }
}

// 更新模型参数
function updateModelParam(modelName, param, value) {
    value = parseFloat(value);
    modelProfiles[modelName][param] = value;
    document.getElementById(`model_${modelName}_${param}Value`).textContent = value.toFixed(2);
}

// 重置模型参数为默认值
function resetModelProfile(modelName) {
    let defaultProfile;

    if (customModels.includes(modelName)) {
        // 自定义模型没有默认值，使用中等配置
        defaultProfile = { bias: 0.5, variance: 0.5, capacity: 0.7, noise_tolerance: 0.5 };
    } else {
        defaultProfile = DEFAULT_PROFILES[modelName];
    }

    modelProfiles[modelName] = { ...defaultProfile };

    // 更新UI
    ['bias', 'variance', 'capacity', 'noise_tolerance'].forEach(param => {
        const slider = document.getElementById(`model_${modelName}_${param}`);
        const valueSpan = document.getElementById(`model_${modelName}_${param}Value`);
        slider.value = defaultProfile[param];
        valueSpan.textContent = defaultProfile[param].toFixed(2);
    });

    showAlert(`${modelName.toUpperCase()} 参数已重置`, 'info');
}

// 删除自定义模型
function deleteCustomModel(modelName) {
    if (confirm(`确定要删除自定义模型 "${modelName.toUpperCase()}" 吗？`)) {
        // 从数组中移除
        const index = customModels.indexOf(modelName);
        if (index > -1) {
            customModels.splice(index, 1);
        }

        // 删除配置
        delete modelProfiles[modelName];

        // 重新渲染所有卡片
        initializeModelCards();

        showAlert(`${modelName.toUpperCase()} 已删除`, 'success');
    }
}

// 添加自定义模型
function addCustomModel() {
    const nameInput = document.getElementById('newModelName');
    const modelName = nameInput.value.trim().toLowerCase();

    // 验证名称
    if (!modelName) {
        showAlert('请输入模型名称', 'warning');
        return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(modelName)) {
        showAlert('模型名称只能包含字母、数字、下划线', 'danger');
        return;
    }

    if (modelName in DEFAULT_PROFILES || customModels.includes(modelName)) {
        showAlert('模型名称已存在', 'danger');
        return;
    }

    // 获取参数
    const profile = {
        bias: parseFloat(document.getElementById('newModelBias').value),
        variance: parseFloat(document.getElementById('newModelVariance').value),
        capacity: parseFloat(document.getElementById('newModelCapacity').value),
        noise_tolerance: parseFloat(document.getElementById('newModelNoiseTol').value),
    };

    // 添加到列表
    customModels.push(modelName);
    modelProfiles[modelName] = profile;

    // 重新渲染
    initializeModelCards();

    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('addModelModal'));
    modal.hide();

    // 清空表单
    document.getElementById('addModelForm').reset();
    resetNewModelSliders();

    showAlert(`${modelName.toUpperCase()} 已添加`, 'success');
}

// 重置新模型滑块
function resetNewModelSliders() {
    document.getElementById('newModelBias').value = 0.5;
    document.getElementById('newModelVariance').value = 0.3;
    document.getElementById('newModelCapacity').value = 0.7;
    document.getElementById('newModelNoiseTol').value = 0.5;

    document.getElementById('newModelBiasValue').textContent = '0.5';
    document.getElementById('newModelVarianceValue').textContent = '0.3';
    document.getElementById('newModelCapacityValue').textContent = '0.7';
    document.getElementById('newModelNoiseTolValue').textContent = '0.5';
}

// 绑定事件
function bindEvents() {
    // 难度参数滑块
    bindSlider('numSamples', 'numSamplesValue');
    bindSlider('separability', 'separabilityValue');
    bindSlider('labelNoise', 'labelNoiseValue');
    bindSlider('featureNoise', 'featureNoiseValue');
    bindSlider('nonlinearity', 'nonlinearityValue');

    // 新模型参数滑块
    bindSlider('newModelBias', 'newModelBiasValue');
    bindSlider('newModelVariance', 'newModelVarianceValue');
    bindSlider('newModelCapacity', 'newModelCapacityValue');
    bindSlider('newModelNoiseTol', 'newModelNoiseTolValue');

    // 任务类型切换
    document.getElementById('taskType').addEventListener('change', function() {
        updateUIForTaskType(this.value);
    });

    // 展开全部
    document.getElementById('expandAllBtn').addEventListener('click', function() {
        document.querySelectorAll('#modelCardsContainer .collapse').forEach(collapse => {
            new bootstrap.Collapse(collapse, { show: true });
        });
        // 更新箭头方向
        setTimeout(() => {
            document.querySelectorAll('.collapse-button').forEach(btn => {
                btn.textContent = '▲';
            });
        }, 350);
    });

    // 收起全部
    document.getElementById('collapseAllBtn').addEventListener('click', function() {
        document.querySelectorAll('#modelCardsContainer .collapse').forEach(collapse => {
            new bootstrap.Collapse(collapse, { hide: true });
        });
        // 更新箭头方向
        setTimeout(() => {
            document.querySelectorAll('.collapse-button').forEach(btn => {
                btn.textContent = '▼';
            });
        }, 350);
    });

    // 重置所有
    document.getElementById('resetAllBtn').addEventListener('click', function() {
        if (confirm('确定要重置所有模型参数吗？')) {
            for (const modelName of Object.keys(modelProfiles)) {
                if (!customModels.includes(modelName)) {
                    resetModelProfile(modelName);
                }
            }
            showAlert('所有模型参数已重置', 'success');
        }
    });

    // 添加模型确认按钮
    document.getElementById('confirmAddModelBtn').addEventListener('click', addCustomModel);

    // 监听折叠事件，更新箭头方向
    document.getElementById('modelCardsContainer').addEventListener('hidden.bs.collapse', function(e) {
        const button = e.target.previousElementSibling?.querySelector('.collapse-button');
        if (button) {
            button.textContent = '▼';
        }
    });

    document.getElementById('modelCardsContainer').addEventListener('shown.bs.collapse', function(e) {
        const button = e.target.previousElementSibling?.querySelector('.collapse-button');
        if (button) {
            button.textContent = '▲';
        }
    });

    // 运行按钮
    document.getElementById('runBtn').addEventListener('click', runSimulation);

    // 导出按钮
    document.getElementById('exportBtn').addEventListener('click', exportCSV);
}

// 绑定滑块
function bindSlider(sliderId, valueId) {
    const slider = document.getElementById(sliderId);
    const value = document.getElementById(valueId);

    slider.addEventListener('input', function() {
        value.textContent = this.value;
    });
}

// 根据任务类型更新UI
function updateUIForTaskType(taskType) {
    const nClassesGroup = document.getElementById('nClassesGroup');
    const labelDistGroup = document.getElementById('labelDistGroup');

    if (taskType === 'regression') {
        nClassesGroup.style.display = 'none';
        labelDistGroup.style.display = 'none';
    } else if (taskType === 'binary') {
        nClassesGroup.style.display = 'none';
        labelDistGroup.style.display = 'block';
    } else {
        nClassesGroup.style.display = 'block';
        labelDistGroup.style.display = 'block';
    }
}

// 初始化图表
function initCharts() {
    // 柱状图1
    const ctx1 = document.getElementById('chart1').getContext('2d');
    charts.chart1 = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '准确率',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });

    // 柱状图2
    const ctx2 = document.getElementById('chart2').getContext('2d');
    charts.chart2 = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'F1',
                data: [],
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });

    // 雷达图
    const radarCtx = document.getElementById('radarChart').getContext('2d');
    charts.radar = new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: ['准确率', 'AUC', 'Precision', 'Recall', 'F1'],
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

// 运行模拟
async function runSimulation() {
    const runBtn = document.getElementById('runBtn');
    const runBtnText = document.getElementById('runBtnText');
    const runBtnSpinner = document.getElementById('runBtnSpinner');

    // 获取选中的模型
    const selectedModels = getSelectedModels();
    if (selectedModels.length === 0) {
        showAlert('请至少选择一个模型', 'warning');
        return;
    }

    // 显示加载状态
    runBtn.disabled = true;
    runBtnText.textContent = '运行中...';
    runBtnSpinner.classList.remove('d-none');

    try {
        // 构建请求数据
        const requestData = buildRequestData(selectedModels);

        // 发送请求
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (data.success) {
            lastResults = data.results;
            displayResults(data.results);
            showAlert('模拟完成！', 'success');
        } else {
            showAlert('模拟失败: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('请求失败: ' + error.message, 'danger');
    } finally {
        // 恢复按钮状态
        runBtn.disabled = false;
        runBtnText.textContent = '▶ 运行模拟';
        runBtnSpinner.classList.add('d-none');
    }
}

// 获取选中的模型
function getSelectedModels() {
    const checkboxes = document.querySelectorAll('.model-select-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// 构建请求数据
function buildRequestData(models) {
    const taskType = document.getElementById('taskType').value;
    const numSamples = parseInt(document.getElementById('numSamples').value);
    const nClasses = parseInt(document.getElementById('nClasses').value);
    const labelDistStr = document.getElementById('labelDistribution').value.trim();

    let labelDistribution = null;
    if (labelDistStr) {
        labelDistribution = labelDistStr.split(',').map(s => parseFloat(s.trim()));
    }

    const difficulty = {
        separability: parseFloat(document.getElementById('separability').value),
        label_noise: parseFloat(document.getElementById('labelNoise').value),
        feature_noise: parseFloat(document.getElementById('featureNoise').value),
        nonlinearity: parseFloat(document.getElementById('nonlinearity').value),
        spurious_correlation: 0.3,
    };

    // 构建每个模型的独立能力画像
    const models_config = {};
    models.forEach(modelName => {
        models_config[modelName] = modelProfiles[modelName];
    });

    return {
        task_type: taskType,
        num_samples: numSamples,
        n_classes: nClasses,
        label_distribution: labelDistribution,
        models: models,
        difficulty: difficulty,
        models_config: models_config,
        random_state: 42,
    };
}

// 显示结果
function displayResults(results) {
    updateTable(results);
    updateCharts(results);
}

// 更新表格
function updateTable(results) {
    const taskType = document.getElementById('taskType').value;
    const thead = document.querySelector('#resultsTableHead tr');
    const tbody = document.querySelector('#resultsTable tbody');

    // 清空表格
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // 根据任务类型设置表头
    let headers = [];
    let metrics = [];

    if (taskType === 'regression') {
        headers = ['模型', 'MAE', 'RMSE', 'R²'];
        metrics = ['mae', 'rmse', 'r2'];
    } else if (taskType === 'multiclass') {
        headers = ['模型', '准确率', 'Macro-F1', 'Weighted-F1', 'LogLoss', 'Top-3'];
        metrics = ['accuracy', 'macro_f1', 'weighted_f1', 'logloss', 'top_3_accuracy'];
    } else {  // binary
        headers = ['模型', '准确率', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'PR-AUC', 'LogLoss'];
        metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc', 'logloss'];
    }

    // 添加表头
    headers.forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        thead.appendChild(th);
    });

    // 添加数据行
    results.forEach(row => {
        const tr = document.createElement('tr');

        // 模型名称
        const modelCell = document.createElement('td');
        modelCell.textContent = row.model.toUpperCase();
        modelCell.style.fontWeight = 'bold';
        tr.appendChild(modelCell);

        // 指标数据
        metrics.forEach(metric => {
            const value = row[metric];
            if (value === undefined || value === null) {
                addCell(tr, 'N/A');
            } else if (metric === 'accuracy' || metric === 'top_3_accuracy' ||
                       metric === 'macro_f1' || metric === 'weighted_f1') {
                addCell(tr, (value * 100).toFixed(2) + '%');
            } else {
                addCell(tr, value.toFixed(4));
            }
        });

        tbody.appendChild(tr);
    });
}

// 添加单元格
function addCell(row, text) {
    const td = document.createElement('td');
    td.textContent = text;
    row.appendChild(td);
}

// 更新图表
function updateCharts(results) {
    const models = results.map(r => r.model.toUpperCase());
    const taskType = document.getElementById('taskType').value;

    const colors = [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(153, 102, 255, 0.6)',
    ];

    if (taskType === 'regression') {
        document.getElementById('chart1Title').textContent = 'MAE 对比';
        document.getElementById('chart2Title').textContent = 'RMSE 对比';

        charts.chart1.data.labels = models;
        charts.chart1.data.datasets[0].label = 'MAE';
        charts.chart1.data.datasets[0].data = results.map(r => r.mae);
        charts.chart1.data.datasets[0].backgroundColor = colors[0];
        charts.chart1.update();

        charts.chart2.data.labels = models;
        charts.chart2.data.datasets[0].label = 'RMSE';
        charts.chart2.data.datasets[0].data = results.map(r => r.rmse);
        charts.chart2.data.datasets[0].backgroundColor = colors[1];
        charts.chart2.update();

        charts.radar.data.labels = ['1-MAE', '1-RMSE', 'R²'];
        charts.radar.data.datasets = results.map((r, i) => ({
            label: r.model.toUpperCase(),
            data: [1 - r.mae, 1 - r.rmse, r.r2],
            backgroundColor: colors[i % colors.length],
        }));
        charts.radar.update();

    } else if (taskType === 'multiclass') {
        document.getElementById('chart1Title').textContent = '准确率对比';
        document.getElementById('chart2Title').textContent = 'Macro-F1 对比';

        charts.chart1.data.labels = models;
        charts.chart1.data.datasets[0].label = '准确率';
        charts.chart1.data.datasets[0].data = results.map(r => r.accuracy);
        charts.chart1.data.datasets[0].backgroundColor = colors[0];
        charts.chart1.update();

        charts.chart2.data.labels = models;
        charts.chart2.data.datasets[0].label = 'Macro-F1';
        charts.chart2.data.datasets[0].data = results.map(r => r.macro_f1);
        charts.chart2.data.datasets[0].backgroundColor = colors[1];
        charts.chart2.update();

        charts.radar.data.labels = ['准确率', 'Macro-F1', 'Weighted-F1', '1-LogLoss', 'Top-3'];
        charts.radar.data.datasets = results.map((r, i) => ({
            label: r.model.toUpperCase(),
            data: [r.accuracy, r.macro_f1, r.weighted_f1, 1 / (1 + r.logloss), r.top_3_accuracy],
            backgroundColor: colors[i % colors.length],
        }));
        charts.radar.update();

    } else {  // binary
        document.getElementById('chart1Title').textContent = 'ROC-AUC 对比';
        document.getElementById('chart2Title').textContent = 'PR-AUC 对比';

        charts.chart1.data.labels = models;
        charts.chart1.data.datasets[0].label = 'ROC-AUC';
        charts.chart1.data.datasets[0].data = results.map(r => r.roc_auc);
        charts.chart1.data.datasets[0].backgroundColor = colors[0];
        charts.chart1.update();

        charts.chart2.data.labels = models;
        charts.chart2.data.datasets[0].label = 'PR-AUC';
        charts.chart2.data.datasets[0].data = results.map(r => r.pr_auc);
        charts.chart2.data.datasets[0].backgroundColor = colors[1];
        charts.chart2.update();

        charts.radar.data.labels = ['准确率', 'ROC-AUC', 'PR-AUC', 'Precision', 'Recall', 'F1'];
        charts.radar.data.datasets = results.map((r, i) => ({
            label: r.model.toUpperCase(),
            data: [r.accuracy, r.roc_auc, r.pr_auc, r.precision, r.recall, r.f1],
            backgroundColor: colors[i % colors.length],
        }));
        charts.radar.update();
    }
}

// 导出CSV
async function exportCSV() {
    if (!lastResults) {
        showAlert('请先运行模拟', 'warning');
        return;
    }

    try {
        const requestData = buildRequestData(getSelectedModels());

        const response = await fetch('/api/export/csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (data.success) {
            const blob = new Blob([data.csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ml_simulator_results.csv';
            a.click();
            window.URL.revokeObjectURL(url);

            showAlert('导出成功！', 'success');
        } else {
            showAlert('导出失败: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('导出失败: ' + error.message, 'danger');
    }
}

// 显示提示
function showAlert(message, type = 'info') {
    const alertBox = document.getElementById('alertBox');

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertBox.innerHTML = '';
    alertBox.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
