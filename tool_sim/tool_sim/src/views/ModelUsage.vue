<template>
  <div class="model-usage hide-scrollbar">
    <!-- 配置面板 -->
    <div class="config-panel">
      <div class="config-header">
        <h3 class="config-title">模型全景扫描控制台</h3>
        <span class="config-desc">选择已固化的形态模型，对指定股票池进行全局多尺度融合相似度扫描</span>
      </div>

      <div class="config-body">
        <!-- 左侧：模型选择 -->
        <div class="config-section">
          <div class="section-label">
            <el-icon :size="16" color="#409EFF"><DataAnalysis /></el-icon>
            <span>选择目标模型</span>
          </div>
          <el-select
            v-model="selectedModelToUse"
            placeholder="请选择自定义形态模型"
            class="model-select"
            size="large"
          >
            <el-option-group label="自定义模型">
              <el-option v-for="mode in customModels" :key="mode.index" :label="mode.name" :value="mode.index">
                <div class="option-content">
                  <span class="option-name">{{ mode.name }}</span>
                  <el-tag size="small" :type="mode.is_yolo ? 'warning' : 'primary'" style="margin-left: 6px;">
                    {{ mode.is_yolo ? 'YOLO' : '' }}
                  </el-tag>
                  <span class="option-tags">{{ mode.lines.join(', ') }}</span>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </div>

        <!-- 分隔线 -->
        <div class="config-divider"></div>

        <!-- 模型预览图 -->
        <div v-if="selectedModelToUse && modelPreviewData" class="config-section" style="flex: 1; min-width: 300px;">
          <div class="section-label">
            <el-icon :size="16" color="#E6A23C"><View /></el-icon>
            <span>{{ modelPreviewMode === 'KLINE' ? 'K线骨架预览' : '均线形态预览' }}</span>
          </div>
          <div ref="modelPreviewRef" style="width: 100%; height: 160px; border: 1px solid #e4e7ed; border-radius: 6px; background: #fff;"></div>
        </div>

        <!-- 分隔线 -->
        <div class="config-divider"></div>

        <!-- 右侧：扫描范围 -->
        <div class="config-section">
          <div class="section-label">
            <el-icon :size="16" color="#409EFF"><List /></el-icon>
            <span>扫描范围</span>
          </div>
          <div class="range-grid">
            <div class="range-item">
              <span class="range-label">目标股票池</span>
              <span class="range-value">{{ targetPoolCount }} 只股票</span>
            </div>
            <div class="range-item">
              <span class="range-label">全局时间范围</span>
              <span class="range-value range-date">{{ scanDateRangeDisplay }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 多尺度权重配置面板 -->
<!--
-->

    <!-- 执行按钮 -->
    <div class="scan-action">
      <el-button
        type="danger"
        size="large"
        class="scan-btn"
        @click="runRealtimeScan"
        :loading="isRealtimeScanning"
        :disabled="!selectedModelToUse"
        style="margin-left: 12px;"
      >
        {{ isRealtimeScanning ? '实时查找中...' : '实时查找（最近走势）' }}
      </el-button>
      <div class="scan-hint" v-if="!selectedModelToUse">请先选择一个模型</div>
      <div class="scan-hint" v-else-if="weightSum !== 100" style="color: #F56C6C;">权重总和需等于 100%</div>
    </div>

    <!-- 扫描结果列表 -->
    <div v-if="hasScanResults" class="result-panel">
      <div class="result-header">
        <h4 class="result-title">
          <el-icon style="margin-right: 6px;"><List /></el-icon>
          多尺度融合扫描结果
          <span class="result-count">共 {{ tableData.length }} 条（按融合相似度排序）</span>
        </h4>
      </div>

      <el-table
        :data="tableData"
        border
        stripe
        style="width: 100%; border-radius: 8px; overflow: hidden;"
        :cell-style="{ textAlign: 'center' }"
        :header-cell-style="{ textAlign: 'center', background: '#f5f7fa', fontWeight: 'bold', color: '#606266' }"
      >
        <!-- 股票名称与代码 -->
        <el-table-column label="证券信息" width="180px">
          <template #default="{ row }">
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 5px 0;">
              <span style="font-weight: bold; color: #303133; font-size: 14px;">{{ row.stockName }}</span>
              <span style="font-size: 11px; color: #909399; margin-top: 4px; background: #f0f2f5; padding: 2px 6px; border-radius: 4px;">
                {{ row.stockCode }}
              </span>
            </div>
          </template>
        </el-table-column>

        <!-- 匹配的时间区间 -->
        <el-table-column label="匹配时段" width="220px">
          <template #default="{ row }">
            <div style="font-size: 13px; color: #606266; padding: 5px 0; text-align: left; margin-left: 20px;">
              <div><el-tag size="small" type="success" effect="dark" style="margin-right: 8px; padding: 0 4px; height: 18px; line-height: 18px;">起</el-tag> {{ row.startDate }}</div>
              <div style="margin-top: 10px;"><el-tag size="small" type="danger" effect="dark" style="margin-right: 8px; padding: 0 4px; height: 18px; line-height: 18px;">止</el-tag> {{ row.endDate }}</div>
            </div>
          </template>
        </el-table-column>

        <!-- 形态走势预览 -->
        <el-table-column label="形态走势预览" width="340px">
          <template #default="{ $index }">
            <div style="display: flex; justify-content: center; align-items: center; padding: 5px 0;">
              <div style="width: 300px; height: 180px; border: 1px solid #ebeef5; border-radius: 6px; background: #fafafa; padding: 5px; box-shadow: inset 0 0 8px rgba(0,0,0,0.03);">
                <div :ref="(el) => setChartRef(el, $index)" style="width: 100%; height: 100%;"></div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 多尺度得分明细 -->
        <el-table-column label="多尺度得分" width="260px">
          <template #default="{ row }">
            <div style="padding: 8px 0; display: flex; flex-direction: column; gap: 6px;">
              <div class="score-row">
                <span class="score-tag daily">日线</span>
                <el-progress :percentage="Number((row.scoreDaily * 100).toFixed(1))" :stroke-width="10" :color="'#409EFF'" style="flex: 1;" />
                <span class="score-num">{{ (row.scoreDaily * 100).toFixed(1) }}%</span>
              </div>
              <div class="score-row">
                <span class="score-tag weekly">周线</span>
                <el-progress :percentage="Number((row.scoreWeekly * 100).toFixed(1))" :stroke-width="10" :color="'#E6A23C'" style="flex: 1;" />
                <span class="score-num">{{ (row.scoreWeekly * 100).toFixed(1) }}%</span>
              </div>
              <div class="score-row">
                <span class="score-tag monthly">月线</span>
                <el-progress :percentage="Number((row.scoreMonthly * 100).toFixed(1))" :stroke-width="10" :color="'#67C23A'" style="flex: 1;" />
                <span class="score-num">{{ (row.scoreMonthly * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 融合相似度 -->
        <el-table-column label="融合相似度" width="180px">
          <template #default="{ row }">
            <div style="display: flex; justify-content: center; align-items: center; padding: 10px 0;">
              <el-progress
                type="circle"
                :percentage="Number((row.fusionScore * 100).toFixed(1))"
                :width="70"
                :stroke-width="5"
                :color="customColors"
              />
            </div>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              plain
              style="border-radius: 12px;"
              @click="applyStockToMain(row)"
            >
              定位到主图
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ====== 实时查找结果（三图并排） ====== -->
    <div v-if="hasRealtimeResults" class="result-panel">
      <div class="result-header" style="display: flex; align-items: center; justify-content: space-between;">
        <h4 class="result-title">
          <el-icon style="margin-right: 6px;"><Aim /></el-icon>
          实时查找结果（最近走势）
          <span class="result-count">共 {{ sortedRealtimeResults.length }} 只</span>
        </h4>
        <el-radio-group v-model="primaryScale" size="small">
          <el-radio-button label="dtw_daily">按日线相似度排序</el-radio-button>
          <el-radio-button label="dtw_weekly">按周线相似度排序</el-radio-button>
        </el-radio-group>
      </div>

      <el-table :data="sortedRealtimeResults" border stripe style="width: 100%; border-radius: 8px;">
        <!-- 股票信息 -->
        <el-table-column label="证券信息" width="140px" align="center">
          <template #default="{ row }">
            <div style="display: flex; flex-direction: column;">
              <span style="font-weight: bold; font-size: 13px;">{{ row.stock_name }}</span>
              <span style="font-size: 11px; color: #909399;">{{ row.stock_code }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 日线（主图，放大） -->
        <el-table-column label="日线（主图）" width="320px" align="center">
          <template #default="{ row, $index }">
            <div style="display: flex; flex-direction: column; align-items: center;">
              <div :ref="el => setRealtimeChartRef(el, $index, 'daily')" style="width: 300px; height: 180px; border: 1px solid #ebeef5; border-radius: 4px;"></div>
              <el-progress :percentage="Math.round((row.dtw_daily || 0) * 100)" :stroke-width="10" :format="() => (row.dtw_daily || 0).toFixed(4)" style="width: 280px; margin-top: 4px;" color="#409EFF" />
            </div>
          </template>
        </el-table-column>

        <!-- 周线（缩略） -->
        <el-table-column label="周线" width="220px" align="center">
          <template #default="{ row, $index }">
            <div style="display: flex; flex-direction: column; align-items: center;">
              <div v-if="row.recent_data_weekly && row.recent_data_weekly.length > 0">
                <div :ref="el => setRealtimeChartRef(el, $index, 'weekly')" style="width: 200px; height: 120px; border: 1px solid #ebeef5; border-radius: 4px;"></div>
                <el-progress :percentage="Math.round((row.dtw_weekly || 0) * 100)" :stroke-width="8" :format="() => (row.dtw_weekly || 0).toFixed(4)" style="width: 190px; margin-top: 4px;" color="#67C23A" />
              </div>
              <span v-else style="color: #c0c4cc; font-size: 12px;">无周线数据</span>
            </div>
          </template>
        </el-table-column>

        <!-- 5分钟线（占位） -->
        <el-table-column label="5分钟线" width="160px" align="center">
          <template #default>
            <div style="width: 140px; height: 120px; border: 1px dashed #dcdfe6; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #fafafa;">
              <span style="color: #c0c4cc; font-size: 11px;">待数据接入</span>
            </div>
          </template>
        </el-table-column>

        <!-- 操作列：历史回测 -->
        <el-table-column label="详情" width="120px" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" :loading="row._loading" @click="showHistoryDetail(row)">
              <el-icon style="margin-right: 2px;"><TrendCharts /></el-icon>
              历史回测
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ====== 历史形态回测报告抽屉 ====== -->
    <el-drawer v-model="historyDrawerVisible" :title="`${drawerStockName} 历史形态回测报告`" direction="rtl" size="45%" :destroy-on-close="true">
      <div v-loading="historyLoading" style="padding: 0 20px 20px;">
        <!-- 未来天数选择器 -->
        <div v-if="historyData" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding: 10px 14px; background: #f5f7fa; border-radius: 8px;">
          <span style="font-size: 13px; color: #606266;">预测天数:</span>
          <el-radio-group v-model="futureDays" size="small" @change="recomputeHistory">
            <el-radio-button :label="5">5天</el-radio-button>
            <el-radio-button :label="10">10天</el-radio-button>
            <el-radio-button :label="20">20天</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 板块A：胜率统计 -->
        <div v-if="historyData" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
          <div style="text-align: center; padding: 14px 8px; border-radius: 8px; background: #f0f9eb; border: 1px solid #e1f3d8;">
            <div style="font-size: 11px; color: #909399;">历史出现次数</div>
            <div style="font-size: 24px; font-weight: bold; color: #67C23A;">{{ historyData.total_matches }}</div>
          </div>
          <div style="text-align: center; padding: 14px 8px; border-radius: 8px;" :style="{ background: historyData.win_rate >= 60 ? '#fef0f0' : '#fdf6ec', border: '1px solid ' + (historyData.win_rate >= 60 ? '#fde2e2' : '#faecd8') }">
            <div style="font-size: 11px; color: #909399;">形态胜率</div>
            <div style="font-size: 24px; font-weight: bold;" :style="{ color: historyData.win_rate >= 60 ? '#F56C6C' : '#E6A23C' }">{{ historyData.win_rate }}%</div>
          </div>
          <div style="text-align: center; padding: 14px 8px; border-radius: 8px;" :style="{ background: historyData.avg_return >= 0 ? '#fef0f0' : '#f0f9eb', border: '1px solid ' + (historyData.avg_return >= 0 ? '#fde2e2' : '#e1f3d8') }">
            <div style="font-size: 11px; color: #909399;">{{ historyData.future_days }}日平均涨幅</div>
            <div style="font-size: 24px; font-weight: bold;" :style="{ color: historyData.avg_return >= 0 ? '#F56C6C' : '#67C23A' }">{{ historyData.avg_return > 0 ? '+' : '' }}{{ historyData.avg_return }}%</div>
          </div>
          <div style="text-align: center; padding: 14px 8px; border-radius: 8px; background: #f4f4f5; border: 1px solid #e9e9eb;">
            <div style="font-size: 11px; color: #909399;">平均最大回撤</div>
            <div style="font-size: 24px; font-weight: bold; color: #909399;">-{{ historyData.avg_max_drawdown }}%</div>
          </div>
        </div>

        <!-- 板块B：未来路径束合图 -->
        <div v-if="historyData && historyData.matches.length > 0" style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px; font-size: 14px; color: #303133;">未来{{ historyData.future_days }}日走势路径束合图（以匹配完成日为基准）</h4>
          <div ref="pathChartRef" style="width: 100%; height: 280px; border: 1px solid #ebeef5; border-radius: 8px;"></div>
        </div>

        <!-- 板块C：历史匹配卡片 -->
        <div v-if="historyData && historyData.matches.length > 0">
          <h4 style="margin: 0 0 8px; font-size: 14px; color: #303133;">历史匹配详情</h4>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div v-for="(m, idx) in historyData.matches" :key="idx"
                 style="display: flex; gap: 12px; padding: 10px; border-radius: 8px; border: 1px solid #ebeef5;"
                 :style="{ background: m.is_up ? '#fff8f8' : '#f8fff8' }">
              <div :ref="el => setHistoryChartRef(el, idx)" style="width: 280px; height: 80px; flex-shrink: 0; border: 1px solid #ebeef5; border-radius: 4px; background: #fff;"></div>
              <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 4px;">
                <div style="font-size: 13px; font-weight: bold;">{{ m.start_date }} ~ {{ m.end_date }}</div>
                <div style="font-size: 12px;">
                  <el-tag size="small" type="info">DTW {{ m.dtw_score }}</el-tag>
                  <el-tag size="small" :type="m.is_up ? 'danger' : 'success'" style="margin-left: 4px;">
                    {{ m.future_return > 0 ? '+' : '' }}{{ m.future_return }}%
                  </el-tag>
                </div>
                <div style="font-size: 11px; color: #909399;">最大回撤 -{{ m.max_drawdown }}%</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="historyData && historyData.matches.length === 0" style="text-align: center; padding: 40px; color: #909399;">
          历史上未找到相似片段
        </div>

        <!-- YOLO全景图入口按钮 -->
        <div v-if="rawHistoryData && rawHistoryData.yolo_all_hits && rawHistoryData.yolo_all_hits.length > 0" style="margin-top: 20px; text-align: center;">
          <el-button type="primary" plain @click="yoloDialogVisible = true">
            <el-icon style="margin-right: 4px;"><FullScreen /></el-icon>
            查看 YOLO 检测全景图 ({{ rawHistoryData.yolo_all_hits.length }}个候选)
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- YOLO全景图全屏弹窗 -->
    <el-dialog v-model="yoloDialogVisible" :title="`${drawerStockName} - YOLO检测全景图`" fullscreen :destroy-on-close="true" @opened="renderYoloPanorama">
      <div ref="yoloPanoramaRef" style="width: 100%; height: calc(100vh - 120px);"></div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { useStore } from "vuex";
import axios from "axios";
import * as echarts from "echarts";
import { ElMessage } from "element-plus";
import { DataAnalysis, List, VideoPlay, SetUp, Aim, View, TrendCharts, FullScreen } from '@element-plus/icons-vue';

const store = useStore();
const API_BASE_URL = 'http://127.0.0.1:5000';

// ============ 状态 ============
const selectedModelToUse = ref('');
const isScanning = ref(false);
const hasScanResults = ref(false);
const scanResults = ref([]);
const tableData = ref([]);
const chartRefs = ref([]);

// ============ 多尺度权重 ============
const wMin5 = ref(0);
const wDaily = ref(50);
const wWeekly = ref(50);

const weightSum = computed(() => wMin5.value + wDaily.value + wWeekly.value);

const customColors = [
  { color: '#909399', percentage: 40 },
  { color: '#e6a23c', percentage: 60 },
  { color: '#67c23a', percentage: 80 },
  { color: '#f56c6c', percentage: 100 }
];

// ============ 计算属性 ============
const customModels = computed(() => {
  return store.getters.getModeListSelf || store.state.modeListSelf || [];
});

// 当前分析模式：优先用所选模型的 analysis_mode，兜底用左侧栏的
const currentAnalysisMode = computed(() => {
  const model = customModels.value.find(m => m.index === selectedModelToUse.value);
  if (model && model.analysis_mode) {
    return model.analysis_mode.toUpperCase();
  }
  return (store.state.newSearchInfo.analysisMode || 'MA').toUpperCase();
});

// ============ 模型预览图 ============
const modelPreviewRef = ref(null);
const modelPreviewData = ref(null);
const modelPreviewMode = ref('MA');

// 选择模型时加载预览数据
watch(selectedModelToUse, async (newVal) => {
  if (!newVal) {
    modelPreviewData.value = null;
    return;
  }
  try {
    // 先从模型元数据文件读取（训练时持久化的骨架）
    const res = await axios.post(`${API_BASE_URL}/api/get_model_meta`, { model_name: newVal });
    if (res.data.success && res.data.meta) {
      const meta = res.data.meta;
      modelPreviewMode.value = meta.analysisMode || 'MA';
      if (modelPreviewMode.value.toUpperCase() === 'KLINE') {
        const skeleton = meta.custom_skeleton || [];
        if (skeleton.length >= 2) {
          modelPreviewData.value = { type: 'skeleton', points: skeleton };
        } else if (meta.segmentData && meta.segmentData.length > 0) {
          modelPreviewData.value = { type: 'segment', data: meta.segmentData[0] };
        } else {
          modelPreviewData.value = null;
        }
      } else {
        const segData = meta.segmentData || [];
        modelPreviewData.value = segData.length > 0 ? { type: 'segment', data: segData[0] } : null;
      }
      if (modelPreviewData.value) {
        await nextTick();
        setTimeout(() => renderModelPreview(), 100);
      }
      return;
    }
    // 兜底：从 brush_history 读取
    const res2 = await axios.post(`${API_BASE_URL}/get_brush_info`, { timestamp: newVal });
    if (res2.data.success && res2.data.info) {
      const info = res2.data.info;
      modelPreviewMode.value = info.analysisMode || 'MA';
      if (modelPreviewMode.value.toUpperCase() === 'KLINE') {
        const skeleton = info.custom_skeleton || info.skeletonPoints || [];
        modelPreviewData.value = skeleton.length >= 2 ? { type: 'skeleton', points: skeleton } : null;
      } else {
        const segData = info.segmentData || [];
        modelPreviewData.value = segData.length > 0 ? { type: 'segment', data: segData } : null;
      }
      if (modelPreviewData.value) {
        await nextTick();
        setTimeout(() => renderModelPreview(), 100);
      }
    } else {
      modelPreviewData.value = null;
    }
  } catch (e) {
    modelPreviewData.value = null;
  }
});

const renderModelPreview = () => {
  if (!modelPreviewRef.value || !modelPreviewData.value) return;
  let chart = echarts.getInstanceByDom(modelPreviewRef.value);
  if (chart) chart.dispose();
  chart = echarts.init(modelPreviewRef.value);

  const preview = modelPreviewData.value;
  const mode = modelPreviewMode.value.toUpperCase();
  const maColorMap = { MA4:'#cd1f0e', MA8:'#edbf09', MA12:'#62c613', MA16:'#1286ff', MA20:'#9f12ff', MA47:'#000000' };

  let series = [];
  const allVals = [];

  if (preview.type === 'skeleton') {
    // 骨架折线图
    const pts = [...preview.points].sort((a, b) => new Date(a.date) - new Date(b.date));
    const prices = pts.map(p => Number(p.price));
    series.push({
      type: 'line',
      data: prices,
      showSymbol: true,
      symbolSize: 8,
      lineStyle: { width: 2.5, color: '#409EFF' },
      itemStyle: { color: '#E6A23C' },
      areaStyle: { color: 'rgba(64,158,255,0.1)' },
    });
    allVals.push(...prices);
  } else {
    const rawData = preview.data;
    if (mode === 'KLINE') {
      series.push({
        type: 'candlestick',
        data: rawData.map(d => [Number(d.open||d.close), Number(d.close), Number(d.low||d.close), Number(d.high||d.close)]),
        itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' }
      });
      rawData.forEach(d => ['high','low'].forEach(k => { const v = Number(d[k]); if (v > 0) allVals.push(v); }));
    } else {
      for (const [ma, color] of Object.entries(maColorMap)) {
        const vals = rawData.map(d => Number(d[ma] || 0)).filter(v => v > 0);
        if (vals.length > 0) {
          series.push({ name: ma, type: 'line', showSymbol: false, lineStyle: { width: 1.5, color }, data: rawData.map(d => Number(d[ma] || null)) });
          vals.forEach(v => allVals.push(v));
        }
      }
    }
  }

  // x轴标签
  let xLabels;
  if (preview.type === 'skeleton') {
    xLabels = [...preview.points].sort((a, b) => new Date(a.date) - new Date(b.date)).map(p => {
      const d = new Date(p.date);
      return `${d.getMonth()+1}/${d.getDate()}`;
    });
  } else {
    xLabels = (preview.data || []).map((_, i) => i + 1);
  }

  const dMin = allVals.length > 0 ? Math.min(...allVals) : 0;
  const dMax = allVals.length > 0 ? Math.max(...allVals) : 1;
  const pad = (dMax - dMin) * 0.1 || 1;

  chart.setOption({
    animation: false,
    grid: { left: 40, right: 10, top: 10, bottom: 25 },
    xAxis: { type: 'category', data: xLabels, axisLabel: { fontSize: 9 } },
    yAxis: { type: 'value', scale: true, axisLabel: { fontSize: 9 }, min: dMin - pad, max: dMax + pad },
    series
  });
};

const targetPoolCount = computed(() => {
  let pool = store.state.searchInfo.stockList.map(item => item.code);
  if (!pool || pool.length === 0) {
    pool = store.state.stockList.filter(item => item.isSelected).map(item => item.code);
    if (pool.length === 0) {
      pool = store.state.stockList.slice(0, 100).map(item => item.code);
    }
  }
  return pool.length;
});

const scanDateRangeDisplay = computed(() => {
  let start = store.state.searchInfo.searchStartDate;
  let end = store.state.searchInfo.searchEndDate;
  if (start instanceof Date) start = formatDateToLocal(start);
  if (end instanceof Date) end = formatDateToLocal(end);
  return `${start || '2016-01-01'} 至 ${end || '2021-12-31'}`;
});

// ============ 工具函数 ============
function formatDateToLocal(date) {
  if (!date) return null;
  let processedDate = date;
  if (!(processedDate instanceof Date) || isNaN(processedDate.getTime())) {
    try {
      const parsedDate = new Date(date);
      if (!isNaN(parsedDate.getTime())) processedDate = parsedDate;
      else return null;
    } catch (e) { return null; }
  }
  const year = processedDate.getFullYear();
  const month = String(processedDate.getMonth() + 1).padStart(2, '0');
  const day = String(processedDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// ============ 核心：多尺度融合扫描 API 调用 ============
const doModelScan = async () => {
  const resultPool = store.state.searchInfo.stockList.map(item => item.code);
  const maNumbers = store.state.modeInfo.lines
    .filter(item => item.startsWith('MA'))
    .map(maItem => Number(maItem.slice(2)));

  const timestamp = new Date().getTime();
  const requestParams = {
    mode_index: store.state.modeInfo.index,
    stock_pool: resultPool,
    start_date: store.state.searchInfo.searchStartDate,
    end_date: store.state.searchInfo.searchEndDate,
    ma_list: maNumbers,
    window_size: 20,
    w_d: wDaily.value / 100,
    w_w: wWeekly.value / 100,
    w_m: 0
  };

  try {
    const response = await axios.post(
      `${API_BASE_URL}/detect_logic_pattern?timestamp=${timestamp}`,
      requestParams
    );

    if (response.data.result && response.data.result.length > 0) {
      const base_periods = response.data.base_ma_periods || maNumbers;
      const maFields = base_periods.map(period => `MA${period}`);

      return response.data.result.map(stock => {
        if (!stock.recent_data || stock.recent_data.length === 0) return stock;
        const rawData = JSON.parse(JSON.stringify(stock.recent_data));
        const twoDArray = stock.recent_data.map(item => maFields.map(field => item[field]));
        const transposed = [];
        for (let j = 0; j < maFields.length; j++) {
          transposed[j] = [];
          for (let i = 0; i < twoDArray.length; i++) {
            transposed[j][i] = twoDArray[i][j];
          }
        }
        return {
          ...stock,
          recent_data: transposed,
          recent_data_raw: rawData
        };
      });
    }
    return [];
  } catch (err) {
    ElMessage.error('多尺度融合扫描失败，请检查控制台');
    return null;
  }
};

// ============ 扫描入口 ============
const runModelScan = async () => {
  if (!selectedModelToUse.value) {
    ElMessage.warning('请先选择一个要应用的形态模型');
    return;
  }
  if (weightSum.value !== 100) {
    ElMessage.warning('权重总和需等于 100%');
    return;
  }

  let searchStart = store.state.searchInfo.searchStartDate;
  let searchEnd = store.state.searchInfo.searchEndDate;
  if (!searchStart || searchStart === '--') searchStart = '2016-01-01';
  if (!searchEnd || searchEnd === '--') searchEnd = '2024-12-31';
  if (searchStart instanceof Date) searchStart = formatDateToLocal(searchStart);
  if (searchEnd instanceof Date) searchEnd = formatDateToLocal(searchEnd);

  const modelDetail = customModels.value.find(m => m.index === selectedModelToUse.value);
  if (!modelDetail) return;

  store.commit('updateModeInfo', {
    index: modelDetail.index,
    name: modelDetail.name,
    lines: ["个股", ...modelDetail.lines],
    isMode: true,
  });

  store.state.searchInfo.searchStartDate = searchStart;
  store.state.searchInfo.searchEndDate = searchEnd;

  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction: "逻辑模式回测(自定义)",
    isDisabled: true,
    isChooseStock: false,
    isHistorySearch: false,
    isHistorySearchNew: true,
  });

  isScanning.value = true;
  hasScanResults.value = false;

  const results = await doModelScan();

  isScanning.value = false;

  if (results && results.length > 0) {
    store.state.sim_stock_list = results;
    store.state.baseInfo.isMode = true;
    store.state.baseInfo.isStock = true;
    scanResults.value = results;
    hasScanResults.value = true;
    ElMessage.success(`多尺度融合扫描完成，共找到 ${results.length} 个高相似度形态！`);
  } else if (results && results.length === 0) {
    hasScanResults.value = false;
    ElMessage.warning('扫描完成，未在指定时间范围内找到符合该形态的股票');
  }
};

// ============ YOLO 训练 ============
const isTrainingYolo = ref(false);

const trainYolo = async () => {
  if (!selectedModelToUse.value) {
    ElMessage.warning('请先选择一个形态模型');
    return;
  }
  const resultPool = store.state.searchInfo.stockList.map(item => item.code);
  const maNumbers = store.state.modeInfo.lines
    .filter(item => item.startsWith('MA'))
    .map(maItem => Number(maItem.slice(2)));

  isTrainingYolo.value = true;
  try {
    const res = await axios.post(`${API_BASE_URL}/api/train_yolo`, {
      mode_index: selectedModelToUse.value,
      stock_pool: resultPool.length > 0 ? resultPool : store.state.stockList.slice(0, 100).map(item => item.code),
      ma_list: maNumbers,
      epochs: 80,
    });
    if (res.data.success) {
      ElMessage.success(`YOLO 训练完成！正样本 ${res.data.pos_count} 张，负样本 ${res.data.neg_count} 张`);
    } else {
      ElMessage.error(res.data.msg || '训练失败');
    }
  } catch (err) {
    ElMessage.error('YOLO 训练失败: ' + (err.response?.data?.msg || err.message));
  } finally {
    isTrainingYolo.value = false;
  }
};

// ============ YOLO 快速扫描 ============
const isYoloScanning = ref(false);

const runYoloScan = async () => {
  if (!selectedModelToUse.value) {
    ElMessage.warning('请先选择一个形态模型');
    return;
  }

  const resultPool = store.state.searchInfo.stockList.map(item => item.code);
  const maNumbers = store.state.modeInfo.lines
    .filter(item => item.startsWith('MA'))
    .map(maItem => Number(maItem.slice(2)));

  let searchStart = store.state.searchInfo.searchStartDate;
  let searchEnd = store.state.searchInfo.searchEndDate;
  if (!searchStart || searchStart === '--') searchStart = '2016-01-01';
  if (!searchEnd || searchEnd === '--') searchEnd = '2024-12-31';
  if (searchStart instanceof Date) searchStart = formatDateToLocal(searchStart);
  if (searchEnd instanceof Date) searchEnd = formatDateToLocal(searchEnd);

  const modelDetail = customModels.value.find(m => m.index === selectedModelToUse.value);
  if (!modelDetail) return;

  store.commit('updateModeInfo', {
    index: modelDetail.index,
    name: modelDetail.name,
    lines: ["个股", ...modelDetail.lines],
    isMode: true,
  });

  isYoloScanning.value = true;
  hasScanResults.value = false;

  try {
    const res = await axios.post(`${API_BASE_URL}/api/detect_yolo_pattern`, {
      mode_index: selectedModelToUse.value,
      stock_pool: resultPool.length > 0 ? resultPool : store.state.stockList.slice(0, 100).map(item => item.code),
      start_date: searchStart,
      end_date: searchEnd,
      ma_list: maNumbers,
      conf_threshold: 0.3,
    });

    if (res.data.success && res.data.result && res.data.result.length > 0) {
      const base_periods = res.data.base_ma_periods || maNumbers;
      const maFields = base_periods.map(period => `MA${period}`);
      const results = res.data.result.map(stock => {
        if (!stock.recent_data || stock.recent_data.length === 0) return stock;
        const rawData = JSON.parse(JSON.stringify(stock.recent_data));
        const twoDArray = stock.recent_data.map(item => maFields.map(field => item[field]));
        const transposed = [];
        for (let j = 0; j < maFields.length; j++) {
          transposed[j] = [];
          for (let i = 0; i < twoDArray.length; i++) {
            transposed[j][i] = twoDArray[i][j];
          }
        }
        return {
          ...stock,
          recent_data: transposed,
          recent_data_raw: rawData,
        };
      });

      store.state.sim_stock_list = results;
      store.state.baseInfo.isMode = true;
      store.state.baseInfo.isStock = true;
      scanResults.value = results;
      hasScanResults.value = true;
      ElMessage.success(`YOLO 快速扫描完成，共找到 ${results.length} 个形态！`);
    } else if (res.data.success) {
      hasScanResults.value = false;
      ElMessage.warning('YOLO 扫描完成，未检测到目标形态');
    } else {
      ElMessage.error(res.data.msg || 'YOLO 扫描失败');
    }
  } catch (err) {
    ElMessage.error('YOLO 扫描失败: ' + (err.response?.data?.msg || err.message));
  } finally {
    isYoloScanning.value = false;
  }
};

// ============ 实时查找（双阶段 + 三尺度） ============
const isRealtimeScanning = ref(false);
const realtimeResults = ref([]);
const hasRealtimeResults = ref(false);
const primaryScale = ref('dtw_daily'); // dtw_daily / dtw_weekly / daily / weekly / min5
const realtimeChartRefs = ref([]);

const setRealtimeChartRef = (el, index, scale) => {
  if (el) {
    if (!realtimeChartRefs.value[index]) realtimeChartRefs.value[index] = {};
    realtimeChartRefs.value[index][scale] = el;
  }
};

// 按主尺度排序的 computed
const sortedRealtimeResults = computed(() => {
  const key = primaryScale.value.startsWith('dtw_') ? primaryScale.value : 'score_' + primaryScale.value;
  return [...realtimeResults.value].sort((a, b) => (b[key] || 0) - (a[key] || 0));
});

const runRealtimeScan = async () => {
  if (!selectedModelToUse.value) {
    ElMessage.warning('请先选择一个形态模型');
    return;
  }

  const resultPool = store.state.searchInfo.stockList.map(item => item.code);
  const pool = resultPool.length > 0
    ? resultPool.map(code => ({ code, name: store.state.stockList.find(s => s.code === code)?.name || code }))
    : store.state.stockList.slice(0, 100).map(item => ({ code: item.code, name: item.name }));

  const maNumbers = store.state.modeInfo.lines
    .filter(item => item.startsWith('MA'))
    .map(maItem => Number(maItem.slice(2)));

  // 规则标签从 extractedFeatures 获取
  const extracted = store.state.newSearchInfo.extractedFeatures?.auto || [];
  const ruleTags = extracted.map(f => typeof f === 'string' ? f : `${f.desc || ''} ${f.hasValue && f.value != null ? f.value + (f.unit || '') : ''}`.trim());

  // 从用户框选区间获取实际日期范围（让后端按实际交易日数确定窗口大小）
  const brushRanges = store.state.newSearchInfo.savedBrushTimeRanges || [];
  const firstBrush = brushRanges[0] || {};
  const brush_start = firstBrush.startDate || '';
  const brush_end = firstBrush.endDate || '';

  isRealtimeScanning.value = true;
  hasRealtimeResults.value = false;

  try {
    const res = await axios.post(`${API_BASE_URL}/api/realtime_scan`, {
      mode_index: selectedModelToUse.value,
      stock_pool: pool,
      ma_list: maNumbers,
      rule_tags: ruleTags,
      rule_prompt: store.state.newSearchInfo.extractedFeatures?.custom || '',
      brush_start,
      brush_end,
    });

    if (res.data.success && res.data.result && res.data.result.length > 0) {
      realtimeResults.value = res.data.result;
      hasRealtimeResults.value = true;
      primaryScale.value = 'dtw_daily';
      ElMessage.success(`实时查找完成，共 ${res.data.result.length} 只匹配（视觉通过${res.data.stats?.pass_visual || 0}，规则通过${res.data.stats?.pass_rule || 0}）`);

      await nextTick();
      setTimeout(() => renderRealtimeCharts(), 300);
    } else if (res.data.success) {
      hasRealtimeResults.value = false;
      ElMessage.warning('实时查找完成，未找到匹配股票');
    } else {
      ElMessage.error(res.data.msg || '实时查找失败');
    }
  } catch (err) {
    ElMessage.error('实时查找失败: ' + (err.response?.data?.msg || err.message));
  } finally {
    isRealtimeScanning.value = false;
  }
};

const renderRealtimeCharts = () => {
  const mode = currentAnalysisMode.value;
  const maColorMap = { MA4:'#cd1f0e', MA8:'#edbf09', MA12:'#62c613', MA16:'#1286ff', MA20:'#9f12ff', MA47:'#000000' };

  sortedRealtimeResults.value.forEach((item, idx) => {
    ['daily', 'weekly'].forEach(scale => {
      const dom = realtimeChartRefs.value[idx]?.[scale];
      if (!dom) return;
      let chart = echarts.getInstanceByDom(dom);
      if (chart) chart.dispose();
      chart = echarts.init(dom);

      const rawData = scale === 'daily' ? item.recent_data_daily : item.recent_data_weekly;
      if (!rawData || rawData.length === 0) return;

      const allVals = [];
      if (mode === 'MA') {
        Object.keys(maColorMap).forEach(ma => rawData.forEach(d => { const v = Number(d[ma]); if (v > 0) allVals.push(v); }));
      } else {
        rawData.forEach(d => ['open','close','high','low'].forEach(k => { const v = Number(d[k]); if (v > 0) allVals.push(v); }));
      }
      const dMin = allVals.length > 0 ? Math.min(...allVals) : 0;
      const dMax = allVals.length > 0 ? Math.max(...allVals) : 1;
      const pad = (dMax - dMin) * 0.1 || 1;

      let series;
      if (mode === 'MA') {
        series = Object.entries(maColorMap).filter(([ma]) => rawData[0] && rawData[0][ma] != null)
          .map(([ma, color]) => ({ name: ma, type: 'line', showSymbol: false, lineStyle: { width: scale === 'daily' ? 1.5 : 1, color }, data: rawData.map(d => Number(d[ma])) }));
      } else {
        series = [{ type: 'candlestick', data: rawData.map(d => [Number(d.open), Number(d.close), Number(d.low), Number(d.high)]), itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' } }];
      }

      chart.setOption({
        animation: false,
        grid: { left: 5, right: 5, top: 8, bottom: 5 },
        xAxis: { type: 'category', show: false, boundaryGap: false },
        yAxis: { type: 'value', show: false, min: dMin - pad, max: dMax + pad, scale: true },
        series
      });
      echarts.connect('realtime_' + idx);
    });
  });
};

// 主尺度切换时重新渲染
watch(primaryScale, () => {
  nextTick(() => setTimeout(() => renderRealtimeCharts(), 100));
});

// ============ 历史形态回测 ============
const historyDrawerVisible = ref(false);
const historyLoading = ref(false);
const historyData = ref(null);
const rawHistoryData = ref(null);  // 后端原始数据（20天）
const drawerStockName = ref('');
const drawerRow = ref(null);
const futureDays = ref(10);
const pathChartRef = ref(null);
const yoloPanoramaRef = ref(null);
const yoloDialogVisible = ref(false);
const historyChartRefs = ref([]);

const setHistoryChartRef = (el, idx) => {
  if (el) historyChartRefs.value[idx] = el;
};

const showHistoryDetail = async (row) => {
  drawerRow.value = row;
  drawerStockName.value = `${row.stock_name} (${row.stock_code})`;
  historyDrawerVisible.value = true;
  await fetchHistoryData();
};

const refetchHistory = async () => {
  // 不再重新请求，改为本地切片
  recomputeHistory();
};

// 本地按天数切片重新计算（不重新请求后端）
const recomputeHistory = () => {
  if (!rawHistoryData.value) return;
  const days = futureDays.value;
  const rawMatches = rawHistoryData.value.matches || [];

  const sliced = rawMatches.map(m => {
    const path = (m.norm_path_full || []).slice(0, days);
    const futureReturn = path.length > 0 ? path[path.length - 1] : 0;
    // 最大回撤
    let peak = 0, maxDd = 0;
    path.forEach(v => { if (v > peak) peak = v; const dd = peak - v; if (dd > maxDd) maxDd = dd; });
    return {
      ...m,
      norm_path: path,
      future_return: Math.round(futureReturn * 100) / 100,
      max_drawdown: Math.round(maxDd * 100) / 100,
      is_up: futureReturn > 0,
      future_data: (m.future_data || []).slice(0, days),
      future_dates: (m.future_dates || []).slice(0, days),
    };
  });

  // 统计
  const total = sliced.length;
  const upCount = sliced.filter(m => m.is_up).length;
  const winRate = total > 0 ? Math.round(upCount / total * 1000) / 10 : 0;
  const avgReturn = total > 0 ? Math.round(sliced.reduce((s, m) => s + m.future_return, 0) / total * 100) / 100 : 0;
  const avgDd = total > 0 ? Math.round(sliced.reduce((s, m) => s + m.max_drawdown, 0) / total * 100) / 100 : 0;

  historyData.value = {
    total_matches: total,
    up_count: upCount,
    win_rate: winRate,
    avg_return: avgReturn,
    avg_max_drawdown: avgDd,
    future_days: days,
    matches: sliced,
  };

  nextTick(() => setTimeout(() => { renderPathChart(); renderHistoryCards(); }, 100));
};

const fetchHistoryData = async () => {
  if (!drawerRow.value) return;
  historyLoading.value = true;
  historyData.value = null;

  try {
    const maNumbers = store.state.modeInfo.lines
      .filter(item => item.startsWith('MA'))
      .map(maItem => Number(maItem.slice(2)));

    const extracted = store.state.newSearchInfo.extractedFeatures?.auto || [];
    const ruleTags = extracted.map(f => typeof f === 'string' ? f : `${f.desc || ''} ${f.hasValue && f.value != null ? f.value + (f.unit || '') : ''}`.trim());

    const res = await axios.post(`${API_BASE_URL}/api/analyze_stock_history`, {
      stock_code: drawerRow.value.stock_code,
      mode_index: selectedModelToUse.value,
      ma_list: maNumbers,
      future_days: futureDays.value,
      dtw_threshold: 0.6,
      rule_tags: ruleTags,
      rule_prompt: store.state.newSearchInfo.extractedFeatures?.custom || '',
    });

    if (res.data.success) {
      rawHistoryData.value = res.data;  // 存原始数据（20天）
      recomputeHistory();  // 按当前天数切片计算
      // 延迟渲染YOLO全景图（等collapse展开后有DOM）
      await nextTick();
      setTimeout(() => renderYoloPanorama(), 300);
    } else {
      ElMessage.warning(res.data.msg || '回测失败');
    }
  } catch (err) {
    ElMessage.error('回测请求失败: ' + (err.response?.data?.msg || err.message));
  } finally {
    historyLoading.value = false;
  }
};

const renderPathChart = () => {
  if (!pathChartRef.value || !historyData.value) return;
  let chart = echarts.getInstanceByDom(pathChartRef.value);
  if (chart) chart.dispose();
  chart = echarts.init(pathChartRef.value);

  const matches = historyData.value.matches;
  const futureDays = historyData.value.future_days;
  const xLabels = Array.from({ length: futureDays + 1 }, (_, i) => i === 0 ? 'Day0\n(基准)' : `+${i}`);

  const series = matches.map((m) => ({
    name: `${m.start_date} ${m.future_return > 0 ? '+' : ''}${m.future_return}%`,
    type: 'line',
    showSymbol: false,
    smooth: true,
    lineStyle: { width: 1.5, color: m.is_up ? '#F56C6C' : '#67C23A', opacity: 0.6 },
    data: [0, ...m.norm_path],
  }));

  // 统计：均值 + 25%/75% 分位置信带
  if (matches.length >= 2) {
    const avgPath = [], p25Path = [], p75Path = [];
    for (let i = 0; i < futureDays; i++) {
      const vals = matches.map(m => m.norm_path[i] || 0).sort((a, b) => a - b);
      const n = vals.length;
      avgPath.push(vals.reduce((a, b) => a + b, 0) / n);
      p25Path.push(vals[Math.floor(n * 0.25)] || vals[0]);
      p75Path.push(vals[Math.floor(n * 0.75)] || vals[n - 1]);
    }
    // 置信区间带（75%上界填充 + 25%下界透明覆盖形成带状）
    series.push({
      name: '75%分位', type: 'line', showSymbol: false,
      lineStyle: { width: 0 }, stack: 'confidence',
      areaStyle: { color: 'rgba(64,158,255,0.15)' },
      data: [0, ...p75Path], z: 1,
    });
    series.push({
      name: '25%分位', type: 'line', showSymbol: false,
      lineStyle: { width: 0 }, stack: 'confidence-negative',
      areaStyle: { color: '#fff', opacity: 1 },
      data: [0, ...p25Path], z: 2,
    });
    // 平均路径
    series.push({
      name: '平均路径', type: 'line', showSymbol: true, symbolSize: 5,
      lineStyle: { width: 3, color: '#409EFF', type: 'dashed' },
      data: [0, ...avgPath], z: 10,
    });
  }

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const dayIdx = params[0]?.dataIndex || 0;
        const dayLabel = dayIdx === 0 ? 'Day 0 (基准日)' : `+${dayIdx} 天`;
        let html = `<div style="font-weight:bold;margin-bottom:4px;">${dayLabel}</div>`;
        params.forEach(p => {
          const matchIdx = matches.findIndex(m => `${m.start_date} ${m.future_return > 0 ? '+' : ''}${m.future_return}%` === p.seriesName);
          let dateStr = '';
          if (p.seriesName === '平均路径' || p.seriesName === '75%分位' || p.seriesName === '25%分位') {
            dateStr = p.seriesName;
          } else if (matchIdx >= 0 && dayIdx > 0) {
            const fd = matches[matchIdx].future_dates;
            dateStr = fd[dayIdx - 1] ? `${p.seriesName} [${fd[dayIdx - 1]}]` : p.seriesName;
          } else {
            dateStr = p.seriesName;
          }
          const val = p.value;
          const color = val >= 0 ? '#F56C6C' : '#67C23A';
          html += `<div style="display:flex;justify-content:space-between;gap:12px;">
            <span>${p.marker} ${dateStr}</span>
            <span style="color:${color};font-weight:bold;">${val > 0 ? '+' : ''}${val.toFixed(2)}%</span>
          </div>`;
        });
        return html;
      },
    },
    legend: { show: false },
    grid: { left: 50, right: 20, top: 15, bottom: 35 },
    xAxis: { type: 'category', data: xLabels, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '涨幅%', axisLabel: { fontSize: 10, formatter: '{value}%' },
      axisLine: { show: false }, splitLine: { lineStyle: { type: 'dashed' } } },
    series,
  });
};

const renderHistoryCards = () => {
  if (!historyData.value) return;
  const matches = historyData.value.matches;
  const mode = currentAnalysisMode.value;

  matches.forEach((m, idx) => {
    const dom = historyChartRefs.value[idx];
    if (!dom) return;
    let chart = echarts.getInstanceByDom(dom);
    if (chart) chart.dispose();
    chart = echarts.init(dom);

    const matchData = m.match_data || [];
    const futureData = m.future_data || [];
    const allData = [...matchData, ...futureData];
    const splitIdx = matchData.length;
    const xLabels = allData.map((_, i) => i === splitIdx ? '→' : '');

    let series;
    if (mode === 'KLINE') {
      series = [{
        type: 'candlestick',
        data: allData.map(d => [Number(d.open||d.close), Number(d.close), Number(d.low||d.close), Number(d.high||d.close)]),
        itemStyle: { color: '#ec0000', color0: '#00da3c' },
      }, {
        type: 'line', data: allData.map((d, i) => i === splitIdx ? Number(d.close) : null),
        markLine: { silent: true, symbol: 'none', lineStyle: { type: 'dashed', color: '#909399' },
          data: [{ xAxis: splitIdx }] },
        showSymbol: false, lineStyle: { width: 0 },
      }];
    } else {
      const colors = { MA4:'#cd1f0e', MA8:'#edbf09', MA12:'#62c613', MA16:'#1286ff', MA20:'#9f12ff', MA47:'#000000' };
      series = Object.entries(colors).map(([ma, color]) => ({
        type: 'line', showSymbol: false, lineStyle: { width: 1, color },
        data: allData.map(d => (d[ma] == null ? null : Number(d[ma]))),
      }));
    }

    chart.setOption({
      animation: false,
      grid: { left: 2, right: 2, top: 3, bottom: 3 },
      xAxis: { type: 'category', show: false, data: xLabels },
      yAxis: { type: 'value', show: false, scale: true },
      series,
    });
  });
};

// ============ YOLO 全景图渲染 ============
const renderYoloPanorama = () => {
  if (!yoloPanoramaRef.value || !rawHistoryData.value) return;
  let chart = echarts.getInstanceByDom(yoloPanoramaRef.value);
  if (chart) chart.dispose();
  chart = echarts.init(yoloPanoramaRef.value);

  const fullHistory = rawHistoryData.value.full_history || [];
  const yoloHits = rawHistoryData.value.yolo_all_hits || [];
  const finalMatches = (historyData.value?.matches || []).map(m => m.start_date);
  const finalDateSet = new Set(finalMatches);
  const mode = currentAnalysisMode.value;

  const dates = fullHistory.map(d => d.trade_date);

  // YOLO检测区间 → markArea
  const markAreas = yoloHits.map(h => [
    { xAxis: h.start_date, itemStyle: { color: finalDateSet.has(h.start_date) ? 'rgba(103,194,58,0.25)' : 'rgba(245,108,108,0.12)' } },
    { xAxis: h.end_date }
  ]);

  // 标注线（垂直线标注每个YOLO检测的起始位置，比pin标记更清晰）
  const markLines = yoloHits.map(h => ({
    xAxis: h.start_date,
    label: {
      show: true,
      formatter: `${(h.confidence * 100).toFixed(0)}%`,
      fontSize: 9,
      color: finalDateSet.has(h.start_date) ? '#67C23A' : '#F56C6C',
      position: 'insideEndTop',
    },
    lineStyle: {
      color: finalDateSet.has(h.start_date) ? '#67C23A' : '#F56C6C',
      type: finalDateSet.has(h.start_date) ? 'solid' : 'dashed',
      width: finalDateSet.has(h.start_date) ? 2 : 1,
    },
  }));

  // 分段边界标注（灰色虚线，每75天一条）
  const segmentStep = 75;
  const totalLen = dates.length;
  const segmentBoundaries = [];
  for (let s = 0; s < totalLen; s += segmentStep) {
    segmentBoundaries.push({
      xAxis: dates[s],
      lineStyle: { color: '#ccc', type: 'dotted', width: 1 },
      label: { show: false },
    });
  }

  // 默认显示最近60%
  const defaultStart = Math.max(0, 40);

  // 主图 series：K线模式画蜡烛图，MA 模式画 6 色均线
  let mainSeries;
  if (mode === 'KLINE') {
    const klineData = fullHistory.map(d => [
      Number(d.open), Number(d.close), Number(d.low), Number(d.high)
    ]);
    mainSeries = {
      type: 'candlestick',
      data: klineData,
      itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' },
      markArea: { silent: true, data: markAreas },
      markLine: { symbol: 'none', silent: true, animation: false, data: [...markLines, ...segmentBoundaries] },
    };
  } else {
    const maColorMap = { MA4:'#cd1f0e', MA8:'#edbf09', MA12:'#62c613', MA16:'#1286ff', MA20:'#9f12ff', MA47:'#000000' };
    mainSeries = Object.entries(maColorMap).map(([ma, color], idx) => ({
      name: ma,
      type: 'line',
      showSymbol: false,
      lineStyle: { width: 1.2, color },
      data: fullHistory.map(d => Number(d[ma])),
      // 仅第一条线挂标注，避免重复
      ...(idx === 0 ? {
        markArea: { silent: true, data: markAreas },
        markLine: { symbol: 'none', silent: true, animation: false, data: [...markLines, ...segmentBoundaries] },
      } : {}),
    }));
  }

  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { show: false },
    grid: { left: 55, right: 25, top: 15, bottom: 70 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9, rotate: 0 } },
    yAxis: { type: 'value', scale: true, axisLabel: { fontSize: 9 } },
    dataZoom: [
      { type: 'inside', start: defaultStart, end: 100 },
      { type: 'slider', start: defaultStart, end: 100, height: 22, bottom: 15 },
    ],
    series: Array.isArray(mainSeries) ? mainSeries : [mainSeries],
  });
};

// ============ 结果列表：图表渲染 ============
const setChartRef = (el, index) => {
  if (el) chartRefs.value[index] = el;
};

watch(scanResults, (newList) => {
  if (!newList || !Array.isArray(newList)) return;

  tableData.value = newList.map(item => {
    const actualStock = store.state.stockList.find(s => s.code === item.stock_code);
    const displayName = actualStock ? actualStock.name : item.stock_name;
    const rawData = item.recent_data_raw || item.recent_data;

    const sDate = rawData && rawData.length > 0
      ? (rawData[0].trade_date || rawData[0].timestamps || '未知') : '未知';
    const eDate = rawData && rawData.length > 0
      ? (rawData[rawData.length - 1].trade_date || rawData[rawData.length - 1].timestamps || '未知') : '未知';

    return {
      ...item,
      stockName: displayName,
      stockCode: item.stock_code,
      startDate: sDate,
      endDate: eDate,
      fusionScore: item.fusion_score || item.similarity,
      scoreDaily: item.score_daily || 0,
      scoreWeekly: item.score_weekly || 0,
      scoreMonthly: item.score_monthly || 0,
    };
  });

  nextTick(() => {
    setTimeout(() => {
      tableData.value.forEach((_, idx) => initChart(idx));
    }, 150);
  });
}, { immediate: true, deep: true });

const initChart = (index) => {
  const dom = chartRefs.value[index];
  if (!dom) return;

  let myChart = echarts.getInstanceByDom(dom);
  if (myChart) myChart.dispose();
  myChart = echarts.init(dom);

  const row = tableData.value[index];
  const rawData = row.recent_data_raw || row.recent_data;
  if (!rawData || !Array.isArray(rawData) || rawData.length === 0) return;

  const dates = rawData.map(item => item.trade_date || item.timestamps || '');

  const mode = currentAnalysisMode.value;

  const series = [];
  const allValues = [];

  if (mode === 'KLINE') {
    series.push({
      name: 'K线', type: 'candlestick',
      data: rawData.map(item => [
        item.open !== undefined ? item.open : (item.close || 0),
        item.close || 0,
        item.low !== undefined ? item.low : (item.close || 0),
        item.high !== undefined ? item.high : (item.close || 0)
      ]),
      itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' }
    });
    rawData.forEach(item => {
      if (item.high != null) allValues.push(item.high);
      if (item.low != null) allValues.push(item.low);
    });
  } else {
    const maColorMap = { MA4: '#cd1f0e', MA8: '#edbf09', MA12: '#62c613', MA16: '#1286ff', MA20: '#9f12ff', MA47: '#000000' };
    for (const [key, color] of Object.entries(maColorMap)) {
      series.push({ name: key, data: rawData.map(item => item[key]), type: 'line', lineStyle: { width: 1.2, color }, showSymbol: false });
      rawData.forEach(item => { if (item[key] != null) allValues.push(item[key]); });
    }
  }

  const validValues = allValues.filter(v => v != null && !isNaN(v) && v !== 0);
  if (validValues.length === 0) return;

  const minValue = Math.min(...validValues);
  const maxValue = Math.max(...validValues);
  const padding = (maxValue - minValue) * 0.1;

  myChart.setOption({
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', min: minValue - padding, max: maxValue + padding, show: false },
    grid: { left: 5, right: 5, top: 5, bottom: 5 },
    series
  });
};

const applyStockToMain = (row) => {
  store.state.stockShowInfo = { name: row.stockName, code: row.stockCode };
  store.state.modeInfo.startDate = row.startDate;
  store.state.modeInfo.endDate = row.endDate;
  ElMessage.success(`已联动大图定位到股票：${row.stockName} (${row.startDate} 至 ${row.endDate})`);
};
</script>

<style scoped>
.hide-scrollbar::-webkit-scrollbar { display: none; }
.hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.model-usage {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
  background-color: #f7f9fa;
}

/* 配置面板 */
.config-panel {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #ebeef5;
  overflow: hidden;
}

.config-header {
  padding: 20px 24px 0;
}

.config-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.config-desc {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: #909399;
}

.config-body {
  display: flex;
  align-items: stretch;
  padding: 20px 24px 24px;
  gap: 0;
}

.config-section {
  flex: 1;
  min-width: 0;
}

.config-divider {
  width: 1px;
  background: #ebeef5;
  margin: 0 28px;
  align-self: stretch;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
}

/* 模型选择 */
.model-select {
  width: 100%;
}

/* 下拉选项 */
.option-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.option-name {
  font-weight: 600;
  color: #303133;
}

.option-tags {
  font-size: 12px;
  color: #8492a6;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

/* 扫描范围 */
.range-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.range-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.range-label {
  font-size: 12px;
  color: #909399;
}

.range-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.range-date {
  font-size: 14px;
}

/* 多尺度权重面板 */
.weight-panel {
  margin-top: 16px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #ebeef5;
  padding: 16px 24px;
}

.weight-header {
  margin-bottom: 12px;
}

.weight-sum {
  margin-left: auto;
  font-size: 13px;
  font-weight: 600;
  color: #67C23A;
}

.weight-error {
  color: #F56C6C;
}

.weight-sliders {
  display: flex;
  gap: 24px;
}

.weight-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.weight-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
  min-width: 60px;
}

.weight-slider {
  flex: 1;
}

.weight-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  min-width: 42px;
  text-align: right;
}

/* 扫描按钮 */
.scan-action {
  margin-top: 24px;
  text-align: center;
}

.scan-btn {
  width: 260px;
  height: 44px;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 500;
}

.scan-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #c0c4cc;
}

/* 结果面板 */
.result-panel {
  margin-top: 24px;
  padding: 20px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #ebeef5;
}

.result-header {
  margin-bottom: 16px;
}

.result-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  padding-left: 12px;
  border-left: 3px solid #409EFF;
}

.result-count {
  margin-left: 8px;
  font-size: 13px;
  font-weight: 400;
  color: #909399;
}

/* 多尺度得分行 */
.score-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.score-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  color: #fff;
  min-width: 28px;
  text-align: center;
}

.score-tag.daily { background: #409EFF; }
.score-tag.weekly { background: #E6A23C; }
.score-tag.monthly { background: #67C23A; }

.score-num {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  min-width: 42px;
  text-align: right;
}
</style>
