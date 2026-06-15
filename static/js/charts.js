/**
 * 绘图库封装（Chart.js）
 *
 * 统一所有图表的创建逻辑与主题色，避免散落硬编码。
 * 设计原则：
 *   - 所有工厂函数创建时即从 getThemeColors() 取色
 *   - 主题切换后由 applyTheme(chart) 统一刷新
 *   - errorBar 插件集中维护，柱状图默认附带
 *
 * 暴露：window.ChartLib
 */
(function (global) {
    'use strict';

    // =========================================================================
    // 主题色
    // =========================================================================

    // 多模型配色（保持与历史版本一致）
    const PALETTE = [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 159, 64, 0.6)',
        'rgba(40, 167, 135, 0.6)',
        'rgba(102, 16, 242, 0.6)',
        'rgba(220, 80, 80, 0.6)',
        'rgba(0, 150, 136, 0.6)',
    ];

    /**
     * 根据当前 body 是否含 dark-mode 返回主题色集合
     */
    function getThemeColors() {
        const isDark = document.body.classList.contains('dark-mode');
        return {
            isDark: isDark,
            text: isDark ? '#e0e0e0' : '#2c2c2c',
            muted: isDark ? '#a0a0a0' : '#6b7280',
            grid: isDark ? '#404040' : '#e8e8e8',
            cardBg: isDark ? '#2d2d2d' : '#ffffff',
            // 误差线颜色：深色用浅色、浅色用深色，保证可见
            errorBar: isDark ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.8)',
            // ROC/PR 曲线主色
            curve: isDark ? '#4a9eff' : '#2563eb',
            diagonal: isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)',
            // 混淆矩阵色阶两端
            matrixLow: isDark ? '#2d2d2d' : '#f5f5f5',
            matrixHigh: isDark ? '#3d6fa3' : '#2563eb',
            matrixText: isDark ? '#e0e0e0' : '#2c2c2c',
            palette: PALETTE,
        };
    }

    function paletteColor(i, alphaOverride) {
        const base = PALETTE[i % PALETTE.length];
        if (alphaOverride === undefined) return base;
        return base.replace(/0\.6\)$/, alphaOverride + ')');
    }

    // =========================================================================
    // 通用刻度/图例配置工厂
    // =========================================================================

    function cartesianScales(theme, yMax) {
        const y = {
            beginAtZero: true,
            ticks: { color: theme.text },
            grid: { color: theme.grid },
        };
        if (yMax !== undefined) y.max = yMax;
        return {
            y: y,
            x: {
                ticks: { color: theme.text },
                grid: { color: theme.grid },
            },
        };
    }

    function legendConfig(theme, display) {
        return {
            display: display !== false,
            labels: { color: theme.text },
        };
    }

    // =========================================================================
    // 误差线插件
    // =========================================================================

    /**
     * 为柱状图绘制误差线（error bar）。
     * dataset 上需挂 errorBars: number[]（与 data 等长），值为 ±标准差。
     */
    function drawErrorBars(chart) {
        const theme = getThemeColors();
        const ctx = chart.ctx;
        const yScale = chart.scales.y;
        if (!yScale) return;

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

                const yTop = yScale.getPixelForValue(value + error);
                const yBottom = yScale.getPixelForValue(value - error);
                const barTop = y;

                ctx.save();
                ctx.strokeStyle = theme.errorBar;
                ctx.lineWidth = 2;
                ctx.beginPath();

                // 垂直线
                ctx.moveTo(x, Math.min(yTop, barTop));
                ctx.lineTo(x, Math.max(yBottom, barTop));
                ctx.stroke();

                const lineWidth = Math.min(15, baseWidth * 0.4);
                // 顶部横线
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

    // 可被外部复用的插件对象
    const errorBarPlugin = {
        id: 'errorBars',
        afterDatasetsDraw: (chart) => drawErrorBars(chart),
    };

    // =========================================================================
    // ROC / PR / 混淆矩阵 / 散点 的纯计算工具（供 index.js 调用）
    // =========================================================================

    /**
     * 二分类 ROC：对正类概率 score 阈值扫描，返回 fpr/tpr/auc。
     * @param {number[]} yTrue  0/1
     * @param {number[]} yScore 正类概率
     */
    function computeROC(yTrue, yScore) {
        const n = yTrue.length;
        const P = yTrue.filter(v => v === 1).length;
        const N = n - P;
        if (P === 0 || N === 0) {
            return { fpr: [0, 1], tpr: [0, 1], auc: NaN, thresholds: [1, 0] };
        }

        // 按 score 降序排序
        const idx = yScore.map((_, i) => i).sort((a, b) => yScore[b] - yScore[a]);
        const sortedScore = idx.map(i => yScore[i]);
        const sortedLabel = idx.map(i => yTrue[i]);

        const fpr = [0];
        const tpr = [0];
        const thresholds = [sortedScore[0] + 1e-9];
        let tp = 0, fp = 0;
        for (let i = 0; i < n; i++) {
            if (sortedLabel[i] === 1) tp++; else fp++;
            // 同分数合并：跳过中间点，避免阶梯被切成斜线
            const sameScore = i < n - 1 && Math.abs(sortedScore[i + 1] - sortedScore[i]) < 1e-12;
            if (sameScore) continue;
            fpr.push(fp / N);
            tpr.push(tp / P);
            thresholds.push(sortedScore[i]);
        }
        fpr.push(1); tpr.push(1);

        // AUC = 梯形积分
        let auc = 0;
        for (let i = 1; i < fpr.length; i++) {
            auc += (fpr[i] - fpr[i - 1]) * (tpr[i] + tpr[i - 1]) / 2;
        }
        return { fpr: fpr, tpr: tpr, auc: Math.max(0, Math.min(1, auc)), thresholds: thresholds };
    }

    /**
     * 二分类 PR 曲线。返回 recall/precision/ap（average precision，梯形近似）。
     */
    function computePR(yTrue, yScore) {
        const P = yTrue.filter(v => v === 1).length;
        const n = yTrue.length;
        if (P === 0) {
            return { recall: [0, 1], precision: [1, 1], ap: NaN };
        }
        const idx = yScore.map((_, i) => i).sort((a, b) => yScore[b] - yScore[a]);
        const sortedLabel = idx.map(i => yTrue[i]);

        // 从高阈值到低：取每个排名为判定点
        let tp = 0, fp = 0;
        const recallArr = [], precisionArr = [];
        precisionArr.push(1); recallArr.push(0); // 起点
        for (let i = 0; i < n; i++) {
            if (sortedLabel[i] === 1) tp++; else fp++;
            const sameScore = i < n - 1 && Math.abs(yScore[idx[i + 1]] - yScore[idx[i]]) < 1e-12;
            if (sameScore) continue;
            recallArr.push(tp / P);
            precisionArr.push(tp / (tp + fp));
        }
        recallArr.push(1); precisionArr.push(tp / (tp + (n - tp)));

        // AP：以 recall 为自变量做梯形积分（按 recall 升序）
        const pts = recallArr.map((r, i) => [r, precisionArr[i]]).sort((a, b) => a[0] - b[0]);
        let ap = 0;
        for (let i = 1; i < pts.length; i++) {
            ap += (pts[i][0] - pts[i - 1][0]) * (pts[i][1] + pts[i - 1][1]) / 2;
        }
        return { recall: recallArr, precision: precisionArr, ap: Math.max(0, Math.min(1, ap)) };
    }

    /**
     * 混淆矩阵（n_classes × n_classes）。matrix[i][j] = 真实i被预测为j的样本数。
     */
    function computeConfusionMatrix(yTrue, yPred, nClasses) {
        const m = Array.from({ length: nClasses }, () => new Array(nClasses).fill(0));
        for (let i = 0; i < yTrue.length; i++) {
            const t = yTrue[i], p = yPred[i];
            if (t >= 0 && t < nClasses && p >= 0 && p < nClasses) m[t][p]++;
        }
        return m;
    }

    // =========================================================================
    // 图表工厂
    // =========================================================================

    /**
     * 创建柱状图（内置 errorBar 插件）。
     * 初始保留一个占位 dataset，便于调用方按 datasets[0].xxx 赋值更新。
     * @param {HTMLCanvasElement} canvas
     * @param {object} opts { yMax }
     */
    function createBarChart(canvas, opts) {
        opts = opts || {};
        const theme = getThemeColors();
        return new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '',
                    data: [],
                    backgroundColor: theme.palette[0],
                    errorBars: null,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: cartesianScales(theme, opts.yMax),
                plugins: { legend: legendConfig(theme) },
            },
            plugins: [errorBarPlugin],
        });
    }

    /**
     * 创建折线图（学习曲线）。
     */
    function createLineChart(canvas, opts) {
        opts = opts || {};
        const theme = getThemeColors();
        return new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: cartesianScales(theme, opts.yMax),
                plugins: { legend: legendConfig(theme) },
            },
        });
    }

    /**
     * 创建雷达图。
     */
    function createRadarChart(canvas) {
        const theme = getThemeColors();
        return new Chart(canvas.getContext('2d'), {
            type: 'radar',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1,
                        ticks: { color: theme.muted, backdropColor: theme.cardBg },
                        grid: { color: theme.grid },
                        pointLabels: { color: theme.text },
                    },
                },
                plugins: { legend: legendConfig(theme) },
            },
        });
    }

    /**
     * 创建 ROC 曲线图（学术论文风格）。
     * data: {
     *   fpr, tpr, auc, label,            // 主曲线（单次或 CV 的 mean）
     *   aucStd?,                          // CV 的 AUC 标准差（可选，用于图例标注）
     *   ciLower?, ciUpper?,               // CV 置信区间上下界 tpr（与 fpr 等长，可选）
     * }
     */
    function createROCChart(canvas, data) {
        const theme = getThemeColors();
        const aucTxt = isNaN(data.auc) ? 'N/A' : data.auc.toFixed(3);
        const aucStdTxt = (data.aucStd != null && !isNaN(data.aucStd))
            ? ` ± ${data.aucStd.toFixed(3)}` : '';
        const ciColor = theme.curve.replace(')', ',0.18)').replace('rgb', 'rgba');

        const datasets = [];

        // ① 置信区间阴影带（CV 模式）：上界正向 + 下界反向闭合为多边形
        if (data.ciLower && data.ciUpper && data.fpr) {
            const upper = data.fpr.map((f, i) => ({ x: f, y: data.ciUpper[i] }));
            const lower = data.fpr.map((f, i) => ({ x: f, y: data.ciLower[i] })).reverse();
            datasets.push({
                label: '±1σ 置信区间',
                data: upper.concat(lower),
                backgroundColor: ciColor,
                borderColor: 'transparent',
                borderWidth: 0,
                pointRadius: 0,
                fill: true,
                tension: 0,
                order: 3,
            });
        }

        // ② 对角线参考
        datasets.push({
            label: '随机分类器 (AUC = 0.5)',
            data: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
            borderColor: theme.diagonal,
            borderDash: [6, 6],
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            tension: 0,
            order: 2,
        });

        // ③ 主曲线
        datasets.push({
            label: `${data.label || '模型'} (AUC = ${aucTxt}${aucStdTxt})`,
            data: data.fpr.map((f, i) => ({ x: f, y: data.tpr[i] })),
            borderColor: theme.curve,
            backgroundColor: 'transparent',
            borderWidth: 2.2,
            pointRadius: 0,
            fill: false,
            tension: 0,
            order: 1,
        });

        return new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: { datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                scales: {
                    x: {
                        type: 'linear', min: 0, max: 1,
                        title: { display: true, text: 'False Positive Rate (FPR)', color: theme.text },
                        ticks: { color: theme.text, stepSize: 0.2 },
                        grid: { color: theme.grid },
                    },
                    y: {
                        type: 'linear', min: 0, max: 1,
                        title: { display: true, text: 'True Positive Rate (TPR)', color: theme.text },
                        ticks: { color: theme.text, stepSize: 0.2 },
                        grid: { color: theme.grid },
                    },
                },
                plugins: {
                    legend: legendConfig(theme),
                    tooltip: {
                        callbacks: {
                            title: (items) => `FPR = ${(+items[0].parsed.x).toFixed(3)}`,
                            label: (ctx) => `TPR = ${(+ctx.parsed.y).toFixed(3)}`,
                        },
                    },
                },
            },
        });
    }

    /**
     * 创建 PR 曲线图。data: {recall, precision, ap, label}
     */
    function createPRChart(canvas, data) {
        const theme = getThemeColors();
        const apTxt = isNaN(data.ap) ? 'N/A' : data.ap.toFixed(4);
        return new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: `${data.label || '模型'} (AP=${apTxt})`,
                        data: data.recall.map((r, i) => ({ x: r, y: data.precision[i] })),
                        borderColor: theme.curve,
                        backgroundColor: theme.curve.replace(')', ',0.15)').replace('rgb', 'rgba'),
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: true,
                        tension: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear', min: 0, max: 1,
                        title: { display: true, text: 'Recall', color: theme.text },
                        ticks: { color: theme.text },
                        grid: { color: theme.grid },
                    },
                    y: {
                        type: 'linear', min: 0, max: 1,
                        title: { display: true, text: 'Precision', color: theme.text },
                        ticks: { color: theme.text },
                        grid: { color: theme.grid },
                    },
                },
                plugins: { legend: legendConfig(theme) },
            },
        });
    }

    /**
     * 创建混淆矩阵热力图（用 Matrix 控制器；若不可用则降级为逐单元格绘制）。
     * data: {matrix, labels}
     */
    function createConfusionMatrix(canvas, data) {
        const theme = getThemeColors();
        const matrix = data.matrix;
        const labels = data.labels || matrix.map((_, i) => String(i));
        const n = matrix.length;

        // 求最大值用于归一化
        let max = 0;
        matrix.forEach(row => row.forEach(v => { if (v > max) max = v; }));
        max = Math.max(max, 1);

        // 颜色插值：matrixLow → matrixHigh
        function lerpColor(t) {
            const c1 = hexToRgb(theme.matrixLow);
            const c2 = hexToRgb(theme.matrixHigh);
            const r = Math.round(c1[0] + (c2[0] - c1[0]) * t);
            const g = Math.round(c1[1] + (c2[1] - c1[1]) * t);
            const b = Math.round(c1[2] + (c2[2] - c1[2]) * t);
            return `rgba(${r},${g},${b},0.9)`;
        }

        // 展平为 dataset.data：{x: 预测列, y: 真实行, v: 计数}
        // 注意 Chart.js 坐标 y 向上，而矩阵第 0 行要显示在顶部 → 用 (n-1-row) 翻转
        const cellData = [];
        const cellColors = [];
        for (let row = 0; row < n; row++) {
            for (let col = 0; col < n; col++) {
                const v = matrix[row][col];
                cellData.push({ x: col, y: n - 1 - row, v: v });
                cellColors.push(lerpColor(v / max));
            }
        }

        const chart = new Chart(canvas.getContext('2d'), {
            type: 'matrix',
            data: {
                datasets: [{
                    label: '混淆矩阵',
                    data: cellData,
                    backgroundColor(ctx) {
                        return cellColors[ctx.dataIndex] || theme.matrixLow;
                    },
                    borderColor: theme.grid,
                    borderWidth: 1,
                    width: ({ chart }) => (chart.chartArea || {}).width
                        ? Math.max(8, (chart.chartArea.right - chart.chartArea.left) / n - 4) : 20,
                    height: ({ chart }) => (chart.chartArea || {}).height
                        ? Math.max(8, (chart.chartArea.bottom - chart.chartArea.top) / n - 4) : 20,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear', min: -0.5, max: n - 0.5,
                        ticks: {
                            stepSize: 1,
                            color: theme.text,
                            callback: (v) => (Number.isInteger(v) && v >= 0 && v < n) ? labels[v] : '',
                        },
                        title: { display: true, text: '预测类别', color: theme.text },
                        grid: { display: false },
                    },
                    y: {
                        type: 'linear', min: -0.5, max: n - 0.5,
                        ticks: {
                            stepSize: 1,
                            color: theme.text,
                            callback: (v) => {
                                if (!Number.isInteger(v) || v < 0 || v >= n) return '';
                                // y 已翻转：显示行标签
                                return labels[n - 1 - v];
                            },
                        },
                        title: { display: true, text: '真实类别', color: theme.text },
                        grid: { display: false },
                    },
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title() { return ''; },
                            label(ctx) {
                                const d = ctx.raw;
                                const trueLabel = labels[n - 1 - d.y];
                                const predLabel = labels[d.x];
                                return `真实=${trueLabel} → 预测=${predLabel}：${d.v} 样本`;
                            },
                        },
                    },
                },
            },
            // 自定义插件：在格子上画数字
            plugins: [{
                id: 'matrixLabels',
                afterDatasetsDraw(chart) {
                    const ds = chart.data.datasets[0];
                    const meta = chart.getDatasetMeta(0);
                    const ctx = chart.ctx;
                    ctx.save();
                    ctx.font = '12px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    meta.data.forEach((el, i) => {
                        const v = ds.data[i].v;
                        ctx.fillStyle = (v / max) > 0.5 ? '#ffffff' : theme.matrixText;
                        ctx.fillText(String(v), el.x, el.y);
                    });
                    ctx.restore();
                },
            }],
        });
        return chart;
    }

    /**
     * 创建散点图（回归：预测vs真实 / 残差图）。
     * opts: {points:[{x,y}], xLabel, yLabel, refLine:bool}
     */
    function createScatterChart(canvas, opts) {
        const theme = getThemeColors();
        const datasets = [];
        if (opts.refLine) {
            // y=x 参考线
            const xs = opts.points.map(p => p.x);
            const lo = Math.min(...xs), hi = Math.max(...xs);
            datasets.push({
                label: 'y = x',
                data: [{ x: lo, y: lo }, { x: hi, y: hi }],
                borderColor: theme.diagonal,
                borderDash: [5, 5],
                borderWidth: 1.5,
                type: 'line',
                pointRadius: 0,
                fill: false,
                showLine: true,
            });
        }
        datasets.push({
            label: opts.label || '样本',
            data: opts.points,
            backgroundColor: theme.curve.replace(')', ',0.4)').replace('rgb', 'rgba'),
            borderColor: theme.curve,
            pointRadius: 2,
        });
        return new Chart(canvas.getContext('2d'), {
            type: 'scatter',
            data: { datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: opts.xLabel || 'x', color: theme.text },
                        ticks: { color: theme.text },
                        grid: { color: theme.grid },
                    },
                    y: {
                        type: 'linear',
                        title: { display: true, text: opts.yLabel || 'y', color: theme.text },
                        ticks: { color: theme.text },
                        grid: { color: theme.grid },
                    },
                },
                plugins: { legend: legendConfig(theme) },
            },
        });
    }

    // =========================================================================
    // 工具
    // =========================================================================

    function hexToRgb(hex) {
        const h = hex.replace('#', '');
        return [
            parseInt(h.substring(0, 2), 16),
            parseInt(h.substring(2, 4), 16),
            parseInt(h.substring(4, 6), 16),
        ];
    }

    /**
     * 销毁图表（若存在）。
     */
    function destroy(chart) {
        if (chart) {
            try { chart.destroy(); } catch (e) { /* ignore */ }
        }
    }

    // 导出
    global.ChartLib = {
        getThemeColors: getThemeColors,
        paletteColor: paletteColor,
        computeROC: computeROC,
        computePR: computePR,
        computeConfusionMatrix: computeConfusionMatrix,
        drawErrorBars: drawErrorBars,
        errorBarPlugin: errorBarPlugin,
        createBarChart: createBarChart,
        createLineChart: createLineChart,
        createRadarChart: createRadarChart,
        createROCChart: createROCChart,
        createPRChart: createPRChart,
        createConfusionMatrix: createConfusionMatrix,
        createScatterChart: createScatterChart,
        destroy: destroy,
    };
})(window);
