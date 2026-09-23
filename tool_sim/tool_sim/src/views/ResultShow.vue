<!--
  页面说明：
  本页面用于展示【基准股票模式评价】的结果，包括结果表格和每条结果的均线图，支持保存配置和下载结果等操作。
-->
<template>
  <div id="app">

    <div style="
  text-align: left;
  background-color: #faf8e1;
  height: 50px; /* 稍微增加一点高度让按钮看起来不局促 */
  margin-top: 5px;
  display: flex; /* 改为 flex */
  align-items: center; /* 【关键】：垂直居中 */
  width: 99%;
  border-radius: 10px;
  margin-left: 5px;
">
      <span style="font-weight: bold; margin-left: 20px; font-size: 14px;">模式相似性查找结果详情</span>

<!--      <el-button-->
<!--          type="success"-->
<!--          size="small"-->
<!--          style="margin-left: 20px; height: 30px;"-->
<!--          @click="autoCalibrateAndSave"-->
<!--      >-->
<!--        基于高分打分优化特征-->
<!--      </el-button>-->

      <div style="flex: 1;"></div> <!-- 空白占位 -->

      <el-button
          type="warning"
          size="small"
          style="margin-right: 20px;"
          :disabled="selectedTrainingSamples.length === 0"
          @click="triggerModelTraining"
      >
        基于勾选样本训练个性化模型 ({{ totalTrainingCount }}个)
      </el-button>
    </div>

    <!-- 1. 新增：漏斗监控面板 -->
    <div v-if="filterStats" style="margin: 15px 5px; padding: 20px; background: #fff; border: 1px solid #dcdfe6; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);">
      <h4 style="margin: 0 0 15px 0; color: #303133; font-size: 14px; display: flex; align-items: center;">
        <el-icon style="margin-right: 8px;"><DataAnalysis /></el-icon> 语义检索过滤过程监控
      </h4>
      <div style="display: flex; justify-content: space-around; align-items: center;">
        <div style="text-align: center;">
          <div style="font-size: 12px; color: #909399;">总历史片段</div>
          <div style="font-size: 22px; font-weight: bold; color: #606266;">{{ filterStats.total }}</div>
        </div>
        <el-icon><ArrowRight /></el-icon>
        <div style="text-align: center;">
          <div style="font-size: 12px; color: #909399;">AI 语义逻辑过滤</div>
          <div style="font-size: 22px; font-weight: bold; color: #67C23A;">{{ filterStats.after_llm_filter }}</div>
        </div>
        <el-icon><ArrowRight /></el-icon>
        <div style="text-align: center;">
          <div style="font-size: 12px; color: #909399;">数学形态相似</div>
          <div style="font-size: 22px; font-weight: bold; color: #E6A23C;">{{ filterStats.after_similarity_filter }}</div>
        </div>
      </div>
    </div>

    <div v-if="isChooseStock || isHistorySearchNew" style="padding-bottom: 50px;">
      <!-- 【修改1】增加 @selection-change 事件监听 -->
      <el-table :data="tableData2" border style="width: 99%; margin-left: 5px; margin-top: 5px; " stripe class="result-table"
        :cell-style="{ textAlign: 'center' }" :header-cell-style="{ textAlign: 'center' }" @selection-change="handleSelectionChange">
          <el-table-column fixed label="股票名称" prop="stockName" width="100px"></el-table-column>
          <el-table-column fixed label="股票代码" prop="stockCode" width="90px"></el-table-column>
<!--          <el-table-column label="股票来源" prop="stockFrom" width="100px"></el-table-column>-->
          <el-table-column label="起始时间" prop="startDate"  width="100px"></el-table-column>
          <el-table-column label="终止时间" prop="endDate"  width="100px"></el-table-column>

        <!-- 【核心修改 1】：左右双图对照区 -->
        <el-table-column label="形态对比 (基准骨架 vs 匹配结果)" width="580px" align="center">
          <template #default="{ row, $index }">
            <div style="display: flex; gap: 15px; justify-content: center; align-items: center; padding: 10px 0;">

              <!-- 左侧：基准骨架图 (读取 Vuex 中用户捏好的骨架) -->
              <div style="flex: 1; border: 1px dashed #dcdfe6; border-radius: 6px; padding: 5px; position: relative;">
                <span style="position: absolute; top: 5px; left: 10px; font-size: 11px; color: #909399; z-index: 10;">基准骨架</span>
                <div :ref="(el) => setTargetChartRef(el, $index)" style="width: 100%; height: 200px;"></div>
              </div>

              <!-- 右侧：匹配的历史 K 线图 -->
              <div style="flex: 1; border: 1px solid #ebeef5; border-radius: 6px; padding: 5px; position: relative; background: #fafafa;">
                <span style="position: absolute; top: 5px; left: 10px; font-size: 11px; color: #409EFF; z-index: 10;">匹配片段</span>
                <div :ref="(el) => setChartRef(el, $index, 0)" style="width: 100%; height: 200px;"></div>
              </div>

            </div>
          </template>
        </el-table-column>

        <!-- 【核心修改 2】：五星打分组件 + 文字描述 -->
        <el-table-column label="人工打分评判" width="240px" align="center">
          <template #default="scope">
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;">
              <el-rate
                  v-model="scope.row.userRating"
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  allow-half
              />
              <el-input
                  v-model="scope.row.description"
                  placeholder="主观描述（可选）"
                  size="small"
                  style="width: 200px; margin-top: 2px;"
              />
              <span style="font-size: 11px; color: #909399;">
                  算法评分: {{ (scope.row.similarity * 100).toFixed(1) }}
                </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="是否用于训练模型" align="center">
          <el-table-column type="selection" width="150" align="center"></el-table-column>
        </el-table-column>
      </el-table>

      <!-- ====== 自适应特征学件控制台 ====== -->
      <div v-if="featureState.length > 0" style="margin: 15px 5px; padding: 15px 20px; background: linear-gradient(135deg, #f5f7fa 0%, #fff 100%); border: 1px solid #dcdfe6; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.06);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-icon :size="18" color="#409EFF"><DataAnalysis /></el-icon>
            <span style="font-weight: bold; font-size: 14px; color: #303133;">自适应特征学件控制台</span>
          </div>
          <el-button
            type="warning"
            size="small"
            :loading="calibrating"
            :disabled="dataObjects3.filter(i => i.userRating > 0).length === 0"
            @click="batchCalibrate"
          >
            <el-icon style="margin-right: 4px;"><Aim /></el-icon>
            基于高分打分自动校准
          </el-button>
        </div>

        <!-- 可量化特征卡片 -->
        <div v-if="quantifiableFeatures.length > 0" style="margin-bottom: 12px;">
          <div style="font-size: 12px; color: #909399; margin-bottom: 8px;">▸ 可量化特征（打分动态校准）</div>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px;">
            <div v-for="feat in quantifiableFeatures" :key="feat.desc"
                 :class="{ 'feature-flash': feat.flash }"
                 style="padding: 10px 14px; border: 1px solid #e4e7ed; border-radius: 8px; background: #fff; transition: all 0.3s;">
              <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 6px;">{{ feat.shortLabel }}</div>
              <div style="font-size: 11px; color: #c0c4cc;">初始: {{ feat.initial.toFixed(1) }}{{ feat.unit }}</div>
              <div style="display: flex; align-items: baseline; gap: 4px; margin: 4px 0;">
                <span style="font-size: 18px; font-weight: bold;" :style="{ color: feat.direction > 0 ? '#67C23A' : feat.direction < 0 ? '#F56C6C' : '#303133' }">
                  {{ feat.center.toFixed(1) }}{{ feat.unit }}
                </span>
                <span v-if="feat.direction > 0" style="color: #67C23A; font-size: 14px;">↑</span>
                <span v-else-if="feat.direction < 0" style="color: #F56C6C; font-size: 14px;">↓</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px;">
                <el-progress :percentage="feat.rangePercent" :stroke-width="6" :show-text="false" style="flex: 1;" color="#409EFF" />
                <span style="font-size: 11px; color: #606266;">[{{ feat.min.toFixed(1) }}~{{ feat.max.toFixed(1) }}]{{ feat.unit }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 定性特征标签 -->
        <div v-if="qualitativeFeatures.length > 0">
          <div style="font-size: 12px; color: #909399; margin-bottom: 8px;">▸ 定性特征（参考标签）</div>
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            <el-tag v-for="feat in qualitativeFeatures" :key="feat.desc" size="small" effect="plain" style="font-size: 12px;">
              {{ feat.desc }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- ====== 生成式数据增强面板 ====== -->
      <div style="margin: 15px 5px; padding: 15px 20px; background: #fff; border: 1px solid #dcdfe6; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.08);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-icon :size="18" color="#9C27B0"><Cpu /></el-icon>
            <span style="font-weight: bold; font-size: 14px; color: #303133;">生成式数据增强</span>
            <el-tag v-if="currentGeneration > 1" type="success" size="small" style="margin-left: 4px;">第 {{ currentGeneration }} 代</el-tag>
          </div>
          <div style="display: flex; gap: 8px;">
            <el-button
              v-if="syntheticResults.length > 0 && syntheticResults.some(s => s.userRating > 0)"
              type="success"
              size="small"
              :loading="syntheticGenerating"
              @click="regenerateFromFeedback"
            >
              <el-icon style="margin-right: 4px;"><RefreshRight /></el-icon>
              基于反馈重新生成 (第 {{ currentGeneration + 1 }} 代)
            </el-button>
            <el-button
              type="primary"
              size="small"
              :loading="syntheticGenerating"
              :disabled="selectedTrainingSamples.length === 0"
              @click="generateAISamples"
            >
              <el-icon style="margin-right: 4px;"><MagicStick /></el-icon>
              {{ syntheticGenerating ? 'AI 仿真生成中...' : generateButtonText }}
            </el-button>
          </div>
        </div>

        <!-- 历史代际（归档样本，可勾选用于训练） -->
        <el-collapse v-if="generationHistory.length > 0" style="margin-bottom: 10px;">
          <el-collapse-item v-for="gen in generationHistory" :key="gen.gen" :name="gen.gen">
            <template #title>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span>第 {{ gen.gen }} 代 ({{ gen.samples.length }} 个样本)</span>
                <el-tag size="small" type="info">归档</el-tag>
                <span style="font-size: 11px; color: #909399;">
                  已勾选 {{ gen.samples.filter(s => s.selected).length }} / 评分: {{ gen.samples.filter(s => s.userRating > 0).map(s => s.userRating + '★').join(' ') || '无' }}
                </span>
              </div>
            </template>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; padding: 10px 0;">
              <div v-for="(synth, sIdx) in gen.samples" :key="gen.gen + '_' + synth.sample_id"
                   style="display: inline-flex; flex-direction: column; align-items: center; width: 180px; border: 1px solid #dcdfe6; border-radius: 6px; padding: 8px; background: #f9f9f9; position: relative;">
                <el-tag type="info" size="small" effect="plain" style="position: absolute; top: 4px; right: 4px; font-size: 9px;">Gen{{ gen.gen }}</el-tag>
                <el-checkbox v-model="synth.selected" style="margin-bottom: 4px; align-self: flex-start;">
                  <span style="font-size: 11px; color: #606266;">{{ synth.sample_id }}</span>
                </el-checkbox>
                <div :ref="(el) => setArchivedChartRef(el, gen.gen, sIdx)" style="width: 160px; height: 100px; border: 1px solid #ebeef5; border-radius: 4px; background: #fff;"></div>
                <div style="margin-top: 4px; display: flex; align-items: center; gap: 4px;">
                  <el-rate v-model="synth.userRating" :max="5" size="small" disabled />
                  <span v-if="synth.userRating > 0" style="font-size: 11px; color: #F7BA2A;">{{ synth.userRating }}★</span>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- 横向滚动卡片栏 -->
        <div v-if="syntheticResults.length > 0" style="overflow-x: auto; white-space: nowrap; padding: 10px 0;">
          <div style="display: inline-flex; gap: 16px;">
            <div v-for="(synth, sIdx) in syntheticResults" :key="synth.sample_id"
                 style="display: inline-flex; flex-direction: column; align-items: center; width: 220px; border: 1px solid #e4e7ed; border-radius: 8px; padding: 10px; background: #fafafa; position: relative; vertical-align: top;">
              <!-- 右上角标签 -->
              <el-tag type="warning" size="small" effect="dark" style="position: absolute; top: 6px; right: 6px; font-size: 10px;">Gen{{ synth.generation || 1 }}</el-tag>
              <!-- 复选框 -->
              <el-checkbox v-model="synth.selected" style="margin-bottom: 6px; align-self: flex-start;">
                <span style="font-size: 12px; color: #606266;">{{ synth.sample_id }}</span>
              </el-checkbox>
              <!-- 迷你 ECharts -->
              <div :ref="(el) => setSynthChartRef(el, sIdx)" style="width: 200px; height: 150px; border: 1px solid #ebeef5; border-radius: 4px; background: #fff;"></div>
              <!-- 评分 + 反馈 -->
              <div style="width: 100%; margin-top: 6px; display: flex; flex-direction: column; gap: 4px;">
                <el-rate v-model="synth.userRating" :max="5" size="small" style="justify-content: center;" />
                <el-input v-model="synth.feedback" placeholder="反馈..." size="small" style="width: 100%;" />
              </div>
            </div>
          </div>
        </div>
        <div v-else style="color: #c0c4cc; font-size: 12px; text-align: center; padding: 10px 0;">
          请先在上方表格中勾选 1-3 个真实匹配片段作为种子，再点击生成按钮
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ElMessage, ElMessageBox} from 'element-plus';
import { DataAnalysis, ArrowRight, Cpu, MagicStick, Aim, RefreshRight } from '@element-plus/icons-vue';
import { ref, onMounted, nextTick, watch, toRaw, computed  } from 'vue';
import { useStore } from "vuex";
import axios from "axios";
import * as echarts from 'echarts';

const store = useStore();

// 生成按钮文案：按当前分析模式动态显示
const generateButtonText = computed(() => {
  const mode = (store.state.newSearchInfo.analysisMode || 'MA').toUpperCase();
  return mode === 'KLINE' ? 'AI 仿真生成 K线样本' : 'AI 仿真生成 均线样本';
});

const isHistorySearch = computed(() => {
  return store.state.baseInfo.isHistorySearch === true;
});
const isChooseStock = computed(() => {
  return store.state.baseInfo.isChooseStock === true;
});
const isHistorySearchNew = computed(() => {
  return store.state.baseInfo.isHistorySearchNew === true;
});
const graphCode = ref('000021');
const filterStats = ref(null);
watch(() => store.state.resultInfo, (newVal) => {
  if (newVal && newVal.filter_stats) {
    filterStats.value = newVal.filter_stats;
    console.log("漏斗数据成功更新:", filterStats.value);
  }
}, { deep: true, immediate: true });
watch(() => store.state.resultStockInfo.code,(newValue) => {
  console.log("----------------------------------");
  console.log(store.state.resultStockInfo.startDate);
  console.log(store.state.resultStockInfo.endDate);
  console.log("----------------------------------");
  graphCode.value = newValue;
  }
);
// -------------------------
function getDateRange(dateStr) {
    const date = new Date(`${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6)}`);
    const range = [];
    for (let i = -2; i <= 2; i++) {
        const newDate = new Date(date);
        newDate.setDate(newDate.getDate() + i);
        const year = newDate.getFullYear();
        const month = String(newDate.getMonth() + 1).padStart(2, '0');
        const day = String(newDate.getDate()).padStart(2, '0');
        range.push(`${year}${month}${day}`);
    }
    return range;
}

// 确定按钮类型（颜色）
// 确定按钮文本
// -------------------------------------------------------------------
const dataObjects = ref([
  {
    stockIndex: 1,
    stockName: '博菲电器',
    stockCode: '001255',
    stockFrom: '基准股票',
    startDate: '2024-09-20',
    endDate: '2024-11-20',
    chartData: [
      [6.507500, 6.707500, 6.910000, 7.110000, 7.155000, 7.217500, 7.442500, 7.732500, 7.807500, 7.842500, 7.652500, 7.460000, 7.472500, 7.492500, 7.605000, 7.650000, 7.777500, 7.852500, 7.960000, 8.027500, 8.217500, 8.667500, 9.102500, 9.662500, 10.185000, 10.215000, 10.147500, 10.040000, 9.835000, 9.857500, 9.972500, 10.072500, 10.002500, 10.030000, 9.932500, 9.692500, 9.497500, 9.267500, 9.207500],
      [6.426250, 6.552500, 6.635000, 6.740000, 6.831250, 6.962500, 7.176250, 7.421250, 7.481250, 7.530000, 7.547500, 7.596250, 7.640000, 7.667500, 7.628750, 7.555000, 7.625000, 7.672500, 7.782500, 7.838750, 7.997500, 8.260000, 8.531250, 8.845000, 9.201250, 9.441250, 9.625000, 9.851250, 10.010000, 10.036250, 10.060000, 10.056250, 9.918750, 9.943750, 9.952500, 9.882500, 9.750000, 9.648750, 9.570000],
      [6.347500, 6.425833, 6.500000, 6.575833, 6.669167, 6.774167, 6.904167, 7.070833, 7.156667, 7.255833, 7.335000, 7.434167, 7.478333, 7.517500, 7.566667, 7.614167, 7.685833, 7.729167, 7.739167, 7.712500, 7.822500, 8.004167, 8.222500, 8.446667, 8.726667, 8.911667, 9.070000, 9.243333, 9.412500, 9.580000, 9.740833, 9.925000, 10.007500, 10.034167, 10.017500, 9.935000, 9.778333, 9.718333, 9.704167],
      [6.301250, 6.367500, 6.421875, 6.480000, 6.549375, 6.623750, 6.735625, 6.865000, 6.953750, 7.041250, 7.091250, 7.168125, 7.235625, 7.315000, 7.402500, 7.488125, 7.553125, 7.601250, 7.665000, 7.717500, 7.818750, 7.963750, 8.080000, 8.200000, 8.413125, 8.556875, 8.703750, 8.845000, 9.003750, 9.148125, 9.295625, 9.450625, 9.560000, 9.692500, 9.788750, 9.866875, 9.880000, 9.842500, 9.815000],
      [6.387500, 6.409500, 6.410000, 6.429000, 6.472000, 6.537500, 6.626000, 6.730500, 6.801000, 6.867500, 6.919000, 6.984000, 7.057500, 7.131500, 7.194000, 7.264500, 7.344000, 7.422500, 7.514000, 7.596000, 7.686000, 7.814500, 7.952500, 8.106500, 8.292000, 8.414000, 8.493500, 8.568000, 8.697500, 8.817000, 8.957500, 9.090500, 9.203500, 9.324500, 9.423000, 9.499000, 9.547500, 9.607500, 9.672500], 
      [6.310851, 6.337872, 6.362128, 6.391702, 6.421489, 6.452979, 6.493404, 6.545319, 6.581489, 6.615532, 6.635957, 6.663191, 6.687447, 6.707872, 6.726809, 6.750426, 6.785745, 6.813830, 6.841489, 6.874468, 6.925745, 6.997660, 7.070851, 7.154894, 7.252553, 7.328511, 7.398511, 7.477447, 7.549787, 7.611277, 7.678936, 7.761702, 7.841277, 7.923404, 7.994468, 8.062128, 8.122553, 8.185532, 8.251064],
    ],
    chartData2: [],
    // 2024-09-20 到 2024-11-20 的每个股票交易日
    dates: [ '20240920', '20240921', '20240922', '20240923', '20240924', '20240925', '20240926', '20240927', '20240928', '20240929',
      '20240930', '20241001', '20241002', '20241003', '20241004', '20241005', '20241006', '20241007', '20241008', '20241009',
      '20241030', '20241031', '20241101', '20241102', '20241101', '20241102',
      '20241109', '20241110', '20241111', '20241112', '20241113', '20241114', '20241115', '20241116', '20241117', '20241118',
      '20241119', '20241120'
    ],
    dates2: getDateRange('20241120'),
    chartData3: [],
    similarity: 0.9232
  },
  {
    stockIndex: 2,
    stockName: '博菲电器',
    stockCode: '001255',
    stockFrom: '基准股票',
    startDate: '2023-02-02',
    endDate: '2023-03-20',
    chartData: [
      [10.602500, 10.647500, 10.687500, 10.675000, 10.672500, 10.707500, 10.727500, 10.815000, 10.887500, 10.992500, 11.025000, 10.950000, 10.937500, 10.867500, 10.892500, 10.927500, 10.985000, 10.980000, 10.985000, 11.067500, 11.172500, 11.342500, 11.552500, 11.577500, 11.705000, 11.752500, 11.662500, 11.752500, 11.667500, 11.575000, 11.437500, 11.327500, 11.185000], 
  [10.343750, 10.435000, 10.513750, 10.585000, 10.637500, 10.677500, 10.707500, 10.745000, 10.780000, 10.850000, 10.876250, 10.882500, 10.912500, 10.930000, 10.958750, 10.938750, 10.961250, 10.923750, 10.938750, 10.997500, 11.078750, 11.161250, 11.268750, 11.322500, 11.438750, 11.547500, 11.607500, 11.665000, 11.686250, 11.663750, 11.550000, 11.540000, 11.426250],
  [10.114167, 10.207500, 10.305833, 10.393333, 10.453333, 10.525833, 10.585000, 10.661667, 10.720833, 10.782500, 10.813333, 10.813333, 10.832500, 10.855833, 10.881667, 10.897500, 10.936667, 10.946667, 10.967500, 10.981667, 11.031667, 11.063333, 11.143333, 11.190833, 11.287500, 11.358333, 11.400000, 11.465833, 11.515000, 11.556667, 11.550833, 11.552500, 11.519167], 
  [10.016875, 10.075000, 10.136250, 10.194375, 10.253750, 10.332500, 10.411250, 10.498750, 10.561875, 10.642500, 10.695000, 10.733750, 10.775000, 10.803750, 10.833125, 10.841875, 10.870625, 10.886875, 10.907500, 10.940000, 10.995625, 11.045625, 11.113750, 11.130625, 11.200000, 11.235625, 11.273125, 11.331250, 11.382500, 11.412500, 11.409375, 11.431250, 11.432500],  
  [9.919500, 9.986500, 10.054500, 10.104500, 10.148000, 10.201500, 10.254500, 10.318500, 10.380500, 10.464500, 10.534000, 10.589000, 10.637000, 10.687500, 10.734500, 10.772500, 10.817000, 10.839000, 10.863500, 10.887000, 10.931000, 10.978000, 11.036500, 11.067500, 11.137500, 11.187000, 11.223500, 11.255000, 11.293500, 11.303500, 11.306000, 11.330500, 11.343000], 
  [10.035106, 10.035532, 10.041064, 10.047872, 10.054894, 10.068298, 10.079362, 10.095319, 10.105319, 10.123830, 10.131064, 10.134255, 10.140638, 10.152979, 10.168936, 10.180426, 10.199574, 10.217872, 10.238298, 10.265745, 10.303404, 10.343191, 10.391277, 10.429149, 10.482340, 10.527872, 10.567872, 10.614043, 10.663404, 10.706596, 10.734468, 10.767021, 10.795532],  

    ],
    chartData2: [],
    dates: [ '20230202', '20230203', '20230204', '20230205', '20230206', '20230207', '20230208', '20230209', '20230210', '20230211',
      '20230212', '20230213', '20230214', '20230215', '20230216', '20230217', '20230218', '20230219', '20230220', '20230221',
      '20230302', '20230303', '20230304', '20230305', '20230306', '20230307',
      '20230314', '20230315', '20230316', '20230317', '20230318', '20230319',
      '20230320'
    ],
    dates2: getDateRange('20250102'),
    chartData3: [],
    similarity: 0.8997
  },
  {
    stockIndex: 3,
    stockName: '博菲电器',
    stockCode: '001255',
    stockFrom: '基准股票',
    startDate: '2024-09-24',
    endDate: '2024-11-19',
    chartData: [
      [13.040000, 13.265000, 13.592500, 14.035000, 14.562500, 15.297500, 15.770000, 16.152500, 16.170000, 16.010000, 16.095000, 16.052500, 16.127500, 16.170000, 16.342500, 16.647500, 17.150000, 17.675000, 18.290000, 18.987500, 19.280000, 19.350000, 19.475000, 19.332500, 19.895000, 20.690000, 20.950000, 21.870000, 22.002500, 22.130000, 22.182500, 21.685000, 21.285000, 20.512500, 20.052500, 19.760000], 
  [12.965000, 13.055000, 13.192500, 13.426250, 13.801250, 14.281250, 14.681250, 15.093750, 15.366250, 15.653750, 15.932500, 16.102500, 16.148750, 16.090000, 16.218750, 16.350000, 16.638750, 16.922500, 17.316250, 17.817500, 18.215000, 18.512500, 18.882500, 19.160000, 19.587500, 20.020000, 20.212500, 20.601250, 20.948750, 21.410000, 21.566250, 21.777500, 21.643750, 21.321250, 21.117500, 20.722500],  
  [13.050000, 13.075833, 13.156667, 13.292500, 13.497500, 13.802500, 14.051667, 14.335000, 14.590833, 14.857500, 15.152500, 15.413333, 15.620000, 15.825833, 16.069167, 16.284167, 16.482500, 16.618333, 16.909167, 17.229167, 17.519167, 17.731667, 18.035833, 18.322500, 18.775000, 19.238333, 19.571667, 20.063333, 20.392500, 20.723333, 20.869167, 20.962500, 21.060833, 21.110833, 21.061667, 21.105000],  
  [13.140625, 13.163125, 13.221875, 13.295625, 13.428125, 13.631250, 13.810000, 14.007500, 14.165625, 14.354375, 14.562500, 14.764375, 14.975000, 15.185625, 15.450000, 15.721875, 16.002500, 16.288125, 16.624375, 16.960000, 17.181875, 17.301250, 17.550625, 17.755000, 18.113125, 18.471250, 18.764375, 19.209375, 19.581875, 19.961250, 20.224375, 20.468750, 20.615625, 20.670625, 20.665000, 20.661875], 
  [13.165500, 13.195500, 13.229000, 13.311000, 13.425000, 13.590000, 13.731500, 13.867000, 13.976500, 14.107000, 14.267000, 14.416500, 14.558000, 14.717500, 14.918500, 15.141000, 15.410000, 15.683500, 16.018000, 16.375000, 16.658000, 16.900500, 17.194500, 17.434500, 17.724500, 17.979000, 18.230500, 18.578000, 18.891000, 19.203000, 19.448000, 19.704500, 19.922500, 20.071500, 20.190000, 20.327000], 
  [13.386809, 13.380851, 13.384043, 13.393191, 13.428298, 13.497234, 13.552340, 13.609149, 13.648936, 13.704681, 13.762553, 13.802128, 13.842766, 13.897234, 13.975532, 14.054043, 14.147234, 14.251702, 14.380851, 14.522340, 14.642979, 14.756596, 14.898723, 15.030638, 15.205532, 15.396596, 15.571277, 15.789787, 15.974468, 16.164894, 16.340000, 16.506383, 16.651915, 16.782340, 16.908511, 17.046596],  
    ],
    chartData2: [],
    dates: [
      '20240924', '20240925', '20240926', '20240927', '20240928', '20240929',
      '20240930', '20241001', '20241002', '20241003', '20241004', '20241005',
      '20241006', '20241007', '20241008', '20241009', '20241010', '20241011',
      '20241101', '20241102', '20241103', '20241104', '20241105', '20241106',
      '20241101', '20241102', '20241103', '20241104', '20241105', '20241106',
      '20241113', '20241114', '20241115', '20241116', '20241117', '20241118',
      '20241119'
    ],
    dates2: getDateRange('20250102'),
    chartData3: [],
    similarity: 0.8740
  },
  {
    stockIndex: 4,
    stockName: '博菲电器',
    stockCode: '001255',
    stockFrom: '基准股票',
    startDate: '2022-06-23',
    endDate: '2022-08-08',
    chartData: [
      [9.687500, 9.625000, 9.750000, 10.050000, 10.272500, 10.707500, 10.967500, 11.132500, 11.335000, 11.182500, 11.085000, 10.932500, 10.680000, 10.512500, 10.630000, 10.902500, 11.342500, 11.900000, 12.282500, 12.750000, 13.247500, 13.515000, 13.632500, 13.600000, 13.700000, 13.835000, 14.010000, 14.110000, 13.722500, 13.320000, 12.950000, 12.590000, 12.500000], 
  [9.676250, 9.681250, 9.786250, 9.915000, 9.980000, 10.166250, 10.358750, 10.591250, 10.803750, 10.945000, 11.026250, 11.032500, 11.007500, 10.847500, 10.857500, 10.917500, 11.011250, 11.206250, 11.456250, 11.826250, 12.295000, 12.707500, 12.957500, 13.175000, 13.473750, 13.675000, 13.821250, 13.855000, 13.711250, 13.577500, 13.480000, 13.350000, 13.111250], 
  [9.633333, 9.666667, 9.725000, 9.807500, 9.875000, 10.023333, 10.180000, 10.320833, 10.431667, 10.505000, 10.600833, 10.705000, 10.762500, 10.800833, 10.894167, 10.989167, 11.119167, 11.198333, 11.332500, 11.528333, 11.756667, 11.975833, 12.181667, 12.417500, 12.763333, 13.083333, 13.308333, 13.486667, 13.556667, 13.556667, 13.530833, 13.433333, 13.307500], 
  [9.523750, 9.593125, 9.680000, 9.738125, 9.793125, 9.926875, 10.035625, 10.138750, 10.240000, 10.313125, 10.406250, 10.473750, 10.493750, 10.506875, 10.608125, 10.754375, 10.907500, 11.075625, 11.241250, 11.429375, 11.651250, 11.777500, 11.907500, 12.046250, 12.242500, 12.440625, 12.638750, 12.840625, 13.003125, 13.142500, 13.218750, 13.262500, 13.292500], 
  [9.320500, 9.389500, 9.480500, 9.579000, 9.673500, 9.816000, 9.937500, 10.017000, 10.101500, 10.178000, 10.245500, 10.297500, 10.328000, 10.353000, 10.451000, 10.559500, 10.663500, 10.785500, 10.943000, 11.153500, 11.375500, 11.563500, 11.719500, 11.863500, 12.061000, 12.189000, 12.328000, 12.459000, 12.538500, 12.616500, 12.701000, 12.790500, 12.902500],  
  [8.573404, 8.598723, 8.630426, 8.673191, 8.709149, 8.767660, 8.831915, 8.897447, 8.981489, 9.063830, 9.133404, 9.202979, 9.259787, 9.312979, 9.392766, 9.478723, 9.569574, 9.669574, 9.776383, 9.900000, 10.035319, 10.159149, 10.271915, 10.382553, 10.510000, 10.628298, 10.749362, 10.866170, 10.961277, 11.049362, 11.132128, 11.213617, 11.295319], 
    ],
    chartData2: [],
    dates: [
      '20220623', '20220624', '20220625', '20220626', '20220627', '20220628',
      '20220629', '20220630', '20220701', '20220702', '20220703', '20220704',
      '20220705', '20220706', '20220707', '20220708', '20220709', '20220710',
      '20220705', '20220706', '20220707', '20220708', '20220709', '20220710',
      '20220801', '20220802', '20220803', '20220804', '20220805', '20220806',
      '20220807', '20220808'
    ],
    dates2: getDateRange('20250102'),
    chartData3: [],
    similarity: 0.7521
  }
]);
const dataObjects2 = ref([
  {
    searchType: '历史查找',
    searchCount: 0,
    futureTime: '5',
    showCustomInput: false,
    customDays: '',
    futureIncome: 0,
    maxRange: 0,
    maxRate: 0,
    stockIncrease: 0,
    stockDecrease: 0,
    score: 0,
    riseFallRatio: [65, 35] // 上涨65%，下跌35%
  }
]);
const dataObjects3 = ref([]);

const curImg = ref();
const imageList = ref([]);
const loading = ref(true);
const fetchImages = async () => {
  const timestamp = new Date().getTime();
  const API_BASE_URL = 'http://127.0.0.1:5000';
  const folderName = store.state.newSearchInfo.baseFolder;
  try {
    loading.value = true;
    const params = new URLSearchParams();
    params.append('timestamp', timestamp);
    params.append('folder', folderName);
    // const response = await axios.get(`${API_BASE_URL}/get_all_screenshots?timestamp=${timestamp}`);
    const response = await axios.get(`${API_BASE_URL}/get_all_screenshots`,{params});
    if (response.data.success) {
      // 处理图片列表，修正URL并编码特殊字符
      imageList.value = response.data.images.map(image => ({
        ...image,
        url: `${API_BASE_URL}/get_screenshot/${encodeURIComponent(image.filename)}`
      }));
    }
  } catch (err) {
    console.error('获取图片失败:', err);
    // 更详细的错误信息输出
    if (err.response) {
      console.error('错误状态码:', err.response.status);
      console.error('错误内容:', err.response.data);
    }
  } finally {
    loading.value = false;
  }
  curImg.value = imageList.value.length > 0 ? imageList.value[0].url : '';
};


watch(() => store.state.resultInfo.filter_stats, (val) => {
  console.log("漏斗数据已收到:", val);
}, { immediate: true });

// 监听vuex中的sim_stock_list,更新dataObjects3的数据
watch(() => store.state.sim_stock_list, async(newList) => {
  console.log("------- ResultShow 监听到新结果，开始准备表格数据 -------", newList?.length);
  await fetchImages();

  if (newList && newList.length > 0) {
    // 将数据映射到 dataObjects3，这是 tableData2 的来源
    dataObjects3.value = newList.map(item => {
      // --- 【新增：从全局列表中查找真实名称】 ---
      // store.state.stockList 包含了所有股票的 code 和 name
      const actualStock = store.state.stockList.find(s => s.code === item.stock_code);
      const displayName = actualStock ? actualStock.name : item.stock_name;
      // 从我们刚才备份的 recent_data_raw 中提取起始/结束日期
      const sDate = item.recent_data_raw && item.recent_data_raw.length > 0
          ? (item.recent_data_raw[0].trade_date || item.recent_data_raw[0].timestamps)
          : '未知';
      const eDate = item.recent_data_raw && item.recent_data_raw.length > 0
          ? (item.recent_data_raw[item.recent_data_raw.length - 1].trade_date || item.recent_data_raw[item.recent_data_raw.length - 1].timestamps)
          : '未知';

      return {
        stockCode: item.stock_code,
        stockName: displayName,
        stockFrom: '系统匹配',
        startDate: sDate,
        endDate: eDate,
        chartData: item.recent_data || [], // 这是转置后的二维数组
        recent_data_raw: item.recent_data_raw,
        similarity: item.similarity,
        userRating: 0, // 【新增】：初始化用户的星级打分为 0
        dates: [],
        dates2: [],
        chartData3: [],
        imagePath: curImg.value
      };
    });

    console.log("dataObjects3 赋值成功，当前长度:", dataObjects3.value.length);
    // 如果后端把 filter_stats 存到了 Vuex 的 resultInfo 里
    filterStats.value = store.state.resultInfo?.filter_stats || null;
    nextTick(() => {
      // 触发图表渲染
      dataObjects3.value.forEach((item, rowIndex) => {
        initChart3(rowIndex * 3, rowIndex, 0);
      });
    });
  } else {
    dataObjects3.value = [];
  }
}, { deep: true, immediate: true }); // 【核心修改 3】：增加 immediate: true

function transposeArray(array) {
    // 检查输入是否为有效的二维数组
    if (!Array.isArray(array) || array.length === 0 || !Array.isArray(array[0])) {
        throw new Error('输入必须是一个非空的二维数组');
    }
    // 获取原数组的行数和列数
    const rows = array.length;
    const cols = array[0].length;
    // 创建一个新的二维数组，行数为原数组的列数，列数为原数组的行数
    const transposed = new Array(cols).fill(0).map(() => new Array(rows).fill(0));
    // 填充转置后的数组
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            transposed[j][i] = array[i][j];
        }
    }
    return transposed;
}

// 创建计算属性而不是直接引用
const tableData = computed(() => dataObjects.value);
const tableData2 = computed(() => dataObjects3.value);
const resultData = computed(() => dataObjects2.value);

// 传入的是股票基准模式的数据
watch(() => store.state.resultList2, (newValue) => {
    console.log("接收结果数据-------------------", toRaw(newValue));
    const rawData = toRaw(newValue);
    const newDataObjects = [];
    let totalSearchCount = 0;

    for (const stockCode in rawData) {
      if (rawData.hasOwnProperty(stockCode)) {
        console.log("股票代码:", stockCode);
        // 获取该股票的所有相似区间数据
        const intervals = rawData[stockCode];
        totalSearchCount += intervals.length;

        // 遍历每个相似区间
        intervals.forEach((interval) => {
          const stock = store.state.stockList.find(stock => stock.code === stockCode.slice(0, 6));
          const ma_values1 = transposeArray(interval.ma_values);
          const index_values = transposeArray(interval.index_ma_values);
          const dates = interval.x_axis_dates;
          const digits = dates.map(date => date.slice(-4));
          const future_value = transposeArray(interval.post_ma_values.slice(0, 10));

          const newData = {
            stockName: stock ? stock.name : '未知股票',
            stockCode: stockCode.slice(0, 6),
            stockFrom: '基准股票',
            startDate: interval.start_date,
            endDate: interval.end_date,
            chartData: ma_values1,
            chartData2: index_values,
            dates: digits,
            dates2: interval.post_dates.slice(0, 10),
            chartData3: future_value,
            similarity: interval.similarity.toFixed(6)
          };
          newDataObjects.push(newData);
        });
      }
    }

    const newResultData = [{
      searchType: '基准股票模式查找',
      searchCount: totalSearchCount,
      futureTime: '5',
      showCustomInput: false,
      customDays: '',
      futureIncome: store.state.resultInfo.futureIncome * 100,
      maxRange: 0,
      maxRate: 0,
      stockIncrease: 0,
      stockDecrease: 0,
      score: 0,
      riseFallRatio: [65, 35]
    }];

    // 直接更新数据对象
    dataObjects.value = newDataObjects;
    dataObjects2.value = newResultData;
    console.log('表格数据已更新');
  },
  { deep: true } // 若 resultList 是对象或数组，需要深度监听
);

// 传入的是推荐模式【金叉】的结果数据
watch(() => store.state.resultList, (newValue) => {
    console.log("接收结果数据-------------------", toRaw(newValue));
    const rawData = toRaw(newValue);
    const newDataObjects = [];
    let totalSearchCount = 0;

    for (const stockCode in rawData) {
      if (rawData.hasOwnProperty(stockCode)) {
        console.log("股票代码:", stockCode);
        // 获取该股票的所有相似区间数据
        const intervals = rawData[stockCode];
        totalSearchCount += intervals.length;

        // 遍历每个相似区间
        intervals.forEach((interval) => {
          const stock = store.state.stockList.find(stock => stock.code === stockCode.slice(0, 6));
          const ma_values1 = transposeArray(interval.ma_data.map(subArray => subArray.slice(1)));
          const index_values = transposeArray(interval.index_ma_values);
          const dates = interval.ma_data.map(item => item[0]);
          const digits = dates.map(date => date.slice(-4));
          const future_value = transposeArray(interval.post_stock_ma_data.slice(0, 10).map(subArray => subArray.slice(1)));

          const newData = {
            stockName: stock ? stock.name : '未知股票',
            stockCode: stockCode.slice(0, 6),
            stockFrom: '基准股票',
            startDate: interval.interval[0],
            endDate: interval.interval[1],
            chartData: ma_values1,
            chartData2: index_values,
            dates: digits,
            dates2: interval.post_stock_dates.slice(0, 10),
            chartData3: future_value,
            similarity: 1
          };
          newDataObjects.push(newData);
        });
      }
    }

    const newResultData = [{
      searchType: '基准股票模式查找',
      searchCount: totalSearchCount,
      futureTime: '5',
      showCustomInput: false,
      customDays: '',
      futureIncome: store.state.resultInfo.futureIncome * 100,
      maxRange: 0,
      maxRate: 0,
      stockIncrease: 0,
      stockDecrease: 0,
      score: 0,
      riseFallRatio: [65, 35]
    }];

    // 直接更新数据对象
    dataObjects.value = newDataObjects;
    dataObjects2.value = newResultData;
    console.log('表格数据已更新');
  },
  { deep: true } // 若 resultList 是对象或数组，需要深度监听
);

// 页面加载时检查是否已有数据
onMounted(() => {
  if (store.state.resultList && Object.keys(store.state.resultList).length > 0) {
    const rawData = toRaw(store.state.resultList);
    const newDataObjects = [];
    let totalSearchCount = 0;

    for (const stockCode in rawData) {
      if (rawData.hasOwnProperty(stockCode)) {
        const intervals = rawData[stockCode];
        totalSearchCount += intervals.length;

        intervals.forEach((interval) => {
          const stock = store.state.stockList.find(stock => stock.code === stockCode.slice(0, 6));
          const ma_values1 = transposeArray(interval.ma_data);
          const index_values = transposeArray(interval.index_ma_values);
          const dates = interval.ma_data.map(item => item[0]);
          const digits = dates.map(date => date.slice(-4));
          const future_value = transposeArray(interval.post_stock_ma_data.slice(0, 10));

          const newData = {
            stockName: stock ? stock.name : '未知股票',
            stockCode: stockCode.slice(0, 6),
            stockFrom: '基准股票',
            startDate: interval.interval[0],
            endDate: interval.interval[1],
            chartData: ma_values1,
            chartData2: index_values,
            dates: digits,
            dates2: interval.post_stock_dates.slice(0, 10),
            chartData3: future_value,
            similarity: 1
          };
          newDataObjects.push(newData);
        });
      }
    }

    const newResultData = [{
      searchType: '基准股票模式查找',
      searchCount: totalSearchCount,
      futureTime: '5',
      showCustomInput: false,
      customDays: '',
      futureIncome: store.state.resultInfo.futureIncome * 100,
      maxRange: 0,
      maxRate: 0,
      stockIncrease: 0,
      stockDecrease: 0,
      score: 0,
      riseFallRatio: [65, 35]
    }];

    // 直接更新数据对象
    dataObjects.value = newDataObjects;
    dataObjects2.value = newResultData;
    console.log('表格数据已更新');
    
    // 强制更新表格
    nextTick(() => {
      console.log('表格数据长度:', tableData.value.length);
    });
  }
});

const chartRefs = ref(Array(dataObjects.value.length * 3).fill(null));

const setChartRef = (el, rowIndex, colIndex) => {
  const index = rowIndex * 3 + colIndex;

  if (el) {
    chartRefs.value[index] = el;

    // 【核心修复：使用 nextTick】确保 div 的 width 和 height 已经生效后再初始化 Echarts
    nextTick(() => {
      if(isHistorySearch.value === true) {
        initChart(index, rowIndex, colIndex);
      }
      if(isChooseStock.value === true || isHistorySearchNew.value === true) {
        initChart3(index, rowIndex, colIndex);
      }
    });
  }
};

const initChart = (index, rowIndex, colIndex, retryCount = 0) => {
  if (chartRefs.value[index]) {
    try {
      const myChart = echarts.init(chartRefs.value[index]);
      let chartData;
      if (colIndex === 0) {
        chartData = dataObjects.value[rowIndex].chartData;
      } else if (colIndex === 1) {
        chartData = dataObjects.value[rowIndex].chartData2;
      }
      // 计算所有数据中的最小值和最大值
      const allValues = [].concat(...chartData);
      const minValue = Math.min(...allValues);
      const maxValue = Math.max(...allValues);
      // 添加一些边距，使图表更美观
      const padding = (maxValue - minValue) * 0.1;
      
      const option = {
        xAxis: {
          type: 'category',
          data: dataObjects.value[rowIndex].dates,
        },
        yAxis: {
          type: 'value',
          axisTick: { show: false }, // 隐藏 y 轴刻度
          axisLabel: { show: false }, // 隐藏 y 轴坐标值
          min: minValue - padding,    // 设置纵轴最小值
          max: maxValue + padding     // 设置纵轴最大值
        },
        series: [
          {
            name: 'MA4',
            data: chartData[0],
            type: 'line',
            lineStyle: { width: 1, color:'#cd1f0e' },// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA8',
            data: chartData[1],
            type: 'line',
            lineStyle: { width: 1 , color:'#edbf09'},// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA12',
            data: chartData[2],
            type: 'line',
            lineStyle: { width: 1 ,color:'#62c613'},// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA16',
            data: chartData[3],
            type: 'line',
            lineStyle: { width: 1, color:'#1286ff' },// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA20',
            data: chartData[4],
            type: 'line',
            lineStyle: { width: 1 ,color:'#9f12ff'},// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA47',
            data: chartData[5],
            type: 'line',
            lineStyle: { width: 1,color:'#000000' },// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
        ]
      };
      myChart.setOption(option);
    } catch (error) {
      console.error('ECharts 初始化出错:', error);
    }
  } else if (retryCount < 5) {
    setTimeout(() => {
      initChart(index, rowIndex, colIndex, retryCount + 1);
    }, 500);
  } else {
    console.log(`chartRef 未获取到元素: ${index}，重试次数达到上限`);
  }
};

const initChart3 = (index, rowIndex, colIndex, retryCount = 0) => {
  if (chartRefs.value[index]) {
    try {
      const dom = chartRefs.value[index];

      // 【修复1】：安全清理已存在的 Echarts 实例，防止重复渲染报警
      let myChart = echarts.getInstanceByDom(dom);
      if (myChart) {
        myChart.dispose();
      }
      myChart = echarts.init(dom);

      // 【修复2】：兼容不同后端接口的数据格式 (recent_data_raw 或 recent_data)
      const rowData = dataObjects3.value[rowIndex];
      const rawData = rowData?.recent_data_raw || rowData?.recent_data;

      if (!rawData || !Array.isArray(rawData) || rawData.length === 0) {
        console.warn(`第 ${rowIndex} 行数据无效，跳过渲染`);
        return;
      }

      // 提取日期 (兼容 trade_date 和 timestamps 字段)
      const dates = rawData.map(item => item.trade_date || item.timestamps || '');

      // 从 Vuex 获取当前的分析模式，默认为 'MA'
      const mode = store.state.newSearchInfo.analysisMode || 'MA';

      const series = [];
      const allValues =[];

      // ==========================================
      // 根据不同模式，动态组装 series
      // ==========================================
      if (mode === 'KLINE') {
        const upColor = '#ec0000';
        const downColor = '#00da3c';

        // 组装 K 线数据[open, close, lowest, highest]
        // 增加容错：如果后端没传开高低收，默认用0代替，防止页面崩溃
        const klineData = rawData.map(item =>[
          item.open !== undefined ? item.open : (item.close || 0),
          item.close || 0,
          item.low !== undefined ? item.low : (item.close || 0),
          item.high !== undefined ? item.high : (item.close || 0)
        ]);

        series.push({
          name: 'K线',
          type: 'candlestick',
          data: klineData,
          itemStyle: {
            color: upColor,
            color0: downColor,
            borderColor: upColor,
            borderColor0: downColor
          },
          z: 1
        });

        rawData.forEach(item => {
          if (item.high != null) allValues.push(item.high);
          if (item.low != null) allValues.push(item.low);
          if (item.close != null) allValues.push(item.close);
        });

      } else {
        // 均线模式
        const ma4 = rawData.map(item => item.MA4);
        const ma8 = rawData.map(item => item.MA8);
        const ma12 = rawData.map(item => item.MA12);
        const ma16 = rawData.map(item => item.MA16);
        const ma20 = rawData.map(item => item.MA20);
        const ma47 = rawData.map(item => item.MA47);

        series.push(
            { name: 'MA4', data: ma4, type: 'line', lineStyle: { width: 1.2, color:'#cd1f0e' }, showSymbol: false, z: 2 },
            { name: 'MA8', data: ma8, type: 'line', lineStyle: { width: 1.2, color:'#edbf09'}, showSymbol: false, z: 2 },
            { name: 'MA12', data: ma12, type: 'line', lineStyle: { width: 1.2, color:'#62c613'}, showSymbol: false, z: 2 },
            { name: 'MA16', data: ma16, type: 'line', lineStyle: { width: 1.2, color:'#1286ff'}, showSymbol: false, z: 2 },
            { name: 'MA20', data: ma20, type: 'line', lineStyle: { width: 1.2, color:'#9f12ff'}, showSymbol: false, z: 2 },
            { name: 'MA47', data: ma47, type: 'line', lineStyle: { width: 1.2, color:'#000000'}, showSymbol: false, z: 2 }
        );

        rawData.forEach(item => {
          if (item.MA4 != null) allValues.push(item.MA4);
          if (item.MA8 != null) allValues.push(item.MA8);
          if (item.MA12 != null) allValues.push(item.MA12);
          if (item.MA16 != null) allValues.push(item.MA16);
          if (item.MA20 != null) allValues.push(item.MA20);
          if (item.MA47 != null) allValues.push(item.MA47);
        });
      }

      const validValues = allValues.filter(v => v != null && !isNaN(v) && v !== 0);
      if (validValues.length === 0) return;

      const minValue = Math.min(...validValues);
      const maxValue = Math.max(...validValues);
      const padding = (maxValue - minValue) * 0.1;

      const option = {
        xAxis: { type: 'category', data: dates, show: false },
        yAxis: {
          type: 'value',
          min: minValue - padding,
          max: maxValue + padding,
          axisLabel: { show: false },
          splitLine: { show: false }
        },
        grid: { left: 5, right: 5, top: 5, bottom: 5 },
        series: series
      };

      myChart.setOption(option);

    } catch (error) {
      console.error('ECharts 初始化出错:', error);
    }
  } else if (retryCount < 5) {
    setTimeout(() => {
      initChart3(index, rowIndex, colIndex, retryCount + 1);
    }, 500);
  }
};

// ==========================================
// 【新增】：渲染左侧基准骨架图的逻辑
// ==========================================
const targetChartRefs = ref([]);

const setTargetChartRef = (el, rowIndex) => {
  if (el) {
    targetChartRefs.value[rowIndex] = el;
    nextTick(() => {
      initTargetSkeletonChart(rowIndex);
    });
  }
};

const initTargetSkeletonChart = (rowIndex) => {
  const dom = targetChartRefs.value[rowIndex];
  if (!dom) return;

  let myChart = echarts.getInstanceByDom(dom);
  if (myChart) myChart.dispose();
  myChart = echarts.init(dom);

  // 从全局状态中获取用户画好的骨架和分析模式
  const mode = store.state.newSearchInfo.analysisMode || 'MA';
  const skeletonData = store.state.newSearchInfo.customSkeleton ||[];

  if (mode === 'KLINE' && skeletonData.length > 0) {
    // ==== 渲染红色的骨架连线 ====
    const dates = skeletonData.map(p => p.date);
    const prices = skeletonData.map(p => p.price);

    // 稍微放大一下 Y 轴的上下空间
    const minVal = Math.min(...prices) * 0.98;
    const maxVal = Math.max(...prices) * 1.02;

    myChart.setOption({
      grid: { left: 10, right: 10, top: 30, bottom: 10, containLabel: false },
      xAxis: { type: 'category', data: dates, show: false },
      yAxis: { type: 'value', min: minVal, max: maxVal, show: false },
      series:[{
        type: 'line',
        data: prices,
        lineStyle: { color: '#F56C6C', width: 2.5 }, // 醒目的红色粗线
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#F56C6C', borderColor: '#fff', borderWidth: 2 }
      }]
    });
  } else {
    // 均线模式：渲染基准均线片段（与右侧匹配图一致的 6 色映射）
    const baseSeg = store.state.newSearchInfo.baseSegmentData || [];
    const maColorMap = { MA4: '#cd1f0e', MA8: '#edbf09', MA12: '#62c613', MA16: '#1286ff', MA20: '#9f12ff', MA47: '#000000' };

    if (baseSeg.length > 0) {
      const dates = baseSeg.map(item => item.trade_date || item.timestamps || '');
      const maNames = ['MA4', 'MA8', 'MA12', 'MA16', 'MA20', 'MA47'];
      const series = [];
      const allValues = [];

      maNames.forEach(ma => {
        const data = baseSeg.map(item => item[ma]);
        data.forEach(v => { if (v != null && !isNaN(v)) allValues.push(v); });
        series.push({
          name: ma,
          data: data,
          type: 'line',
          lineStyle: { width: 1.2, color: maColorMap[ma] },
          showSymbol: false,
          z: 2
        });
      });

      const validValues = allValues.filter(v => v != null && !isNaN(v) && v !== 0);
      const minValue = validValues.length ? Math.min(...validValues) : 0;
      const maxValue = validValues.length ? Math.max(...validValues) : 0;
      const padding = (maxValue - minValue) * 0.1 || 1;

      myChart.setOption({
        grid: { left: 5, right: 5, top: 5, bottom: 5 },
        xAxis: { type: 'category', data: dates, show: false },
        yAxis: {
          type: 'value',
          min: minValue - padding,
          max: maxValue + padding,
          axisLabel: { show: false },
          splitLine: { show: false }
        },
        series: series
      });
    } else {
      // 没有基准数据时，显示占位提示
      myChart.setOption({
        title: {
          text: '均线形态\n(请参考右侧匹配结果)',
          textStyle: { fontSize: 13, color: '#C0C4CC', fontWeight: 'normal' },
          left: 'center', top: 'center'
        }
      });
    }
  }
};

const autoCalibrateAndSave = async () => {
  const highScoring = dataObjects3.value.filter(item => item.userRating >= 4);
  if (highScoring.length === 0) {
    ElMessage.warning("请至少为结果列表中的 1 个片段打出 4 星及以上评分");
    return;
  }

  // 1. 计算高分片段的平均波动率
  let totalAmp = 0;
  highScoring.forEach(item => {
    // 假设 item.recent_data_raw 中包含 high 和 low
    const h = Math.max(...item.recent_data_raw.map(d => d.high));
    const l = Math.min(...item.recent_data_raw.map(d => d.low));
    const mean = item.recent_data_raw.map(d => d.close).reduce((a,b)=>a+b, 0) / item.recent_data_raw.length;
    totalAmp += ((h - l) / mean * 100);
  });
  const avgAmp = (totalAmp / highScoring.length).toFixed(1);

  // 2. 发送给后端，更新 JSON 中的记录
  try {
    const timestamp = store.state.newSearchInfo.savedBrushTimeRanges[0]?.saveTime; // 获取当前基准片段的时间戳
    await axios.post('http://127.0.0.1:5000/update_brush_params', {
      timestamp: timestamp,
      new_volatility: parseFloat(avgAmp)
    });

    ElMessage.success(`优化完成！已根据高分样本将波动率特征调整为 ${avgAmp}%`);
  } catch (e) {
    ElMessage.error("参数更新失败");
  }
};

// ========== 负样本自动收集：低分评价触发 ==========
const submitNegativeSample = async (row) => {
  const modeIndex = store.state.modeInfo?.index;
  if (!modeIndex) {
    console.warn('[负样本收集] 缺少 modeInfo.index，跳过');
    return;
  }
  if (!row.recent_data_raw || row.recent_data_raw.length === 0) {
    console.warn('[负样本收集] 缺少 recent_data_raw，跳过');
    return;
  }

  const maNumbers = store.state.modeInfo.lines
    ?.filter(item => item.startsWith('MA'))
    .map(maItem => Number(maItem.slice(2))) || [4, 8, 12, 16, 20, 47];

  try {
    const res = await axios.post('http://127.0.0.1:5000/submit_feedback', {
      mode_index: modeIndex,
      feedback_type: 'dislike',
      recent_data: row.recent_data_raw,
      ma_list: maNumbers
    });
    if (res.data.success) {
      ElMessage({
        type: 'warning',
        message: res.data.msg || '已纳入负样本库',
        duration: 2000
      });
    }
  } catch (e) {
    console.error('[负样本收集] 提交失败:', e);
  }
};

// 监听 dataObjects3 中每条数据的 userRating 变化
watch(
  () => dataObjects3.value.map(item => item.userRating),
  (newRatings, oldRatings) => {
    let changed = false;
    newRatings.forEach((rating, idx) => {
      const prev = oldRatings?.[idx] ?? 0;
      if (rating !== prev && rating > 0) {
        changed = true;
        // 负样本收集（保留）
        if (rating < 2) {
          submitNegativeSample(dataObjects3.value[idx]);
        }
        // 即时校准已移除，改为批量校准按钮触发
      }
    });
    if (changed) syncTrainingPool();
  },
  { deep: true }
);

// ============ 自适应特征学件 ============
const featureState = ref([]);
const quantifiableFeatures = computed(() => featureState.value.filter(f => f.hasValue));
const qualitativeFeatures = computed(() => featureState.value.filter(f => !f.hasValue));

// 初始化特征状态（从 store 读取）
const initFeatureState = () => {
  const rawFeatures = store.state.newSearchInfo.extractedFeatures?.auto || [];
  featureState.value = rawFeatures.map(f => {
    if (typeof f === 'string') {
      return { desc: f, hasValue: false };
    }
    const val = f.hasValue && f.value != null ? Number(f.value) : null;
    const tol = 0.20;
    return {
      desc: f.desc || '',
      shortLabel: extractShortLabel(f.desc || ''),
      hasValue: f.hasValue && val !== null,
      unit: f.unit || '',
      initial: val || 0,
      center: val || 0,
      min: val ? val * (1 - tol) : 0,
      max: val ? val * (1 + tol) : 0,
      tolerance: tol,
      direction: 0,
      flash: false,
      rangePercent: 50,
    };
  });

  // 额外计算特征直接从 store 的 extractedFeatures.auto 读取，无需单独追加
};

function extractShortLabel(desc) {
  // 精确匹配已知特征
  if (desc.includes('波动幅度')) return '波动幅度';
  if (desc.includes('振幅比')) return '振幅比';
  if (desc.includes('最大回撤')) return '最大回撤';
  if (desc.includes('拐点')) return '拐点数';
  if (desc.includes('上行趋势')) return '上行趋势';
  if (desc.includes('下行趋势')) return '下行趋势';
  // 通用提取
  const match = desc.match(/([一-鿿]{2,6}(?:幅度|天数|强度|程度|次数|比例|时间|数量|区间))/);
  if (match) return match[1];
  return desc.length > 8 ? desc.substring(0, 8) + '...' : desc;
}

// 从 segment 的 recent_data_raw 计算量化特征值
function computeSegmentFeatureValues(rawData) {
  if (!rawData || rawData.length === 0) return {};
  const closes = rawData.map(d => Number(d.close || d.Close || 0)).filter(v => v > 0);
  const highs = rawData.map(d => Number(d.high || d.High || 0)).filter(v => v > 0);
  const lows = rawData.map(d => Number(d.low || d.Low || 0)).filter(v => v > 0);
  if (closes.length < 2) return {};

  const returns = [];
  for (let i = 1; i < closes.length; i++) returns.push((closes[i] - closes[i-1]) / closes[i-1]);
  const mean = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
  const std = arr => { const m = mean(arr); return Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / arr.length); };

  const volatility = std(returns) * 100;
  const trend = ((closes[closes.length - 1] / closes[0]) - 1) * 100;
  const amplitude = highs.length > 0 && lows.length > 0
    ? ((Math.max(...highs) - Math.min(...lows)) / mean(closes)) * 100
    : 0;

  // MA cross count
  let crossCount = 0;
  const maKeys = ['MA4', 'MA8', 'MA12', 'MA16', 'MA20', 'MA47'];
  for (let k1 = 0; k1 < maKeys.length - 1; k1++) {
    for (let k2 = k1 + 1; k2 < maKeys.length; k2++) {
      for (let i = 1; i < rawData.length; i++) {
        const prev1 = Number(rawData[i-1][maKeys[k1]] || 0);
        const prev2 = Number(rawData[i-1][maKeys[k2]] || 0);
        const cur1 = Number(rawData[i][maKeys[k1]] || 0);
        const cur2 = Number(rawData[i][maKeys[k2]] || 0);
        if (prev1 && prev2 && cur1 && cur2) {
          if ((prev1 < prev2 && cur1 >= cur2) || (prev1 > prev2 && cur1 <= cur2)) crossCount++;
        }
      }
    }
  }

  // MA entanglement (how close MAs are)
  let entanglement = 0;
  for (let i = 0; i < rawData.length; i++) {
    const vals = maKeys.map(k => Number(rawData[i][k] || 0)).filter(v => v > 0);
    if (vals.length >= 2) entanglement += std(vals) / mean(vals);
  }
  entanglement = rawData.length > 0 ? (entanglement / rawData.length) * 100 : 0;

  // Max drawdown
  let peak = closes[0], maxDD = 0;
  for (const c of closes) {
    if (c > peak) peak = c;
    const dd = (peak - c) / peak;
    if (dd > maxDD) maxDD = dd;
  }

  return { volatility, trend, amplitude, crossCount, entanglement, maxDrawdown: maxDD * 100 };
}

// 打分 → 特征校准
const updateFeaturesOnRating = (rating, segmentRawData) => {
  const segVals = computeSegmentFeatureValues(segmentRawData);
  const eta = 0.2;

  featureState.value.forEach(feat => {
    if (!feat.hasValue) return;

    // 将 segment 计算值映射到对应特征
    let V_i = null;
    const desc = feat.desc;
    if (desc.includes('振幅比') || desc.includes('振幅')) V_i = segVals.amplitude;
    else if (desc.includes('最大回撤') || desc.includes('回撤') || desc.includes('回落')) V_i = segVals.maxDrawdown;
    else if (desc.includes('波动')) V_i = segVals.volatility;
    else if (desc.includes('趋势') || desc.includes('涨跌') || desc.includes('上行') || desc.includes('下行')) V_i = segVals.trend;
    else if (desc.includes('纠缠') || desc.includes('密集') || desc.includes('缠绕')) V_i = segVals.entanglement;
    else if (desc.includes('交叉') || desc.includes('金叉') || desc.includes('上穿') || desc.includes('下穿')) V_i = segVals.crossCount;
    else if (desc.includes('幅度')) V_i = segVals.amplitude;
    // 兜底：如果是第一个量化特征，用 volatility
    if (V_i === null) return;

    const oldCenter = feat.center;

    if (rating >= 4) {
      // 正向强化：中心靠拢，区间收缩
      feat.center = (1 - eta) * feat.center + eta * V_i;
      feat.tolerance = Math.max(0.05, feat.tolerance * 0.95);
      feat.min = feat.center * (1 - feat.tolerance);
      feat.max = feat.center * (1 + feat.tolerance);
    } else if (rating === 3) {
      // 中性：微扩
      feat.tolerance = feat.tolerance * 1.02;
      feat.min = feat.center * (1 - feat.tolerance);
      feat.max = feat.center * (1 + feat.tolerance);
    } else if (rating <= 2 && rating > 0) {
      // 负向排斥：截断边界
      if (V_i > feat.center) {
        feat.max = Math.max(feat.min, feat.max - 0.3 * (V_i - feat.max));
      } else {
        feat.min = Math.min(feat.max, feat.min + 0.3 * (feat.min - V_i));
      }
      feat.center = (feat.min + feat.max) / 2;
    }

    // 方向指示
    const diff = feat.center - oldCenter;
    feat.direction = Math.abs(diff) < 0.01 ? 0 : (diff > 0 ? 1 : -1);

    // 范围百分比（用于进度条）
    const rangeSpan = feat.max - feat.min;
    const fullSpan = feat.initial * feat.tolerance * 2;
    feat.rangePercent = fullSpan > 0 ? Math.max(5, Math.min(100, (1 - rangeSpan / (feat.initial * 0.4 + 0.01)) * 100)) : 50;

    // 闪烁动画
    feat.flash = true;
    setTimeout(() => { feat.flash = false; }, 600);
  });
};

// 初始化
initFeatureState();

// store 数据到达后重新初始化特征面板
watch(() => store.state.newSearchInfo.extractedFeatures?.auto, (newVal) => {
  if (newVal && newVal.length > 0) {
    initFeatureState();
  }
}, { deep: true });


const syntheticGenerating = ref(false);
const syntheticResults = ref([]);
const synthChartRefs = ref([]);
const currentGeneration = ref(1);
const generationHistory = ref([]);

// 训练样本总数（勾选 + 当代选中 + 归档选中）
const totalTrainingCount = computed(() => {
  const tableChecked = selectedTrainingSamples.value.length;
  const synthSelected = syntheticResults.value.filter(s => s.selected).length;
  const archivedSelected = generationHistory.value.flatMap(g => g.samples.filter(s => s.selected)).length;
  return tableChecked + synthSelected + archivedSelected;
});

// 监听归档代际勾选变化
watch(() => generationHistory.value.map(g => g.samples.map(s => s.selected)),
  () => { syncTrainingPool(); },
  { deep: true }
);

// 监听当代仿真样本的评分和勾选变化
watch(() => syntheticResults.value.map(s => [s.userRating, s.selected]),
  () => { syncTrainingPool(); },
  { deep: true }
);

const calibrating = ref(false);

const setSynthChartRef = (el, idx) => {
  if (el) synthChartRefs.value[idx] = el;
};

// 归档图表 ref 管理
const archivedChartRefs = ref({});
const setArchivedChartRef = (el, gen, idx) => {
  if (!archivedChartRefs.value[gen]) archivedChartRefs.value[gen] = [];
  if (el) archivedChartRefs.value[gen][idx] = el;
};

const initArchivedCharts = () => {
  nextTick(() => {
    setTimeout(() => {
      const mode = (store.state.newSearchInfo.analysisMode || 'MA').toUpperCase();
      generationHistory.value.forEach(gen => {
        const refs = archivedChartRefs.value[gen.gen];
        if (!refs) return;
        gen.samples.forEach((synth, idx) => {
          const dom = refs[idx];
          if (!dom) return;
          let chart = echarts.getInstanceByDom(dom);
          if (chart) chart.dispose();
          chart = echarts.init(dom);
          const rawData = synth.recent_data_raw;
          if (!rawData || rawData.length === 0) return;

          // 收集所有数据点计算范围
          const allVals = [];
          if (mode === 'MA') {
            ['MA4','MA8','MA12','MA16','MA20','MA47'].forEach(ma => rawData.forEach(d => { const v = Number(d[ma]); if (v > 0) allVals.push(v); }));
          } else {
            rawData.forEach(d => ['open','close','high','low'].forEach(k => { const v = Number(d[k]); if (v > 0) allVals.push(v); }));
          }
          const dataMin = allVals.length > 0 ? Math.min(...allVals) : 0;
          const dataMax = allVals.length > 0 ? Math.max(...allVals) : 1;
          const padding = (dataMax - dataMin) * 0.1 || 1;

          let series;
          if (mode === 'MA') {
            const maFields = ['MA4','MA8','MA12','MA16','MA20','MA47'].filter(k => rawData[0] && rawData[0][k] != null);
            series = maFields.map(ma => ({ name: ma, type: 'line', showSymbol: false, lineStyle: { width: 1.5 }, data: rawData.map(d => Number(d[ma])) }));
          } else {
            series = [{ type: 'candlestick', data: rawData.map(d => [Number(d.open), Number(d.close), Number(d.low), Number(d.high)]) }];
          }

          chart.setOption({
            animation: false,
            grid: { left: 5, right: 5, top: 5, bottom: 5 },
            xAxis: { type: 'category', show: false, boundaryGap: false },
            yAxis: { type: 'value', show: false, min: dataMin - padding, max: dataMax + padding, scale: true },
            series
          });
        });
      });
    }, 200);
  });
};

// 同步训练池到 Vuex（供 Main copy1 训练集清洗舱使用）
// 逻辑：正样本=仅勾选的；负样本=仅打分≤2星的
const syncTrainingPool = () => {
  store.commit('updateTrainingPool', {
    // 正样本：表格勾选
    positiveChecked: selectedTrainingSamples.value.map(i => ({
      stockCode: i.stockCode, stockName: i.stockName,
      startDate: i.startDate, endDate: i.endDate,
      userRating: i.userRating || 0, source: '勾选',
      recent_data_raw: i.recent_data_raw
    })),
    positiveRated: [], // 不再按高分计入，仅勾选
    // 正样本：仿真勾选（当代 + 归档）
    positiveSynth: [
      ...syntheticResults.value.filter(s => s.selected).map(s => ({
        stockCode: s.sample_id, stockName: s.sample_id,
        userRating: s.userRating, feedback: s.feedback || '', source: '勾选仿真',
        recent_data_raw: s.recent_data_raw
      })),
      ...generationHistory.value.flatMap(gen =>
        gen.samples.filter(s => s.selected).map(s => ({
          stockCode: s.sample_id, stockName: s.sample_id,
          userRating: s.userRating || 0, feedback: s.feedback || '',
          source: `Gen${gen.gen}勾选`, generation: gen.gen,
          recent_data_raw: s.recent_data_raw
        }))
      ),
    ],
    // 负样本：表格打分≤2星
    negativeRated: dataObjects3.value.filter(i => i.userRating > 0 && i.userRating <= 2).map(i => ({
      stockCode: i.stockCode, stockName: i.stockName,
      startDate: i.startDate, endDate: i.endDate,
      userRating: i.userRating, description: i.description || '', source: '低分历史',
      recent_data_raw: i.recent_data_raw
    })),
    // 负样本：仿真打分≤2星（当代 + 归档）
    negativeSynth: [
      ...syntheticResults.value.filter(s => s.userRating > 0 && s.userRating <= 2).map(s => ({
        stockCode: s.sample_id, stockName: s.sample_id,
        userRating: s.userRating, feedback: s.feedback || '', source: '低分仿真',
        recent_data_raw: s.recent_data_raw
      })),
      ...generationHistory.value.flatMap(gen =>
        gen.samples.filter(s => s.userRating > 0 && s.userRating <= 2).map(s => ({
          stockCode: s.sample_id, stockName: s.sample_id,
          userRating: s.userRating, feedback: s.feedback || '',
          source: `Gen${gen.gen}低分`, generation: gen.gen,
          recent_data_raw: s.recent_data_raw
        }))
      ),
    ],
  });
};

// 批量正态分布校准
const batchCalibrate = async () => {
  const ratedItems = dataObjects3.value.filter(item => item.userRating > 0);
  if (ratedItems.length === 0) {
    ElMessage.warning('请先对结果打分');
    return;
  }
  calibrating.value = true;
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/calibrate_features', {
      mode_index: store.state.modeInfo?.index || '',
      ratings: ratedItems.map(item => ({
        rating: item.userRating,
        description: item.description || '',
        recent_data_raw: item.recent_data_raw
      })),
      current_features: quantifiableFeatures.value.map(f => ({
        desc: f.desc, key: f.desc, initial: f.initial,
        center: f.center, min: f.min, max: f.max, unit: f.unit
      }))
    });
    if (res.data.success && res.data.updated_features) {
      // 用后端正态分布结果更新 featureState
      res.data.updated_features.forEach(uf => {
        const feat = featureState.value.find(f => f.desc === uf.desc);
        if (feat) {
          const oldCenter = feat.center;
          feat.center = uf.center;
          feat.min = uf.min;
          feat.max = uf.max;
          feat.direction = uf.center > oldCenter ? 1 : (uf.center < oldCenter ? -1 : 0);
          feat.flash = true;
          setTimeout(() => { feat.flash = false; }, 600);
        }
      });
      ElMessage.success(`校准完成（正态分布 95% 置信区间），基于 ${ratedItems.length} 个评分`);
    } else {
      ElMessage.error(res.data.msg || '校准失败');
    }
  } catch (e) {
    ElMessage.error('校准请求失败: ' + (e.response?.data?.msg || e.message));
  } finally {
    calibrating.value = false;
  }
};

// 递归生成：基于反馈重新生成下一代
const regenerateFromFeedback = async () => {
  const currentGen = syntheticResults.value;
  const goodSamples = currentGen.filter(s => s.userRating >= 4).map(s => s.recent_data_raw);
  const badSamples = currentGen.filter(s => s.userRating > 0 && s.userRating <= 2).map(s => s.recent_data_raw);
  const feedback = currentGen
    .filter(s => s.userRating > 0 || (s.feedback && s.feedback.trim()))
    .map(s => ({ rating: s.userRating, description: s.feedback, recent_data_raw: s.recent_data_raw }));

  if (feedback.length === 0) {
    ElMessage.warning('请先对当前代仿真样本打分或输入反馈');
    return;
  }

  const nextGen = currentGeneration.value + 1;
  const seeds = selectedTrainingSamples.value.map(item => item.recent_data_raw).filter(Boolean);
  const skeleton = store.state.newSearchInfo.skeletonPoints || [];
  const features = (store.state.newSearchInfo.extractedFeatures?.auto || [])
    .map(f => typeof f === 'string' ? f : `${f.desc || ''} ${f.hasValue && f.value != null ? f.value + (f.unit || '') : ''}`.trim());

  // 归档当前代
  generationHistory.value.push({
    gen: currentGeneration.value,
    samples: currentGen.map(s => ({ ...s }))
  });
  initArchivedCharts();

  syntheticGenerating.value = true;
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/generate_synthetic_samples', {
      seeds,
      condition_skeleton: skeleton,
      condition_features: features,
      calibrated_features: quantifiableFeatures.value.map(f => ({
        desc: f.desc, center: f.center, min: f.min, max: f.max, unit: f.unit
      })),
      feedback_data: feedback,
      good_samples: goodSamples,
      bad_samples: badSamples,
      generation: nextGen,
      analysis_mode: store.state.newSearchInfo.analysisMode || 'KLINE',
      ma_list: [4, 8, 12, 16, 20, 47],
      num_samples: 8
    });

    if (res.data.success && res.data.synthetic_results) {
      syntheticResults.value = res.data.synthetic_results.map(s => ({
        ...s,
        generation: nextGen,
        selected: false,
        userRating: 0,
        feedback: ''
      }));
      currentGeneration.value = nextGen;
      ElMessage.success(`第 ${nextGen} 代样本已生成（基于 ${goodSamples.length} 高分 + ${badSamples.length} 低分反馈）`);

      await nextTick();
      setTimeout(() => {
        syntheticResults.value.forEach((_, idx) => initSynthChart(idx));
      }, 200);
    }
  } catch (e) {
    ElMessage.error('重新生成失败');
    console.error(e);
  } finally {
    syntheticGenerating.value = false;
  }
};

const generateAISamples = async () => {
  if (selectedTrainingSamples.value.length === 0) {
    ElMessage.warning('请先勾选 1-3 个真实片段作为种子');
    return;
  }

  // 收集种子数据
  const seeds = selectedTrainingSamples.value.map(item => item.recent_data_raw).filter(Boolean);

  // 从 Vuex 收集骨架和特征
  const skeleton = store.state.newSearchInfo.skeletonPoints || [];
  const features = (store.state.newSearchInfo.extractedFeatures?.auto || [])
    .map(f => {
      if (typeof f === 'string') return f;
      let s = f.desc || '';
      if (f.hasValue && f.value != null) s += ` ${f.value}${f.unit || ''}`;
      return s;
    });

  syntheticGenerating.value = true;
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/generate_synthetic_samples', {
      seeds,
      condition_skeleton: skeleton,
      condition_features: features,
      calibrated_features: quantifiableFeatures.value.map(f => ({
        desc: f.desc, center: f.center, min: f.min, max: f.max, unit: f.unit
      })),
      analysis_mode: store.state.newSearchInfo.analysisMode || 'KLINE',
      ma_list: [4, 8, 12, 16, 20, 47],
      num_samples: 8
    });

    if (res.data.success && res.data.synthetic_results) {
      syntheticResults.value = res.data.synthetic_results.map(s => ({
        ...s,
        generation: 1,
        selected: false,
        userRating: 0,
        feedback: ''
      }));
      currentGeneration.value = 1;
      generationHistory.value = [];
      ElMessage.success(`AI 已生成 ${syntheticResults.value.length} 个仿真样本`);

      await nextTick();
      setTimeout(() => {
        syntheticResults.value.forEach((_, idx) => initSynthChart(idx));
      }, 200);
    }
  } catch (e) {
    ElMessage.error('仿真生成失败');
    console.error(e);
  } finally {
    syntheticGenerating.value = false;
  }
};

const initSynthChart = (idx) => {
  const dom = synthChartRefs.value[idx];
  if (!dom) return;

  let chart = echarts.getInstanceByDom(dom);
  if (chart) chart.dispose();
  chart = echarts.init(dom);

  const synth = syntheticResults.value[idx];
  const rawData = synth.recent_data_raw;
  if (!rawData || rawData.length === 0) return;

  const dates = rawData.map(d => d.trade_date || '');
  const mode = (store.state.newSearchInfo.analysisMode || 'MA').toUpperCase();
  const allValues = [];

  let series = [];
  if (mode === 'KLINE') {
    const klineData = rawData.map(d => [
      d.open || d.close, d.close || 0,
      d.low || d.close, d.high || d.close
    ]);
    series.push({ name: 'K线', type: 'candlestick', data: klineData, itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' } });
    rawData.forEach(d => {
      if (d.high != null) allValues.push(d.high);
      if (d.low != null) allValues.push(d.low);
    });
  } else {
    const maColorMap = { MA4: '#cd1f0e', MA8: '#edbf09', MA12: '#62c613', MA16: '#1286ff', MA20: '#9f12ff', MA47: '#000000' };
    for (const [key, color] of Object.entries(maColorMap)) {
      const vals = rawData.map(d => d[key]);
      if (vals.some(v => v != null)) {
        series.push({ name: key, data: vals, type: 'line', lineStyle: { width: 1, color }, showSymbol: false });
        vals.forEach(v => { if (v != null) allValues.push(v); });
      }
    }
  }

  const validValues = allValues.filter(v => v != null && !isNaN(v) && v !== 0);
  if (validValues.length === 0) return;
  const minVal = Math.min(...validValues);
  const maxVal = Math.max(...validValues);
  const padding = (maxVal - minVal) * 0.08;

  chart.setOption({
    animation: false,
    grid: { left: 5, right: 5, top: 8, bottom: 5 },
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', min: minVal - padding, max: maxVal + padding, show: false },
    series
  });
};

// 1. 用于存储用户勾选样本的响应式变量
const selectedTrainingSamples = ref([]);

// 2. 表格勾选事件
const handleSelectionChange = (val) => {
  selectedTrainingSamples.value = val;
  syncTrainingPool();
};

// 3. 触发训练函数 → 先弹清洗舱（通过 Vuex 跨组件触发 Main copy1 的弹窗）
const triggerModelTraining = () => {
  // 先确保 trainingPool 已同步
  syncTrainingPool();
  const pool = store.state.trainingPool || {};
  const total = (pool.positiveChecked?.length || 0) + (pool.positiveRated?.length || 0) + (pool.positiveSynth?.length || 0);
  if (total === 0) {
    ElMessage.warning('请先勾选样本或对结果打分');
    return;
  }
  // 跨组件触发 Main copy1 的清洗舱弹窗
  store.state.showTrainCleanDialog = true;
};
</script>

<style scoped>
/* 可根据需要添加样式 */
.result-table {
  margin-left: 30px;
  margin-top: 20px;
}
@keyframes feature-flash-anim {
  0% { background: #fff; }
  30% { background: #ecf5ff; }
  100% { background: #fff; }
}
.feature-flash {
  animation: feature-flash-anim 0.6s ease;
}
</style>