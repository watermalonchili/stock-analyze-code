<!--
  页面说明：
  本页面用于展示推荐模式和自定义模式的卡片列表，每个卡片内嵌入均线走势小图，辅助用户选择或查看不同的均线模式。
-->
<template>
  <div
    style="
      background-color: #f3f3f3;
      height: 600px;
      width: 265px;
      margin-top: -15px;
      margin-bottom: 10px;
      border-radius: 10px;"
  >
    <el-tabs v-model="activeName3" style="margin-left: 20px; width: 220px; height: 570px;">
      <el-tab-pane label="系统模式" name="index">
        <div class="scrollable-div">
          <!-- <el-card style="height: 60px; width: 210px; margin-bottom: 10px;" @click="handleCardClick1()">
            <span style="margin-top: -60px; font-size: 13px; font-weight: bold; cursor: pointer;">自定义模式</span>
          </el-card> -->
          <el-card
            v-for="(item, index) in modeList"
            :key="index"
            style="margin-bottom: 10px;margin-left: 0px;width: 210px; height: 200px;
            "
          >
            <!-- 使用动态 ref 绑定 -->
            <div
              :ref="(el) => (chartRefs[index] = el)"
              style="  width: 205px;  height: 200px;  margin-top: -60px;  margin-left: -20px;  z-index: 1; "
            ></div>
            <template #header>
              <div
                @click="handleCardClick(item, index)"
                class="mode-card-title"
                style="position: relative; z-index: 2; margin-top: -15px; font-size: 13px; font-weight: bold; cursor: pointer;"
              >
                {{ item.name }}
              </div>
            </template>
          </el-card>
          <el-dialog
            v-model="dialogVisible"
            :append-to-body="true"
            :destroy-on-close="true"
            @open="handleDialogOpen"
            class="modecards-dialog-tour"
          >
            <template #title>系统模式详解</template>
            <hr/>
            <!-- 将table和chart容器直接放在默认插槽 -->
            <el-table :data="tableData" stripe border >
              <el-table-column prop="name" label="模式名称" width="110" />
              <el-table-column prop="code" label="模式代码" width="110" />
              <el-table-column prop="desc" label="模式定义" width="240"/>
              <el-table-column prop="class" label="模式类型" width="120" />
              <el-table-column prop="minDays" label="查找时间区间/天" width="140"/>
            </el-table>
            <div ref="dialogChartRef" style="width: 700px; height: 300px; margin-top: -40px; margin-bottom: -40px;"></div>
            <template #footer>
                <el-button style="position: relative; z-index: 1;" @click="handleApplyMode0" class="apply-mode-btn-step2">历史查找(新)</el-button>
                <el-button style="position: relative; z-index: 1;" @click="handleApplyMode" class="apply-mode-btn-step2">历史查找</el-button>
                <el-button @click="handleApplyMode1" class="apply-mode-btn-step2">模式选股</el-button>
            </template>
          </el-dialog>
        </div>
      </el-tab-pane>
      <el-tab-pane label="自定义模式" name="index1">
        <div class="scrollable-div">
          <el-card
            v-for="(item, index) in modeListSelf"
            :key="index"
            style="margin-bottom: 10px;margin-left: 0px;width: 210px; height: 50px;"
          >
              <div
                @click="handleCustomCardClick(item, index)"
                class="mode-card-title"
                style="margin-top: -5px; font-size: 13px; font-weight: bold; cursor: pointer;"
              >
                {{ item.name }}
              </div>

          </el-card>
          <!-- 自定义模式专用对话框 -->
          <el-dialog
            v-model="customDialogVisible"
            :append-to-body="true"
            :destroy-on-close="true"
            @open="handleCustomDialogOpen"
            class="modecards-dialog-tour"
          >
            <template #title>{{ customDialogTitle }}</template>
            <hr/>
            <el-table :data="customTableData" stripe border style="margin-bottom: 20px;">
              <el-table-column header-align="center" align="center" prop="name" label="模式名称" width="140" />
              <el-table-column header-align="center" align="center" prop="index" label="模式代码" width="140" />
              <el-table-column header-align="center" align="center" prop="lines" label="均线列表" width="240"/>
              <!--可添加其他用户自定义的相似性匹配参数-->
              <el-table-column header-align="center" align="center" prop="recentNDaysValue" label="选股考察区间（近N天）" width="200"/>
            </el-table>
            <span style="font-size: 13px; color: black; margin-left: 10px;">该自定义模式的查找基准区间</span>
            <div style="border: 1px solid #cbcbcb; height: 180px; width: 100%;  margin-left: 0px; margin-top: 5px; border-radius: 5px; overflow: hidden;">

              <div style="display: flex; height: 170px; align-items: center; padding: 0 15px; overflow-x: auto; scrollbar-width: none; margin-top: 10px;">
                <div v-for="img in imageList" :key="img.filename" class="image-gallery" style="margin-right: 15px; flex-shrink: 0;">
                  <img
                    :src="img.url"
                    :alt="img.filename"
                    :title="img.filename"
                    class="screenshot-img"
                    style="width: 260px; height: 260px; object-fit: cover; border-radius: 3px; margin-top: 28px;"
                    @error="handleImageError(img)"
                  >
                </div>
              </div>
            </div>
            <template #footer>
              <el-button @click="handleApplyModeCustomNew" type="primary" plain>历史查找(新)</el-button>
                <el-button @click="handleApplyMode2" class="apply-mode-btn-step2">历史查找</el-button>
                <el-button @click="handleApplyMode3" class="apply-mode-btn-step2">模式选股</el-button>
            </template>
          </el-dialog>
          <!-- 推荐模式专用对话框 -->
          <el-dialog
            v-model="dialogVisible"
            :append-to-body="true"
            :destroy-on-close="true"
            @open="handleDialogOpen"
            class="modecards-dialog-tour"
          >
            <template #title>系统模式详解</template>
            <hr/>
            <!-- 将table和chart容器直接放在默认插槽 -->
            <el-table :data="tableData" stripe border >
              <el-table-column prop="name" label="模式名称" width="110" />
              <el-table-column prop="code" label="模式代码" width="110" />
              <el-table-column prop="desc" label="模式定义" width="240"/>
              <el-table-column prop="class" label="模式类型" width="120" />
              <el-table-column prop="minDays" label="查找时间区间/天" width="140"/>
            </el-table>
            <div ref="dialogChartRef" style="width: 700px; height: 300px; margin-top: -40px; margin-bottom: -40px;"></div>
            <template #footer>
                <el-button @click="handleApplyMode0" class="apply-mode-btn-step2">历史查找（新）</el-button>
                <el-button @click="handleApplyMode" class="apply-mode-btn-step2">历史查找</el-button>
                <el-button @click="handleApplyMode1" class="apply-mode-btn-step2">模式选股</el-button>
            </template>
          </el-dialog>
        </div>
      </el-tab-pane>
      <!-- <el-tab-pane label="自定义模式" name="self"> </el-tab-pane> -->
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, defineProps, defineEmits,toRaw, computed } from "vue";
import { useStore } from "vuex";
import axios from "axios";
import * as echarts from "echarts";

const store = useStore();
const activeName3 = ref("index");
const modeList = store.state.modeList.map((item) => {
  return {
    name: item.name,
    index: item.index,
    modeClass: item.modeClass,
    modeDescription: item.modeDescription,
    minDays: item.minDays,
    isSelected: item.isSelected,
    lines: item.lines,
  };
});

// const modeListSelf = store.state.modeListSelf.map((item) => {
//   return {
//     name: item.name,
//     index: item.index,
//     modeFolder: item.modeFolder,
//     selectedFactor: item.selectedFactor,
//     selectedFactor2: item.selectedFactor2,
//     photoOption: item.photoOption,
//     savedBrushTimeRanges: item.savedBrushTimeRanges,
//     recentNDaysValue: item.recentNDaysValue,
//     lines: item.lines,
//   };
// });

// 图片获取 ==========================================================
// const modeListSelf = ref([]);

const modeListSelf = computed(() => {
  return store.getters.getModeListSelf
})

const imageList = ref([]);
const loading = ref(true);
// 获取图片列表函数（修改版）
const fetchImages = async () => {
  const timestamp = new Date().getTime();
  const API_BASE_URL = 'http://127.0.0.1:5000';
  const folderName = toRaw(customTableData.value)[0].index;

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
};

const modeInfo = store.state.modeInfo;

// 查找 .div-custom 样式规则
const findDivCustomRule = () => {
  for (const styleSheet of document.styleSheets) {
    try {
      const rules = styleSheet.cssRules || styleSheet.rules;
      for (const rule of rules) {
        if (rule.selectorText === '.div-custom') {
          console.log('找到 .div-custom 样式规则:', rule);
          return rule;
        }
      }
    } catch (e) {
      console.warn('无法访问样式表:', e);
    }
  }
  return null;
};

// 存储 CSS 文件引用
let cssRule = null;

const handleApplyMode0 = () => {
  // 处理应用模式的逻辑
  console.log("应用模式(新):", modeList[currentChartIndex.value]);
  store.commit('updateModeInfo', {
    index: modeList[currentChartIndex.value].index,
    name: modeList[currentChartIndex.value].name,
    modeClass: modeList[currentChartIndex.value].modeClass,
    modeDescription: modeList[currentChartIndex.value].modeDescription,
    lines: ["个股", ...modeList[currentChartIndex.value].lines],
    lines1: ["深证指数", ...modeList[currentChartIndex.value].lines],
    lines2: ["行业指数", ...modeList[currentChartIndex.value].lines],
    isMode: true,
    minDays: modeList[currentChartIndex.value].minDays,
  });
  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction:"逻辑模式回测",
    isDisabled: true,
    isChooseStock: false,
    isHistorySearch: false,
    isHistorySearchNew: true,
  });
  if (!cssRule) {
    // 查找 .div-custom 规则
    cssRule = findDivCustomRule();
    if (!cssRule) {
      console.error('未找到 .div-custom 样式规则');
      return;
    }
  }
  // 添加边框样式
  cssRule.style.border = '1px solid gray';
  dialogVisible.value = false;
  customDialogVisible.value = false;
};

const handleApplyMode = () => {
  // 处理应用模式的逻辑
  console.log("应用模式:", modeList[currentChartIndex.value]);
  store.commit('updateModeInfo', {
    index: modeList[currentChartIndex.value].index,
    name: modeList[currentChartIndex.value].name,
    modeClass: modeList[currentChartIndex.value].modeClass,
    modeDescription: modeList[currentChartIndex.value].modeDescription,
    lines: ["个股", ...modeList[currentChartIndex.value].lines],
    lines1: ["深证指数", ...modeList[currentChartIndex.value].lines],
    lines2: ["行业指数", ...modeList[currentChartIndex.value].lines],
    isMode: true,
    minDays: modeList[currentChartIndex.value].minDays,
  });
  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction:"历史查找",
    isDisabled: true,
    isChooseStock: false,
    isHistorySearchNew: false,
    isHistorySearch: true,
  });
  if (!cssRule) {
    // 查找 .div-custom 规则
    cssRule = findDivCustomRule();
    if (!cssRule) {
      console.error('未找到 .div-custom 样式规则');
      return;
    }
  }
  // 添加边框样式
  cssRule.style.border = '1px solid gray';
  dialogVisible.value = false;
  customDialogVisible.value = false;
};

const handleApplyMode1 = () => {
  // 处理应用模式的逻辑
  console.log("应用模式:", modeList[currentChartIndex.value]);
  store.commit('updateModeInfo', {
    index: modeList[currentChartIndex.value].index,
    name: modeList[currentChartIndex.value].name,
    modeClass: modeList[currentChartIndex.value].modeClass,
    modeDescription: modeList[currentChartIndex.value].modeDescription,
    lines: ["个股", ...modeList[currentChartIndex.value].lines],
    lines1: ["深证指数", ...modeList[currentChartIndex.value].lines],
    lines2: ["行业指数", ...modeList[currentChartIndex.value].lines],
    isMode: true,
    startDate: '2025-05-04',
    endDate: '2025-05-08',
    minDays: modeList[currentChartIndex.value].minDays,
  });
  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction:"推荐模式查找",
    isDisabled: true,
    isHistorySearch: false,
    isHistorySearchNew: false,
    isChooseStock: true,
  });
  if (!cssRule) {
    // 查找 .div-custom 规则
    cssRule = findDivCustomRule();
    if (!cssRule) {
      console.error('未找到 .div-custom 样式规则');
      return;
    }
  }
  // 添加边框样式
  cssRule.style.border = '1px solid gray';
  dialogVisible.value = false;
  customDialogVisible.value = false;
};

// 自定义模式对话框打开时的处理函数 =============================================
// 历史查找
const handleApplyMode2 = () => {
  // 自定义模式不提供默认查找区间
  store.state.modeInfo.startDate = null;
  store.state.modeInfo.endDate = null;
  console.log("应用模式:", modeListSelf.value[currentChartIndex.value]);
  store.commit('updateModeInfo', {
    index: modeListSelf.value[currentChartIndex.value].index,
    name: modeListSelf.value[currentChartIndex.value].name,
    lines: ["个股", ...modeListSelf.value[currentChartIndex.value].lines],
    isMode: false,
    isSelected: true,
  });

  store.commit('updateNewSearchInfo', {
    recentNDaysValue: modeListSelf.value[currentChartIndex.value].recentNDaysValue,
    baseFolder: modeListSelf.value[currentChartIndex.value].index,
  });


  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction:"推荐模式查找",
    isDisabled: true,
    isChooseStock: false,
    isHistorySearch: true,
    isHistorySearchNew: false,
  });
  if (!cssRule) {
    // 查找 .div-custom 规则
    cssRule = findDivCustomRule();
    if (!cssRule) {
      console.error('未找到 .div-custom 样式规则');
      return;
    }
  }
  // 添加边框样式
  cssRule.style.border = '1px solid gray';
  dialogVisible.value = false;
  customDialogVisible.value = false;
};

const handleApplyMode3 = () => {
  // 处理应用模式的逻辑
  store.state.modeInfo.startDate = null;
  store.state.modeInfo.endDate = null;
  console.log(modeListSelf.value);
  console.log("应用模式:", modeListSelf.value[currentChartIndex.value]);
  store.commit('updateModeInfo', {
    index: modeListSelf.value[currentChartIndex.value].index,
    name: modeListSelf.value[currentChartIndex.value].name,
    lines: ["个股", ...modeListSelf.value[currentChartIndex.value].lines],
    isMode: false,
    isSelected: true,
  });

  store.commit('updateNewSearchInfo', {
    recentNDaysValue: modeListSelf.value[currentChartIndex.value].recentNDaysValue,
    baseFolder: modeListSelf.value[currentChartIndex.value].index,
    savedBrushTimeRanges: modeListSelf.value[currentChartIndex.value].savedBrushTimeRanges,
  });
  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction:"推荐模式查找",
    isDisabled: true,
    isHistorySearch: false,
    isHistorySearchNew: false,
    isChooseStock: true,
  });
  if (!cssRule) {
    // 查找 .div-custom 规则
    cssRule = findDivCustomRule();
    if (!cssRule) {
      console.error('未找到 .div-custom 样式规则');
      return;
    }
  }
  console.log('新的自定义区间', store.state.newSearchInfo.savedBrushTimeRanges);
  // 添加边框样式
  cssRule.style.border = '1px solid gray';
  dialogVisible.value = false;
  customDialogVisible.value = false;
};



const tableData = ref([
  {
    name: "模式1",
    code: "MODE1",
    desc: "描述1",
    class: "类型1",
    minDays: 5,
    isConsecutive: "是",
  },
]);

const customTableData = ref([
]);

const dialogVisible = ref(false);
const customDialogVisible = ref(false);
const dialogTitle = ref('');
const customDialogTitle = ref('');
let currentChartIndex = ref(null);
const dialogChartRef = ref(null);
const chartRefs = ref([]);

const handleCardClick = (item, index) => {
  // 显示弹窗
  dialogVisible.value = true;
  // 设置弹窗标题和内容
  dialogTitle.value = item.name;
  currentChartIndex.value = index;
  tableData.value = [{
      name: item.name,
      code: item.index,
      desc: item.modeDescription,
      class: item.modeClass,
      minDays: item.minDays,
      isConsecutive: item.isConsecutive,
    }]
};

const handleCustomCardClick = (item, index) => {
  // 显示自定义模式弹窗
  customDialogVisible.value = true;
  // 设置弹窗标题和内容
  customDialogTitle.value = item.name;
  currentChartIndex.value = index;
  customTableData.value = [{
      name: item.name,
      index: item.index,
      lines: item.lines,
      recentNDaysValue: item.recentNDaysValue,
    }]
  fetchImages(); // 获取对应的图片列表
};

const handleCardClick1 = (item, index) => {
    store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    isDisabled: true,
    isHistorySearch: false,
    isChooseStock: true,
  });
};


// 定义公共的系列配置
const commonSeriesConfig = {
  type: "line",
  showSymbol: false, // 不显示数据圆点
  lineStyle: {
    width: 1, // 减小曲线粗细
  },
};

// 定义每个折线图的真实数据，描述不同的均线走势，并添加曲线名称
const chartDataList = [
    {
    curveNames: modeList[0].lines,
    series: [
      { data: [125, 132, 138, 142, 150, 158, 165, 168, 178, 185, 192] },
      { data: [110, 116, 122, 125, 134, 140, 143, 147, 153, 160, 167] },
      { data: [95, 102, 109, 113, 122, 130, 136, 141, 150, 158, 165] },
      { data: [80, 84, 88, 90.4, 96, 100, 104, 105.6, 112, 116, 120] },
      { data: [63, 66.5, 70, 71.4, 77, 80.5, 81.9, 84, 87.5, 91, 94.5] },
      { data: [51, 54, 55.2, 57, 60, 62.4, 64.2, 66, 69, 70.8, 73.2]},

    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA4","MA8", "MA12","MA16", "MA20", "MA47"][index],
    })),
  },
  {
    curveNames: ["MA4", "MA12", "MA20"],
    series: [
      { data: [190, 180, 170, 160, 150, 140, 130, 120, 110, 100] },
      { data: [135, 130, 125, 120, 115, 110, 105, 100, 95, 90] },
      { data: [98, 96, 94, 92, 90, 88, 86, 84, 82, 80] },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA4", "MA12", "MA20"][index],
    })),
  },
  {
    curveNames: ["MA4", "MA12", "MA20"],
    series: [
      { data: [80, 85, 90, 95, 100, 105, 110, 115, 120, 125] },
      { data: [90, 92, 94, 96, 98, 100, 102, 104, 106, 108] },
      { data: [95, 96, 97, 98, 99, 100, 101, 102, 103, 104] },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA4", "MA12", "MA20"][index],
    })),
  },
  {
    curveNames: ["MA10", "MA20", "MA50"],
    series: [
      { data: [125, 120, 115, 110, 105, 100, 95, 90, 85, 80] },
      { data: [108, 106, 104, 102, 100, 98, 96, 94, 92, 90] },
      { data: [104, 103, 102, 101, 100, 99, 98, 97, 96, 95] },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA10", "MA20", "MA50"][index],
    })),
  },
  {
    curveNames: ["MA4", "MA12", "MA20"],
    series: [
      { data: [90, 90.5, 91, 92, 94, 96, 98, 100, 102, 104] },
      { data: [90, 90.2, 90.4, 90.6, 90.8, 91, 92, 94, 96, 98] },
      { data: [90, 90.1, 90.2, 90.3, 90.4, 90.5, 90.6, 90.8, 91, 92] },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name:["MA4", "MA12", "MA20"][index],
    })),
  },
  {
    curveNames: ["MA10", "MA20", "MA60"],
    series: [
      { data: [110, 110.5, 111, 112, 114, 116, 118, 120, 122, 124] },
      { data: [105, 105.2, 105.4, 105.6, 105.8, 106, 107, 109, 111, 113] },
      {
        data: [100, 100.1, 100.2, 100.3, 100.4, 100.5, 100.6, 100.8, 101, 102],
      },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA10", "MA20", "MA60"][index],
    })),
  },
  {
    curveNames: ["MA5", "MA10", "MA20"],
    series: [
      { data: [100, 100.2, 100.5, 101, 102, 104, 106, 108, 110, 112] },
      {
        data: [
          100, 100.1, 100.3, 100.6, 100.9, 101.2, 101.6, 102, 102.4, 102.8,
        ],
      },
      {
        data: [
          100, 100, 100.1, 100.2, 100.3, 100.4, 100.5, 100.6, 100.7, 100.8,
        ],
      },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA5", "MA10", "MA20"][index],
    })),
  },
  {
    curveNames: ["MA10", "MA20", "MA60"],
    series: [
      { data: [120, 119.8, 119.5, 119, 118, 116, 114, 112, 110, 108] },
      {
        data: [ 120, 119.9, 119.7, 119.4, 119.1, 118.8, 118.4, 118, 117.6, 117.2, ],
      },
      {
        data: [ 120, 120, 119.9, 119.8, 119.7, 119.6, 119.5, 119.4, 119.3, 119.2, ],
      },
    ].map((series, index) => ({
      ...commonSeriesConfig,
      ...series,
      name: ["MA10", "MA20", "MA60"][index],
    })),
  },
];

// 生成图表配置项
const generateChartOptions = (dataIndex) => {
  const data = chartDataList[dataIndex];
  const seriesData = data.series.map((series) => series.data).flat();
  const minData = Math.min(...seriesData);
  const maxData = Math.max(...seriesData);
  const range = maxData - minData;
  const padding = range * 0.125; // 因为有效数据占 80%，所以上下各留 10% 的空间
  return {
    legend: {
      data: data.curveNames,
      left: "left",
      orient: "vertical",
      itemWidth: 8,
      itemHeight: 8,
      iconSize: 8,
      top: "20%",
      textStyle: {
        fontSize: 9,
      },
    },
    xAxis: {
      type: "category",
      data: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    },
    yAxis: {
      type: "value",
      axisTick: { show: false },
      axisLabel: { show: false },
      min: minData - padding,
      max: maxData + padding,
    },
    series: data.series,
  };
};

// 渲染图表
const renderChart = (chartDom, dataIndex) => {
  const myChart = echarts.init(chartDom, null, {
    renderer: "canvas",
    useDirtyRect: false,
  });
  const options = generateChartOptions(dataIndex);
  myChart.setOption(options);
};



// 从store中获取数据
const getModeListSelf = () => store.getters.getModeListSelf;

// 加载数据的方法
const loadModeListSelf = () => store.dispatch('loadModeListSelf');

// 监听数据变化
watch(() => getModeListSelf(),
  (newVal) => {
    if (newVal.length > 0) {
      console.log('从JSON加载的modeListSelf:', newVal);
      modeListSelf.value = newVal;
      // 这里可以处理数据加载完成后的逻辑
    }
  },
  { immediate: true } // 立即执行一次
);


// 从后端获取模式列表
const fetchModeList = async () => {
  try {
    await store.dispatch('fetchModeListSelf')
  } catch (error) {
    alert('获取模式列表失败: ' + error.message)
  }
}

onMounted(() => {
    // loadModeListSelf();
    fetchModeList();
    modeList.forEach((_, index) => {
      const chartDom = chartRefs.value[index];
      if (chartDom) {
        renderChart(chartDom, index);
      } else {
        console.error(`Invalid DOM element at index ${index}`);
      }
    });

});

const renderDialogChart = () => {
  nextTick(() => { // 确保 DOM 更新
    if (dialogChartRef.value && currentChartIndex.value !== null) {
      // 销毁旧图表防止重复
      if (dialogChartRef.value.chartInstance) {
        dialogChartRef.value.chartInstance.dispose();
      }
      const myChart = echarts.init(dialogChartRef.value);
      const options = generateChartOptions(currentChartIndex.value);
      myChart.setOption(options);
      // 可选：保存实例引用以便后续销毁
      dialogChartRef.value.chartInstance = myChart;
    }
  });
};

const handleDialogOpen = () => {
  // 再增加一个小延迟，确保 DOM 完全渲染
  setTimeout(() => {
    nextTick(() => {
      renderDialogChart();
    });
  }, 100);
};


// 手动处理 ResizeObserver 循环
const originalResizeObserver = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends originalResizeObserver {
  constructor(callback) {
    super((entries, observer) => {
      try {
        callback(entries, observer);
      } catch (error) {
        // 捕获错误并避免控制台显示
      }
    });
  }
};

const btnBaseStock = ref()

const startModeTour = () => {
  console.log("点击了推荐模式新手指引");
  setTimeout(() => {
    modeTourVisible.value = true;
  }, 800);
};

const props = defineProps({
  startTour: Boolean
});
const emit = defineEmits(["tour-finished"]);
const modeTourVisible = ref(false);
const modeTourStep = ref(0);

// 监听外部触发
watch(() => props.startTour, (val) => {
  if (val) {
    modeTourStep.value = 0;
    modeTourVisible.value = true;
  }
});

function onTourClose() {
  modeTourVisible.value = false;
  emit("tour-finished");
}

const handleModeTourChange = (current, prev) => {
  // STEP 1: 自动点击推荐模式卡片标题，弹出弹窗
  if (current === 1) {
    const card = document.querySelector('.mode-card-title');
    if (card) {
      card.click();
    }
    setTimeout(() => {
      modeTourStep.value = 1; // 保证 el-tour 继续在第二步
    }, 350);
  }
};

const handleApplyModeCustomNew = () => {
  const selectedMode = modeListSelf.value[currentChartIndex.value];
  if (!selectedMode) return;

  console.log("应用自定义模型(新):", selectedMode.name);

  // 1. 更新模式信息
  store.commit('updateModeInfo', {
    index: selectedMode.index, // 这里会传入 CUSTOM_1772348276 这样的ID
    name: selectedMode.name,
    // 确保均线格式统一
    lines: ["个股", ...selectedMode.lines],
    isMode: true,
  });

  // 2. 关键：激活新版历史查找标识，让 Main.vue 去跑 doResult2
  store.commit("updateBaseInfo", {
    isMode: true,
    isStock: false,
    currentFunction: "逻辑模式回测(自定义)",
    isDisabled: true,
    isChooseStock: false,
    isHistorySearch: false,    // 关闭旧版
    isHistorySearchNew: true,  // 开启新版
  });

  // 3. 处理边框样式反馈
  if (!cssRule) cssRule = findDivCustomRule();
  if (cssRule) cssRule.style.border = '1px solid gray';

  // 关闭弹窗
  customDialogVisible.value = false;
};
</script>

<style scoped>
/* 修改 el-table 的字体大小 */
.el-table {
  font-size: 13px;
  text-align: center;
}

/* 修改 el-table 表头的字体大小 */
.el-table__header th {
  font-size: 13px;
  text-align: center;
}

/* 修改 el-table 表格内容的字体大小 */
.el-table__body td {
  font-size: 13px;
  text-align: center;
}

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 20px;
}

</style>