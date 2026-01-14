// 全局变量
let charts = {};
let lastResults = null;
let lastExperimentType = 'single';  // 记录最后一次的实验方案类型
let modelProfiles = {};  // 存储每个模型的能力参数
let customModels = [];  // 存储自定义模型名称

// 预定义模型能力画像
const DEFAULT_PROFILES = {
    'svm': {
        bias: 0.5, variance: 0.2, capacity: 0.6, noise_tolerance: 0.4,
        supported_tasks: ['binary']  // SVM主要支持二分类
    },
    'rf': {
        bias: 0.3, variance: 0.4, capacity: 0.7, noise_tolerance: 0.8,
        supported_tasks: ['binary', 'multiclass', 'regression']  // RF支持所有任务
    },
    'lgbm': {
        bias: 0.3, variance: 0.3, capacity: 0.8, noise_tolerance: 0.6,
        supported_tasks: ['binary', 'multiclass', 'regression']  // LightGBM支持所有任务
    },
    'dnn': {
        bias: 0.2, variance: 0.7, capacity: 0.95, noise_tolerance: 0.5,
        supported_tasks: ['binary', 'multiclass', 'regression']  // DNN支持所有任务
    },
    'cnn': {
        bias: 0.3, variance: 0.5, capacity: 0.85, noise_tolerance: 0.6,
        supported_tasks: ['binary', 'multiclass', 'regression']  // CNN支持所有任务
    },
    'rnn': {
        bias: 0.4, variance: 0.6, capacity: 0.8, noise_tolerance: 0.5,
        supported_tasks: ['binary', 'multiclass', 'regression']  // RNN支持所有任务
    },
    'transformer': {
        bias: 0.2, variance: 0.9, capacity: 0.98, noise_tolerance: 0.4,
        supported_tasks: ['binary', 'multiclass', 'regression']  // Transformer支持所有任务
    },
    'logreg': {
        bias: 0.5, variance: 0.1, capacity: 0.5, noise_tolerance: 0.5,
        supported_tasks: ['binary', 'multiclass']  // Logistic Regression支持分类任务
    },
    'xgboost': {
        bias: 0.3, variance: 0.3, capacity: 0.8, noise_tolerance: 0.7,
        supported_tasks: ['binary', 'multiclass', 'regression']  // XGBoost支持所有任务
    },
    'catboost': {
        bias: 0.3, variance: 0.25, capacity: 0.78, noise_tolerance: 0.75,
        supported_tasks: ['binary', 'multiclass', 'regression']  // CatBoost支持所有任务
    },
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

    // 生成任务标签
    const supportedTasks = profile.supported_tasks || ['binary', 'multiclass', 'regression'];
    const taskBadges = supportedTasks.map(task => {
        const labels = {
            'binary': '二分类',
            'multiclass': '多分类',
            'regression': '回归'
        };
        const colors = {
            'binary': 'bg-primary',
            'multiclass': 'bg-success',
            'regression': 'bg-info'
        };
        return `<span class="badge ${colors[task]} me-1" style="font-size: 0.7rem;">${labels[task]}</span>`;
    }).join('');

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
                    <div style="cursor: pointer;" onclick="toggleModelSelection('${modelName}')">
                        <span class="fw-bold">
                            ${modelName.toUpperCase()}
                            ${isCustom ? ' <span class="badge bg-warning text-dark">自定义</span>' : ''}
                        </span>
                        <div class="mt-1">${taskBadges}</div>
                    </div>
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
        defaultProfile = {
            bias: 0.5,
            variance: 0.5,
            capacity: 0.7,
            noise_tolerance: 0.5,
            supported_tasks: modelProfiles[modelName].supported_tasks || ['binary', 'multiclass', 'regression']
        };
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

    // 获取选中的任务类型
    const supportedTasks = [];
    if (document.getElementById('newModelTaskBinary').checked) {
        supportedTasks.push('binary');
    }
    if (document.getElementById('newModelTaskMulticlass').checked) {
        supportedTasks.push('multiclass');
    }
    if (document.getElementById('newModelTaskRegression').checked) {
        supportedTasks.push('regression');
    }

    if (supportedTasks.length === 0) {
        showAlert('请至少选择一种任务类型', 'warning');
        return;
    }

    // 获取参数
    const profile = {
        bias: parseFloat(document.getElementById('newModelBias').value),
        variance: parseFloat(document.getElementById('newModelVariance').value),
        capacity: parseFloat(document.getElementById('newModelCapacity').value),
        noise_tolerance: parseFloat(document.getElementById('newModelNoiseTol').value),
        supported_tasks: supportedTasks,
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

    // 学习曲线参数滑块
    bindSlider('lcAcc10', 'lcAcc10Value');
    bindSlider('lcAcc100', 'lcAcc100Value');
    bindSlider('lcAlpha', 'lcAlphaValue');
    bindSlider('lcNoise', 'lcNoiseValue');

    // 任务类型切换
    document.getElementById('taskType').addEventListener('change', function() {
        updateUIForTaskType(this.value);
    });

    // 实验方案类型切换
    document.getElementById('experimentType').addEventListener('change', function() {
        updateUIForExperimentType(this.value);
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

    // 自动勾选支持该任务类型的模型
    autoSelectModelsForTask(taskType);
}

// 根据实验方案类型更新UI
function updateUIForExperimentType(experimentType) {
    const cvConfig = document.getElementById('cvConfig');
    const lcConfigSimple = document.getElementById('lcConfigSimple');
    const lcConfig = document.getElementById('lcConfig');

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

// =============================================================================
// 批量操作函数
// =============================================================================

// 根据任务类型自动选择模型
function autoSelectModelsForTask(taskType) {
    // 先取消所有选择
    deselectAllModels();

    // 根据任务类型选择对应模型
    selectModelsByTask(taskType, false);  // false = 不显示提示

    // 显示提示
    const taskNames = {
        'binary': '二分类',
        'multiclass': '多分类',
        'regression': '回归'
    };
    showAlert(`已自动选中支持${taskNames[taskType]}的模型`, 'info');
}

// 根据任务类型选择模型
function selectModelsByTask(taskType, showPrompt = true) {
    // 先取消所有选中
    deselectAllModels();

    const checkboxes = document.querySelectorAll('.model-select-checkbox');
    let selectedCount = 0;

    checkboxes.forEach(checkbox => {
        const modelName = checkbox.value;
        let profile;

        // 获取模型配置
        if (customModels.includes(modelName)) {
            profile = modelProfiles[modelName];
        } else {
            profile = DEFAULT_PROFILES[modelName];
        }

        // 检查模型是否支持该任务类型
        const supportedTasks = profile.supported_tasks || ['binary', 'multiclass', 'regression'];

        if (supportedTasks.includes(taskType)) {
            checkbox.checked = true;
            updateModelCardSelection(modelName, true);
            selectedCount++;
        }
    });

    // 显示提示（如果需要）
    if (showPrompt) {
        const taskNames = {
            'binary': '二分类',
            'multiclass': '多分类',
            'regression': '回归'
        };
        showAlert(`已选中 ${selectedCount} 个支持${taskNames[taskType]}的模型`, 'success');
    }
}

// 全选模型
function selectAllModels() {
    const checkboxes = document.querySelectorAll('.model-select-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        updateModelCardSelection(checkbox.value, true);
    });
    showAlert('已选中所有模型', 'info');
}

// 全不选模型
function deselectAllModels() {
    const checkboxes = document.querySelectorAll('.model-select-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
        updateModelCardSelection(checkbox.value, false);
    });
}

// 更新模型卡片的选中状态
function updateModelCardSelection(modelName, isSelected) {
    const card = document.getElementById(`model_${modelName}_card`);
    const header = document.getElementById(`model_${modelName}_header`);

    if (card && header) {
        if (isSelected) {
            card.classList.add('selected');
            header.style.backgroundColor = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            header.style.color = 'white';
        } else {
            card.classList.remove('selected');
            header.style.backgroundColor = '';
            header.style.color = '';
        }
    }
}

// 绘制误差线
function drawErrorBars(chart) {
    const ctx = chart.ctx;
    const yScale = chart.scales.y;

    chart.data.datasets.forEach((dataset, datasetIndex) => {
        if (!dataset.errorBars || !dataset.errorBars.some(e => e > 0)) {
            return;
        }

        const meta = chart.getDatasetMeta(datasetIndex);
        const errorData = dataset.errorBars;

        meta.data.forEach((bar, index) => {
            const value = dataset.data[index];
            const error = errorData[index];

            if (!error || error === 0) return;

            const x = bar.x;
            const y = bar.y;
            const baseWidth = bar.width;

            // 计算误差条的位置
            const yTop = yScale.getPixelForValue(value + error);
            const yBottom = yScale.getPixelForValue(value - error);
            const barTop = y;

            // 绘制误差线
            ctx.save();
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.lineWidth = 2;
            ctx.beginPath();

            // 垂直线
            ctx.moveTo(x, Math.min(yTop, barTop));
            ctx.lineTo(x, Math.max(yBottom, barTop));
            ctx.stroke();

            // 顶部横线
            const lineWidth = Math.min(15, baseWidth * 0.4);
            ctx.beginPath();
            ctx.moveTo(x - lineWidth / 2, Math.min(yTop, barTop));
            ctx.lineTo(x + lineWidth / 2, Math.min(yTop, barTop));
            ctx.stroke();

            // 底部横线
            ctx.beginPath();
            ctx.moveTo(x - lineWidth / 2, Math.max(yBottom, barTop));
            ctx.lineTo(x + lineWidth / 2, Math.max(yBottom, barTop));
            ctx.stroke();

            ctx.restore();
        });
    });
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
                errorBars: null
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
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
                errorBars: null
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
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
            lastExperimentType = data.experiment_type || 'single';
            displayResults(data.results, data.experiment_type);
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

    // 构建实验方案配置
    const experimentType = document.getElementById('experimentType').value;
    let experimentConfig = {
        type: experimentType,
    };

    if (experimentType === 'cv') {
        experimentConfig.n_folds = parseInt(document.getElementById('nFolds').value);
    } else if (experimentType === 'learning_curve') {
        const trainSizesStr = document.getElementById('trainSizes').value.trim();
        experimentConfig.train_sizes = trainSizesStr.split(',').map(s => parseFloat(s.trim()));
        experimentConfig.n_runs = parseInt(document.getElementById('lcRuns').value);

        // 学习曲线参数
        experimentConfig.lc_params = {
            acc_10: parseFloat(document.getElementById('lcAcc10').value),
            acc_100: parseFloat(document.getElementById('lcAcc100').value),
            alpha: parseFloat(document.getElementById('lcAlpha').value),
            noise_std_start: parseFloat(document.getElementById('lcNoise').value),
        };
    }

    return {
        task_type: taskType,
        num_samples: numSamples,
        n_classes: nClasses,
        label_distribution: labelDistribution,
        models: models,
        difficulty: difficulty,
        models_config: models_config,
        experiment_config: experimentConfig,
        random_state: 42,
    };
}

// 显示结果
function displayResults(results, experimentType) {
    updateTable(results, experimentType);
    updateCharts(results, experimentType);
}

// 更新表格
function updateTable(results, experimentType) {
    const taskType = document.getElementById('taskType').value;
    const thead = document.querySelector('#resultsTableHead tr');
    const tbody = document.querySelector('#resultsTable tbody');

    // 清空表格
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // 根据任务类型和实验方案设置表头
    let headers = [];
    let metrics = [];

    // 对于交叉验证和学习曲线，字段名包含 _mean 和 _std 后缀
    const isStatistical = experimentType === 'cv' || experimentType === 'learning_curve';

    if (taskType === 'regression') {
        if (isStatistical) {
            headers = ['模型', 'MAE', 'RMSE', 'R²'];
            metrics = [['mae_mean', 'mae_std'], ['rmse_mean', 'rmse_std'], ['r2_mean', 'r2_std']];
        } else {
            headers = ['模型', 'MAE', 'RMSE', 'R²'];
            metrics = ['mae', 'rmse', 'r2'];
        }
    } else if (taskType === 'multiclass') {
        if (isStatistical) {
            headers = ['模型', '准确率', 'Macro-F1', 'Weighted-F1', 'LogLoss'];
            metrics = [
                ['accuracy_mean', 'accuracy_std'],
                ['macro_f1_mean', 'macro_f1_std'],
                ['weighted_f1_mean', 'weighted_f1_std'],
                ['logloss_mean', 'logloss_std']
            ];
        } else {
            headers = ['模型', '准确率', 'Macro-F1', 'Weighted-F1', 'LogLoss', 'Top-3'];
            metrics = ['accuracy', 'macro_f1', 'weighted_f1', 'logloss', 'top_3_accuracy'];
        }
    } else {  // binary
        if (isStatistical) {
            headers = ['模型', '准确率', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'PR-AUC'];
            metrics = [
                ['accuracy_mean', 'accuracy_std'],
                ['precision_mean', 'precision_std'],
                ['recall_mean', 'recall_std'],
                ['f1_mean', 'f1_std'],
                ['roc_auc_mean', 'roc_auc_std'],
                ['pr_auc_mean', 'pr_auc_std']
            ];
        } else {
            headers = ['模型', '准确率', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'PR-AUC', 'LogLoss'];
            metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc', 'logloss'];
        }
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
        let modelName = row.model;
        if (experimentType === 'learning_curve' && row.train_size !== undefined) {
            modelName += ` (${(row.train_size * 100).toFixed(0)}%)`;
        }
        modelCell.textContent = modelName.toUpperCase();
        modelCell.style.fontWeight = 'bold';
        tr.appendChild(modelCell);

        // 指标数据
        metrics.forEach(metric => {
            if (isStatistical) {
                // 统计结果：显示 均值 ± 标准差
                const meanVal = row[metric[0]];
                const stdVal = row[metric[1]];

                if (meanVal === undefined || meanVal === null) {
                    addCell(tr, 'N/A');
                } else {
                    addCell(tr, `${meanVal.toFixed(4)} ± ${stdVal.toFixed(4)}`);
                }
            } else {
                // 单次结果
                const value = row[metric];
                if (value === undefined || value === null) {
                    addCell(tr, 'N/A');
                } else {
                    addCell(tr, value.toFixed(4));
                }
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
function updateCharts(results, experimentType) {
    const taskType = document.getElementById('taskType').value;
    const isStatistical = experimentType === 'cv' || experimentType === 'learning_curve';

    const colors = [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(153, 102, 255, 0.6)',
    ];

    // 学习曲线使用折线图，其他使用柱状图
    if (experimentType === 'learning_curve') {
        updateLearningCurveCharts(results, taskType, colors);
    } else {
        // 单次运行或交叉验证使用柱状图
        updateBarCharts(results, taskType, isStatistical, colors);
    }
}

// 更新柱状图（单次运行和交叉验证）
function updateBarCharts(results, taskType, isStatistical, colors) {
    const models = results.map(r => r.model.toUpperCase());

    // 获取指标值（均值）和误差（标准差）
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

    if (taskType === 'regression') {
        document.getElementById('chart1Title').textContent = 'MAE 对比';
        document.getElementById('chart2Title').textContent = 'RMSE 对比';

        // Chart 1: MAE
        charts.chart1.data.labels = models;
        charts.chart1.data.datasets[0].label = 'MAE';
        charts.chart1.data.datasets[0].data = results.map(r => getValue(r, 'mae'));
        charts.chart1.data.datasets[0].backgroundColor = colors[0];
        charts.chart1.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'mae')) : null;
        charts.chart1.update();

        // Chart 2: RMSE
        charts.chart2.data.labels = models;
        charts.chart2.data.datasets[0].label = 'RMSE';
        charts.chart2.data.datasets[0].data = results.map(r => getValue(r, 'rmse'));
        charts.chart2.data.datasets[0].backgroundColor = colors[1];
        charts.chart2.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'rmse')) : null;
        charts.chart2.update();

        // Radar chart
        charts.radar.data.labels = ['1-MAE', '1-RMSE', 'R²'];
        charts.radar.data.datasets = results.map((r, i) => ({
            label: r.model.toUpperCase(),
            data: [1 - getValue(r, 'mae'), 1 - getValue(r, 'rmse'), getValue(r, 'r2')],
            backgroundColor: colors[i % colors.length],
        }));
        charts.radar.update();

    } else if (taskType === 'multiclass') {
        document.getElementById('chart1Title').textContent = '准确率对比';
        document.getElementById('chart2Title').textContent = 'Macro-F1 对比';

        // Chart 1: Accuracy
        charts.chart1.data.labels = models;
        charts.chart1.data.datasets[0].label = '准确率';
        charts.chart1.data.datasets[0].data = results.map(r => getValue(r, 'accuracy'));
        charts.chart1.data.datasets[0].backgroundColor = colors[0];
        charts.chart1.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'accuracy')) : null;
        charts.chart1.update();

        // Chart 2: Macro-F1
        charts.chart2.data.labels = models;
        charts.chart2.data.datasets[0].label = 'Macro-F1';
        charts.chart2.data.datasets[0].data = results.map(r => getValue(r, 'macro_f1'));
        charts.chart2.data.datasets[0].backgroundColor = colors[1];
        charts.chart2.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'macro_f1')) : null;
        charts.chart2.update();

        // Radar chart
        charts.radar.data.labels = ['准确率', 'Macro-F1', 'Weighted-F1', '1-LogLoss', 'Top-3'];
        charts.radar.data.datasets = results.map((r, i) => ({
            label: r.model.toUpperCase(),
            data: [
                getValue(r, 'accuracy'),
                getValue(r, 'macro_f1'),
                getValue(r, 'weighted_f1'),
                1 / (1 + getValue(r, 'logloss')),
                isStatistical ? 0.9 : getValue(r, 'top_3_accuracy')
            ],
            backgroundColor: colors[i % colors.length],
        }));
        charts.radar.update();

    } else {  // binary
        document.getElementById('chart1Title').textContent = 'ROC-AUC 对比';
        document.getElementById('chart2Title').textContent = 'PR-AUC 对比';

        // Chart 1: ROC-AUC
        charts.chart1.data.labels = models;
        charts.chart1.data.datasets[0].label = 'ROC-AUC';
        charts.chart1.data.datasets[0].data = results.map(r => getValue(r, 'roc_auc'));
        charts.chart1.data.datasets[0].backgroundColor = colors[0];
        charts.chart1.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'roc_auc')) : null;
        charts.chart1.update();

        // Chart 2: PR-AUC
        charts.chart2.data.labels = models;
        charts.chart2.data.datasets[0].label = 'PR-AUC';
        charts.chart2.data.datasets[0].data = results.map(r => getValue(r, 'pr_auc'));
        charts.chart2.data.datasets[0].backgroundColor = colors[1];
        charts.chart2.data.datasets[0].errorBars = isStatistical ? results.map(r => getError(r, 'pr_auc')) : null;
        charts.chart2.update();

        // Radar chart
        charts.radar.data.labels = ['准确率', 'ROC-AUC', 'PR-AUC', 'Precision', 'Recall', 'F1'];
        charts.radar.data.datasets = results.map((r, i) => ({
            label: r.model.toUpperCase(),
            data: [
                getValue(r, 'accuracy'),
                getValue(r, 'roc_auc'),
                getValue(r, 'pr_auc'),
                getValue(r, 'precision'),
                getValue(r, 'recall'),
                getValue(r, 'f1')
            ],
            backgroundColor: colors[i % colors.length],
        }));
        charts.radar.update();
    }
}

// 更新学习曲线图表
function updateLearningCurveCharts(results, taskType, colors) {
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

    // 选择主要指标
    let metric1, metric2;
    if (taskType === 'regression') {
        metric1 = 'mae_mean';
        metric2 = 'rmse_mean';
        document.getElementById('chart1Title').textContent = 'MAE 学习曲线';
        document.getElementById('chart2Title').textContent = 'RMSE 学习曲线';
    } else if (taskType === 'multiclass') {
        metric1 = 'accuracy_mean';
        metric2 = 'macro_f1_mean';
        document.getElementById('chart1Title').textContent = '准确率学习曲线';
        document.getElementById('chart2Title').textContent = 'Macro-F1 学习曲线';
    } else {  // binary
        metric1 = 'accuracy_mean';
        metric2 = 'roc_auc_mean';
        document.getElementById('chart1Title').textContent = '准确率学习曲线';
        document.getElementById('chart2Title').textContent = 'ROC-AUC 学习曲线';
    }

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
    charts.chart1.config.type = 'line';
    charts.chart1.data.labels = labels;
    charts.chart1.data.datasets = datasets1;
    charts.chart1.update();

    charts.chart2.config.type = 'line';
    charts.chart2.data.labels = labels;
    charts.chart2.data.datasets = datasets2;
    charts.chart2.update();

    // 雷达图不适用于学习曲线，隐藏或显示提示
    charts.radar.data.labels = [];
    charts.radar.data.datasets = [];
    charts.radar.update();
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
