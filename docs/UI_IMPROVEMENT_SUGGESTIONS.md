# UI 设计改进建议

本文档记录了 ML Simulator 项目的 UI 设计改进建议，供未来参考。

## 当前状态

截至 2026-01-14，项目已完成以下功能：
- ✅ 模型能力配置（支持10种预定义模型 + 自定义模型）
- ✅ 任务配置（二分类、多分类、回归）
- ✅ 实验方案（单次运行、交叉验证、学习曲线）
- ✅ 数据集特性配置（可分性、噪声、非线性）
- ✅ 批量模型选择（按任务类型自动/手动筛选）
- ✅ 结果展示（表格 + 柱状图 + 雷达图 + 学习曲线）
- ✅ 误差条显示（交叉验证和学习曲线的标准差）

## UI 设计改进建议

### 1. 视觉层次优化

#### 1.1 颜色系统统一
**建议**：建立统一的颜色主题

| 用途 | 当前颜色 | 建议改进 |
|------|---------|---------|
| 主色调 | Bootstrap 默认蓝 | 定义品牌色（如 #667eea） |
| 实验设计 | 蓝色 (#0d6efd) | 保持蓝色系 |
| 数据集特性 | 蓝色 (#17a2b8) | 改为绿色/青色系 |
| 模型配置 | 绿色 (#198754) | 改为橙色/紫色系 |
| 成功提示 | 绿色 | 保持 |
| 警告提示 | 黄色 | 保持 |
| 错误提示 | 红色 | 保持 |

**理由**：三个配置区域目前使用蓝/蓝/绿，建议使用三种明显不同的颜色来区分功能模块。

#### 1.2 卡片间距优化
**建议**：增加卡片间距，提升视觉呼吸感

```css
.row.mb-3 {
    margin-bottom: 2rem !important;  /* 从 1rem 增加到 2rem */
}

.card {
    margin-bottom: 0;
    transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}
```

### 2. 交互体验优化

#### 2.1 加载状态反馈
**建议**：为长时间运行的操作添加进度条

**场景**：交叉验证、学习曲线（运行时间较长）

**实现方案**：
```html
<!-- 添加进度条 -->
<div class="progress mb-3" id="simulationProgress" style="display: none;">
    <div class="progress-bar progress-bar-striped progress-bar-animated"
         role="progressbar" style="width: 0%"></div>
</div>

<div class="alert alert-info" id="simulationStatus" style="display: none;">
    <span id="statusText">正在初始化...</span>
</div>
```

**进度反馈**：
- 单次运行：无需进度条（快速）
- 5折交叉验证：显示 0% → 20% → 40% ... → 100%
- 学习曲线：显示总进度（训练集数量 × 重复次数）

#### 2.2 快捷操作面板
**建议**：添加"快速开始"预设场景

```html
<div class="card mb-3">
    <div class="card-header">
        <h6 class="mb-0">⚡ 快速开始</h6>
    </div>
    <div class="card-body">
        <div class="d-flex gap-2">
            <button class="btn btn-sm btn-outline-primary" onclick="loadPreset('binary_easy')">
                二分类-简单
            </button>
            <button class="btn btn-sm btn-outline-primary" onclick="loadPreset('binary_hard')">
                二分类-困难
            </button>
            <button class="btn btn-sm btn-outline-primary" onclick="loadPreset('multiclass_balanced')">
                多分类-均衡
            </button>
            <button class="btn btn-sm btn-outline-primary" onclick="loadPreset('cv_comparison')">
                模型对比（5折CV）
            </button>
            <button class="btn btn-sm btn-outline-primary" onclick="loadPreset('learning_curve_analysis')">
                学习曲线分析
            </button>
        </div>
    </div>
</div>
```

**预设场景配置**：
```javascript
const PRESETS = {
    'binary_easy': {
        taskType: 'binary',
        difficulty: { separability: 0.9, label_noise: 0.02, ... },
        models: ['lgbm', 'xgboost', 'catboost'],
        experimentType: 'single'
    },
    'cv_comparison': {
        taskType: 'binary',
        models: ['svm', 'rf', 'lgbm', 'dnn', 'transformer'],
        experimentType: 'cv',
        nFolds: 5
    },
    // ... 更多预设
};
```

#### 2.3 结果对比高亮
**建议**：在表格中突出显示最佳结果

**实现方案**：
```javascript
// 在 updateTable 函数中添加
const metricValues = results.map(r => r[metric]);
const maxValue = Math.max(...metricValues);

addCell(tr, value.toFixed(4), {
    isBest: value === maxValue  // 标记最佳值
});
```

```css
.best-value {
    background-color: #d4edda;
    font-weight: bold;
    border: 2px solid #28a745;
}
```

### 3. 响应式设计优化

#### 3.1 移动端适配
**建议**：优化小屏幕显示

**当前问题**：
- 配置区域卡片在小屏幕上堆叠，需要大量滚动
- 模型卡片内容过多，在小屏幕上难以操作

**改进方案**：
```css
@media (max-width: 768px) {
    /* 配置区域使用垂直堆叠 */
    .col-lg-7, .col-lg-5 {
        width: 100%;
        margin-bottom: 1rem;
    }

    /* 模型卡片简化 */
    .model-card-body {
        font-size: 0.85rem;
    }

    .param-slider {
        margin-bottom: 0.5rem;
    }

    /* 批量操作按钮换行 */
    .card-header .d-flex {
        flex-direction: column;
        align-items: flex-start;
    }
}
```

#### 3.2 大屏优化
**建议**：充分利用大屏幕空间

```css
@media (min-width: 1400px) {
    .container-fluid {
        max-width: 1600px;
        margin: 0 auto;
    }

    /* 配置区域使用 4 列布局 */
    .col-xl-8 { flex: 0 0 66.666667%; max-width: 66.666667%; }
    .col-xl-4 { flex: 0 0 33.333333%; max-width: 33.333333%; }
}
```

### 4. 数据可视化增强

#### 4.1 图表动画
**建议**：添加平滑的过渡动画

```javascript
charts.chart1.options.animation = {
    duration: 800,
    easing: 'easeInOutQuart'
};
```

#### 4.2 交互式提示
**建议**：在图表上悬停时显示详细信息

```javascript
plugins: {
    tooltip: {
        callbacks: {
            afterBody: function(context) {
                const dataset = context.chart.data.datasets[0.datasetIndex];
                if (dataset.errorBars) {
                    const error = dataset.errorBars[context.dataIndex];
                    return `标准差: ±${error.toFixed(4)}`;
                }
                return '';
            }
        }
    }
}
```

#### 4.3 图表切换按钮
**建议**：为结果图表添加切换按钮

```html
<div class="btn-group mb-3" role="group">
    <button class="btn btn-sm btn-outline-primary active" onclick="switchChart('bar')">
        柱状图
    </button>
    <button class="btn btn-sm btn-outline-primary" onclick="switchChart('boxplot')">
        箱线图
    </button>
    <button class="btn btn-sm btn-outline-primary" onclick="switchChart('violin')">
        小提琴图
    </button>
</div>
```

### 5. 用户引导

#### 5.1 新手引导
**建议**：首次访问时显示功能介绍

```javascript
// 使用 Shepherd.js 或类似库
const tour = new Shepherd.Tour({
    defaultStepOptions: {
        classes: 'shadow-md bg-purple-500',
        scrollTo: { behavior: 'smooth', block: 'center' }
    }
});

tour.addStep({
    id: 'task-config',
    text: '首先选择任务类型和配置数据集特性',
    attachTo: { element: '#taskType', on: 'bottom' }
});

tour.addStep({
    id: 'model-selection',
    text: '选择要对比的模型，支持批量选择',
    attachTo: { element: '#modelCardsContainer', on: 'bottom' }
});

tour.start();
```

#### 5.2 帮助文档链接
**建议**：在卡片右上角添加帮助图标

```html
<a href="#" class="text-muted" data-bs-toggle="tooltip" title="查看帮助文档">
    <i class="bi bi-question-circle"></i>
</a>
```

### 6. 性能优化

#### 6.1 图表懒加载
**建议**：只在需要时渲染图表

```javascript
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            initChart(entry.target.id);
            observer.unobserve(entry.target);
        }
    });
});

document.querySelectorAll('canvas').forEach(canvas => {
    observer.observe(canvas);
});
```

#### 6.2 防抖优化
**建议**：为滑块输入添加防抖

```javascript
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 滑块输入时防抖，避免频繁更新
const debouncedUpdate = debounce((modelName, param, value) => {
    updateModelParam(modelName, param, value);
}, 150);
```

### 7. 无障碍访问

#### 7.1 键盘导航
**建议**：支持键盘快捷键

```javascript
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'Enter':
                e.preventDefault();
                runSimulation();
                break;
            case 'r':
                e.preventDefault();
                resetAllModels();
                break;
            case 'a':
                e.preventDefault();
                selectAllModels();
                break;
        }
    }
});
```

#### 7.2 ARIA 标签
**建议**：为交互元素添加 ARIA 属性

```html
<button aria-label="运行模拟" id="runBtn">
    <span aria-hidden="true">▶ 运行模拟</span>
</button>
```

### 8. 高级功能

#### 8.1 配置导出/导入
**建议**：支持导出当前配置为 JSON

```javascript
function exportConfig() {
    const config = {
        task: getTaskConfig(),
        difficulty: getDifficultyConfig(),
        models: getSelectedModels(),
        profiles: modelProfiles
    };

    const blob = new Blob([JSON.stringify(config, null, 2)],
        { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ml-simulator-config-${Date.now()}.json`;
    a.click();
}
```

#### 8.2 结果对比历史
**建议**：保存历史结果，支持对比

```javascript
// 使用 IndexedDB 或 localStorage 存储历史记录
function saveResult(result) {
    const history = JSON.parse(localStorage.getItem('resultHistory') || '[]');
    history.push({
        timestamp: Date.now(),
        config: getCurrentConfig(),
        result: result
    });
    localStorage.setItem('resultHistory', JSON.stringify(history.slice(-10)));  // 保留最近10条
}
```

#### 8.3 模型推荐
**建议**：基于任务特性推荐最佳模型

```javascript
function recommendModels(taskConfig, difficulty) {
    const recommendations = [];

    // 简单规则引擎
    if (taskConfig.taskType === 'binary') {
        if (difficulty.separability > 0.8) {
            recommendations.push({
                model: 'logreg',
                reason: '高可分性，逻辑回归即可'
            });
        }
        if (difficulty.nonlinearity > 0.5) {
            recommendations.push({
                model: 'dnn',
                reason: '高非线性，需要深度学习'
            });
        }
    }

    return recommendations;
}
```

## 实施优先级

### 高优先级
1. ✅ 批量模型选择（已实现）
2. ✅ 误差条显示（已实现）
3. ⭐ 加载状态反馈（进度条）
4. ⭐ 快捷操作面板（预设场景）
5. ⭐ 结果对比高亮（最佳值标记）

### 中优先级
1. 颜色系统统一
2. 新手引导
3. 配置导出/导入
4. 键盘快捷键

### 低优先级
1. 箱线图/小提琴图
2. 结果对比历史
3. 模型推荐系统
4. 无障碍优化

## 设计参考

- [Chart.js Examples](https://www.chartjs.org/docs/latest/samples/)
- [Bootstrap Components](https://getbootstrap.com/docs/5.3/components/)
- [Material Design Guidelines](https://m3.material.io/)
- [Data Visualization Best Practices](https://www.tableau.com/learn/articles/whitepapers/best-beautiful-data-visualization-guidelines)

## 反馈渠道

如果您有其他 UI 设计建议，请：
- 提交 Issue
- 发起 Pull Request
- 联系项目维护者

---

*文档创建日期：2026-01-14*
*最后更新日期：2026-01-14*
