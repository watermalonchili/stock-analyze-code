<template>
  <div
    ref="chartRef111"
    :style="`width: ${width ? width + 'px' : '980px'}; height: ${height ? height + 'px' : '550px'}; margin-left: 0px`"
  ></div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from "vue";
import * as echarts from "echarts";
import axios from "axios";
import { defineExpose } from 'vue'

const props = defineProps({
  code: {
    type: String,
    default: false,
  },
  startDate: {
    type: String,
    default: "2016-06-02",
  },
  endDate: {
    type: String,
    default: "2016-06-20",
  },
  checkListMAOption: {
    type: Array,
    default: () => ["", "MA4", "MA8", "MA12", "MA16", "MA20", "MA47"],
  },
  analysisMode: {
    type: String,
    default: 'MA',
  },
  width: {
    type: [Number, String],
    default: 980
  },
  height: {
    type: [Number, String],
    default: 550
  },
  legendData: {
    type: Array,
    default: () => ["SZSE component index", "MA4", "MA8", "MA12", "MA16", "MA20", "MA47"]
  },
  selectedDatePreset: {
    type: String,
    default: null
  },
  isZoomLocked: {
    type: Boolean,
    default: false,
  },
  savedBrushes: {
    type: Array,
    default: () => [],
  }
});

const emit = defineEmits(['brush-updated']);

const upColor = "#ec0000";
const downColor = "#00da3c";

const currentActiveBrush = ref(null);

function splitData(rawData) {
  let categoryData = [];
  let values = [];
  let volumes = [];
  for (let i = 0; i < rawData.length; i++) {
    const item = rawData[i];
    categoryData.push(rawData[i].splice(0, 1)[0]);
    values.push(item);
    const isUp = item[1] > item[0];
    volumes.push({
      value: [i, item[4]],
      itemStyle: {
        color: isUp ? upColor : downColor,
      },
    });
  }
  return {
    categoryData,
    values,
    volumes,
  };
}

function calculateMA(dayCount, data) {
  let result = [];
  for (let i = 0, len = data.values.length; i < len; i++) {
    if (i < dayCount) {
      result.push("-");
      continue;
    }
    var sum = 0;
    for (let j = 0; j < dayCount; j++) {
      sum += data.values[i - j][1];
    }
    result.push(+(sum / dayCount).toFixed(3));
  }
  return result;
}

const chartRef111 = ref(null);
let myChart = null;
let rawDataGlobal = null;

function formatDateToLocal(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

watch(
  [() => props.startDate, () => props.endDate],
  ([newStartDate, newEndDate], [oldStartDate, oldEndDate]) => {
    console.log('[Graph.vue] Watch: startDate or endDate changed', { newStartDate, newEndDate, oldStartDate, oldEndDate });
    if (!props.selectedDatePreset && (newStartDate !== oldStartDate || newEndDate !== oldEndDate)) {
      if (!myChart || !rawDataGlobal) {
        return;
      }
      const startIndex = rawDataGlobal.categoryData.findIndex((d) => d >= newStartDate);
      let endIndex = rawDataGlobal.categoryData.findIndex((d) => d >= newEndDate);
      if (startIndex === -1) {
        return;
      }
      if (endIndex === -1) endIndex = rawDataGlobal.categoryData.length - 1;
      myChart.dispatchAction({
        type: "brush",
        areas: [
          {
            brushType: "lineX",
            coordRange: [newStartDate, newEndDate],
            xAxisIndex: 0,
          },
        ],
      });
      myChart.dispatchAction({
        type: "dataZoom",
        start: (startIndex / rawDataGlobal.categoryData.length) * 100,
        end: (endIndex / rawDataGlobal.categoryData.length) * 100 + 0.1,
      });
    }
  },
  {
    deep: true,
    immediate: true,
  }
);

watch(() => props.selectedDatePreset, (newPreset) => {
  if (!myChart || !rawDataGlobal) {
    return;
  }

  const totalDataPoints = rawDataGlobal.categoryData.length;
  let startIndex = 0;
  let endIndex = totalDataPoints - 1;
  let startPercent = 0;
  let endPercent = 100;
  let coordRangeStart = rawDataGlobal.categoryData[0];
  let coordRangeEnd = rawDataGlobal.categoryData[totalDataPoints - 1];

  const today = new Date(rawDataGlobal.categoryData[endIndex]); // Use latest available date in data as "today"
  
  if (newPreset) {
    let tempStartDate = new Date(today);
    switch (newPreset) {
      case 'daily':
        tempStartDate.setDate(today.getDate() - 30);
        break;
      case 'weekly':
        tempStartDate.setMonth(today.getMonth() - 6);
        break;
      case 'monthly':
        tempStartDate.setFullYear(today.getFullYear() - 2);
        break;
      default:
        break;
    }
    coordRangeStart = formatDateToLocal(tempStartDate);
    coordRangeEnd = formatDateToLocal(today);

    startIndex = rawDataGlobal.categoryData.findIndex((d) => d >= coordRangeStart);
    if (startIndex === -1) startIndex = 0;

    endIndex = rawDataGlobal.categoryData.findIndex((d) => d >= coordRangeEnd);
    if (endIndex === -1) endIndex = totalDataPoints - 1;

    startPercent = (startIndex / totalDataPoints) * 100;
    endPercent = (endIndex / totalDataPoints) * 100 + 0.1;
  }
  myChart.dispatchAction({
    type: "brush",
    areas: [
      {
        brushType: "lineX",
        coordRange: [coordRangeStart, coordRangeEnd],
        xAxisIndex: 0,
      },
    ],
  });
  myChart.dispatchAction({
    type: "dataZoom",
    start: startPercent,
    end: endPercent,
  });
});

watch(() => props.isZoomLocked, (newVal) => {
  if (myChart) {
    const option = myChart.getOption();
    if (option.dataZoom && option.dataZoom.length > 0) {
      option.dataZoom.forEach(zoom => {
        zoom.zoomLock = newVal;
        zoom.moveOnMouseWheel = !newVal;
      });
    }
    // Update brush type based on isZoomLocked
    if (option.toolbox && option.toolbox.feature && option.toolbox.feature.brush) {
      option.toolbox.feature.brush.type = newVal ? ["lineX"] : []; // Only lineX when locked, none when unlocked
    }
    myChart.setOption(option, {
      notMerge: false, // Ensure this is false to merge options
      lazyUpdate: true // Improve performance
    });
    if (!newVal) {
      clearActiveBrush();
    }
  } else {
    console.warn('[Graph.vue] myChart not initialized when isZoomLocked changed.');
  }
});

watch(() => props.savedBrushes, (newSavedBrushes) => {
  if (myChart) {
    updateGraphicElements();
  } else {
    console.warn('[Graph.vue] myChart not initialized when savedBrushes changed.');
  }
}, { deep: true });

const clearActiveBrush = () => {
    if (myChart) {
        myChart.dispatchAction({
            type: 'brush',
            areas: []
        });
        currentActiveBrush.value = null;
        emit('brush-updated', null);
    } else {
      console.warn('[Graph.vue] myChart not initialized, cannot clear active brush.');
    }
};



const fetchDataAndUpdateChart = async () => {
  console.log('[Graph.vue] fetchDataAndUpdateChart called.');
  if (chartRef111.value) {
    if (!myChart) {
      myChart = echarts.init(chartRef111.value);

      myChart.on('brushSelected', function (params) {
        if (params.batch.length > 0 && params.batch[0].areas.length > 0) {
          const selectedArea = params.batch[0].areas[0];
          console.log('[Graph.vue] Selected area detected:', selectedArea);
          // 根据画框类型获取对应的DOM元素
          let brushElement = null;
          if (selectedArea.brushType === 'rect') {
            // 矩形框：使用原rect元素选择器
            brushElement = myChart.getDom().querySelector('.ec-brush-area-rect');
          } else if (selectedArea.brushType === 'lineX') {
            // 水平线框：选择brush容器下的路径元素（ECharts lineX类型画框的特征元素）
            brushElement = myChart.getDom().querySelector('.ec-brush > path');
          }

          // 替换原像素位置计算逻辑，不依赖DOM元素，直接通过坐标转换获取
          let pixelPosition = null;
          if (selectedArea.brushType === 'lineX') {
            // 对于lineX类型，通过坐标系统计算位置
            const xAxis = myChart.getModel().getComponent('xAxis', 0);
            const grid = myChart.getModel().getComponent('grid', 0);
            if (xAxis && grid && grid.coordinateSystem) {
              const startX = myChart.convertToPixel({ xAxisIndex: 0 }, selectedArea.coordRange[0]);
              const endX = myChart.convertToPixel({ xAxisIndex: 0 }, selectedArea.coordRange[1]);
              const gridRect = grid.coordinateSystem.getRect();
              
              pixelPosition = {
                x: Math.min(startX, endX),
                y: gridRect.y,
                width: Math.abs(endX - startX),
                height: gridRect.height
              };
              console.log(`[Graph.vue] Calculated lineX pixelPosition:`, pixelPosition);
            }
          } else if (selectedArea.brushType === 'rect' && brushElement) {
            // 保留原rect类型的计算逻辑
            const bbox = brushElement.getBoundingClientRect();
            const chartRect = myChart.getDom().getBoundingClientRect();
            pixelPosition = {
              x: bbox.left - chartRect.left,
              y: bbox.top - chartRect.top,
              width: bbox.width,
              height: bbox.height
            };
          }

          let brushInfo;
          if (selectedArea.brushType === 'rect') {
            const startXIndex = selectedArea.coordRange[0][0];
            const endXIndex = selectedArea.coordRange[1][0];
            console.log('[Graph.vue] Rect brush selected from X index:', startXIndex, 'to', endXIndex);
            const startYValue = selectedArea.coordRange[0][1];
            const endYValue = selectedArea.coordRange[1][1];
            
            brushInfo = {
              type: 'rect',
              startDate: rawDataGlobal.categoryData[startXIndex],
              endDate: rawDataGlobal.categoryData[endXIndex],
              yRange: [startYValue, endYValue],
              pixelPosition: pixelPosition
            };
          }
          else { // brushType === 'lineX'
            const startVal = selectedArea.coordRange[0];
            const endVal = selectedArea.coordRange[1];
            console.log('[Graph.vue] lineX coordRange values:', startVal, endVal, 'types:', typeof startVal, typeof endVal);
            // coordRange may be indices (number) or category values (string) depending on ECharts version
            const startDate = typeof startVal === 'number' ? rawDataGlobal.categoryData[startVal] : startVal;
            const endDate = typeof endVal === 'number' ? rawDataGlobal.categoryData[endVal] : endVal;
            brushInfo = {
              type: 'lineX',
              startDate,
              endDate,
              pixelPosition: pixelPosition
            };
          }
          currentActiveBrush.value = brushInfo;
          emit('brush-updated', currentActiveBrush.value);
        } else {
            currentActiveBrush.value = null;
            emit('brush-updated', null);
        }
      });
    }
    try {
      console.log(`[Graph.vue] Fetching data for code: ${props.code}.json`);
      const response = await axios.get(`/data/${props.code}.json`);
      const rawData = response.data;
      rawDataGlobal = splitData(rawData);
      console.log('[Graph.vue] Data fetched and split successfully.');
      setChartOption();
      console.log('[Graph.vue] Chart option set after data fetch.');

      // Dispatch initial brush for a default view
      myChart.dispatchAction({
        type: "brush",
        areas: [
          {
            brushType: "lineX",
            coordRange: ["2020-01-01", "2020-12-31"], // Default range for initial view
            xAxisIndex: 0,
          },
        ],
      });
    } catch (error) {
      console.error("[Graph.vue] Failed to get data:", error);
    }
  } else {
    console.error('[Graph.vue] chartRef111 is null. Chart div not found.');
  }
};

const updateGraphicElements = () => {
    if (!myChart || !rawDataGlobal) {
        return;
    }
    const graphicElements = props.savedBrushes.map(brush => {
        const startIndex = rawDataGlobal.categoryData.indexOf(brush.startDate);
        const endIndex = rawDataGlobal.categoryData.indexOf(brush.endDate);
        if (startIndex === -1 || endIndex === -1) {
            return null;
        }
        if (brush.type === 'rect' && brush.pixelPosition) {
            return {
                type: 'rect',
                shape: {
                    x: brush.pixelPosition.x,
                    y: brush.pixelPosition.y,
                    width: brush.pixelPosition.width,
                    height: brush.pixelPosition.height
                },
                style: {
                    stroke: 'red',
                    fill: 'rgba(0,0,0,0)',
                    lineWidth: 2
                },
                z: 100
            };
        } else if (brush.type === 'lineX') {
            const xAxis = myChart.getModel().getComponent('xAxis', 0);
            const grid = myChart.getModel().getComponent('grid', 0);

            // Ensure grid and xAxis coordinate systems are ready
            if (!grid || !xAxis || !grid.coordinateSystem || !xAxis.coordinateSystem) {
              return null;
            }

            const xStart = myChart.convertToPixel({ xAxisIndex: 0 }, rawDataGlobal.categoryData[startIndex]);
            const xEnd = myChart.convertToPixel({ xAxisIndex: 0 }, rawDataGlobal.categoryData[endIndex]);
            const gridRect = grid.coordinateSystem.getRect();
            const yTop = gridRect.y;
            const yBottom = gridRect.y + gridRect.height;
            const rectWidth = Math.abs(xEnd - xStart);
            const rectX = Math.min(xStart, xEnd);
            return {
                type: 'rect',
                shape: {
                    x: rectX,
                    y: yTop,
                    width: rectWidth,
                    height: yBottom - yTop
                },
                style: {
                    stroke: 'red',
                    fill: 'rgba(0,0,0,0)',
                    lineWidth: 2
                },
                z: 100
            };
        }
        return null;
    }).filter(Boolean);

    myChart.setOption({
        graphic: graphicElements
    }, {
        notMerge: false,
        lazyUpdate: true
    });
};


function setChartOption() {
  if (!rawDataGlobal) {
    console.error("[Graph.vue] setChartOption: rawDataGlobal is null. Cannot set chart option.");
    return;
  }
  const option = {
    color: ['#cd1f0e ', '#edbf09', '#62c613', '#1286ff', '#9f12ff', '#000000'],
    animation: true,
    legend: {
      top: 35,
      left: "center",
      data: props.checkListMAOption,
      selected:{'个股': props.analysisMode === 'KLINE', '深证指数':false, '行业指数':false},
      itemWidth: 13,
      itemHeight: 13,
      textStyle: {
        fontSize: 11
      }
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      borderWidth: 1,
      borderColor: "#ccc",
      padding: 5,
      textStyle: { color: "#000", align: "left", fontSize: 9 },
      position: function (pos) {
        return [pos[0] + 20, pos[1] - 50];
      },
    },
    axisPointer: {
      link: [{ xAxisIndex: "all" }],
      label: { backgroundColor: "#777" },
    },
    toolbox: {
      show: true, 
      right: 90,
      top: 25,
      feature: {
        dataZoom: { yAxisIndex: false },
        brush: {
          type: ["lineX", "clear"],
          iconStyle: {
            borderColor: "#000",
            color: "#fff",
          },
          title: {
            lineX: "横向选择",
            clear: "清除选择",
          },
        }, // Modified: only lineX when locked, none when unlocked
      },
    },
    brush: {
      xAxisIndex: "all",
      brushLink: "all",
      outOfBrush: { colorAlpha: 0.1 },
    },
    grid: [
      {
        left: "10%",
        right: "8%",
        height: "50%",
      },
      {
        left: "10%",
        right: "8%",
        top: "49%",
        height: "9%",
      },
    ],
    xAxis: [
      {
        type: "category",
        data: rawDataGlobal.categoryData,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: "dataMin",
        max: "dataMax",
        axisPointer: {
          z: 100,
        },
      },
      {
        type: "category",
        gridIndex: 1,
        data: rawDataGlobal.categoryData,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: "dataMin",
        max: "dataMax",
      },
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true,
        },
        splitLine: { show: false },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        show: false,
      },
    ],
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: [0, 1],
        start: 95,
        end: 100,
        zoomLock: props.isZoomLocked,
        moveOnMouseWheel: !props.isZoomLocked,
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: "slider",
        top: "65%",
        height: 25,
        start: 95,
        end: 100,
        zoomLock: props.isZoomLocked,
        moveOnMouseWheel: !props.isZoomLocked,
      },
    ],
    series: [
      {
        name: props.checkListMAOption[0],
        type: "candlestick",
        data: rawDataGlobal.values,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: undefined,
          borderColor0: undefined,
        },
      },
      ...props.checkListMAOption.slice(1).map((ma) => ({
        name: ma,
        type: "line",
        data: calculateMA(parseInt(ma.replace("MA", "")), rawDataGlobal),
        smooth: true,
        symbol: "circle",
        symbolSize: 0,
        lineStyle: { opacity: 1, width: 0.8 },
      })),
    ],
    graphic: []
  };
  myChart.setOption(option, true);
  updateGraphicElements(); // After setting the main option, update graphic elements
}

onMounted(() => {
  console.log('[Graph.vue] Component mounted. chartRef111:', chartRef111.value);
  nextTick(() => {
    fetchDataAndUpdateChart();
  });
});

watch(() => props.checkListMAOption, () => {
  console.log('[Graph.vue] Watch: checkListMAOption changed', props.checkListMAOption);
    if (rawDataGlobal && myChart) {
      console.log("[Graph.vue] MA line selection changed, starting chart refresh.");
      setChartOption(); // This will re-apply the option with new MA lines and updated brush/dataZoom lock
      
      // Re-dispatch brush and dataZoom to ensure the view aligns with new options
      const newStartDate = props.startDate;
      const newEndDate = props.endDate;
      
      const startIndex = rawDataGlobal.categoryData.findIndex((d) => d >= newStartDate);
      let endIndex = rawDataGlobal.categoryData.findIndex((d) => d >= newEndDate);
      if (startIndex === -1) {
        console.warn("[Graph.vue] checkListMAOption watch: Start date not found, skipping brush/dataZoom dispatch.");
        return;
      }
      if (endIndex === -1) endIndex = rawDataGlobal.categoryData.length - 1;
      
      myChart.dispatchAction({
        type: "brush",
        areas: [
          {
            brushType: "lineX",
            coordRange: [newStartDate, newEndDate],
            xAxisIndex: 0,
          },
        ],
      });
      myChart.dispatchAction({
        type: "dataZoom",
        start: (startIndex / rawDataGlobal.categoryData.length) * 100,
        end: (endIndex / rawDataGlobal.categoryData.length) * 100 + 0.1,
      });
      console.log(`[Graph.vue] checkListMAOption watch: Dispatched dataZoom for range: ${newStartDate} to ${newEndDate}`);
    } else {
      console.warn('[Graph.vue] checkListMAOption watch: rawDataGlobal or myChart not ready.');
    }
  },
  { deep: true }
);

watch(() => props.analysisMode, (newMode) => {
  if (myChart) {
    myChart.dispatchAction({
      type: 'legendToggleSelect',
      name: '个股'
    });
    // 确保目标状态正确：dispatchAction 是 toggle，需要判断当前状态
    // 改用 setOption 直接控制 selected
    const option = myChart.getOption();
    if (option.legend && option.legend[0]) {
      const selected = option.legend[0].selected || {};
      if (newMode === 'KLINE' && selected['个股'] === false) {
        myChart.dispatchAction({ type: 'legendToggleSelect', name: '个股' });
      } else if (newMode !== 'KLINE' && selected['个股'] !== false) {
        myChart.dispatchAction({ type: 'legendToggleSelect', name: '个股' });
      }
    }
  }
});

watch(() => props.code,() => {
  console.log('[Graph.vue] Watch: code changed to', props.code);
  fetchDataAndUpdateChart();
});

const getDataByRange = (start, end) => {
  // 1. 获取当前图表的完整配置项
  if (!myChart) return null;
  const option = myChart.getOption();

  // 2. 获取 X 轴上的所有日期数据
  const xAxisData = option.xAxis[0].data;
  if (!xAxisData) return null;

  // 3. 寻找选定日期的索引位置
  const startIndex = xAxisData.findIndex(d => d === start);
  const endIndex = xAxisData.findIndex(d => d === end);

  if (startIndex === -1 || endIndex === -1) {
    console.error("在图表中未找到指定的日期区间:", start, end);
    return null;
  }

  // 【核心修复：找到图表中的 K 线序列（类型为 candlestick）】
  const klineSeries = option.series.find(s => s.type === 'candlestick');
  const klineRawData = klineSeries ? klineSeries.data : [];

  const result =[];
  // 4. 遍历该索引区间，提取每一天的 K 线和均线数值
  for (let i = startIndex; i <= endIndex; i++) {
    const dayObj = { trade_date: xAxisData[i] };

    // 【新增：提取开、收、低、高数据】
    // Echarts 蜡烛图数据格式通常是 [open, close, lowest, highest]
    if (klineRawData[i]) {
      dayObj.open = klineRawData[i][0];
      dayObj.close = klineRawData[i][1];
      dayObj.low = klineRawData[i][2];
      dayObj.high = klineRawData[i][3];
    }

    // 提取用户选中的 MA 均线数据
    props.checkListMAOption.forEach(maName => {
      const seriesItem = option.series.find(s => s.name === maName);
      if (seriesItem && seriesItem.data) {
        dayObj[maName] = seriesItem.data[i];
      }
    });

    result.push(dayObj);
  }

  console.log("成功提取包含 K 线和均线的片段数据:", result);
  return result;
};
const dispatchBrush = (start, end) => {
  if (!myChart) return;
  myChart.dispatchAction({
    type: "brush",
    areas: [{ brushType: "lineX", coordRange: [start, end], xAxisIndex: 0 }]
  });
};

defineExpose({ getDataByRange, clearActiveBrush, dispatchBrush });

</script>