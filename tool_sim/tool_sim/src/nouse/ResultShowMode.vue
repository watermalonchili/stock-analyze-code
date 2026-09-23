<!--
  页面说明：
  本页面用于展示【系统自定义模式评价】的结果，包括结果表格和YOLO目标检测结果，支持保存配置和下载结果等操作。
-->
<template>
  <div id="app">
    <!--展示模式分析结果的表格-->
    <div style="text-align: left; margin-top: 20px; background-color:#f4f6ce; height: 60px; margin-top: 0px; width: 95%; margin-left: 28px;">
      <div style="text-align: left; display: inline-flex; ">
        <span style="font-weight: bold; margin-top: 10px; margin-left: 20px; font-size: 14px;">系统模式评价结果</span>
        <el-button
          type="info"
          plain
          style="margin-left: 740px; height: 25px; margin-top: 10px; font-size: 13px;"
        >保存配置到自定义模式
        </el-button>
        <el-button
          type="info"
          plain
          style="margin-left: 10px; height: 25px; margin-top: 10px; font-size: 13px;"
        >下载查找结果
        </el-button>
      </div>
      <div style="text-align: left;  margin-top: 0px; margin-left: 20px; font-size: 12px;">使用系统提供模式进行相似性查找，对结果的未来一段时间内行情趋势进行统计分析</div>
    </div>

    <el-table :data="resultData" border style="width: 95%; margin-left: 28px; margin-top: 5px;" stripe class="result-table" 
    :cell-style="{ textAlign: 'center' }" :header-cell-style="{ textAlign: 'center' }">
      <el-table-column label="查找类型" prop="searchType" width="100px"></el-table-column>
      <el-table-column label="相似结果/个" prop="searchCount" width="100px"></el-table-column>
        <el-table-column label="趋势考察区间" width="150">
          <template #default="{ row }">
            <el-select v-model="row.futureTime" placeholder="请选择考察区间" @change="handleSelectChange(row)" style="width: 120px; margin-left: 5px;">
              <el-option label="未来三天" value="3" />
              <el-option label="未来五天" value="5" />
              <el-option label="未来十天" value="10" />
              <el-option label="未来一个月" value="30" />
              <el-option label="自定义时间/天" value="custom" />
            </el-select>
            <!-- 自定义时间输入框 -->
            <el-input v-if="row.showCustomInput" v-model="row.customDays" placeholder="请输入天数" 
              type="number" @blur="handleCustomInput(row)" class="mt-2 w-48" />
          </template>
        </el-table-column>
        <!--上升幅度最大的区间-->
        <el-table-column label="最大涨幅" width="260">
          <el-table-column prop="stockIncrease" label="个股" width="80">
            <template #default="{ row }">
              <el-tag :type="getTagType(row.stockIncrease)">{{ row.stockIncrease }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="indexIncrease" label="交易所指数" width="100">
            <template #default="{ row }">
              <el-tag :type="getTagType(row.indexIncrease)">{{ row.indexIncrease }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="industryIncrease" label="行业指数" width="80">
            <template #default="{ row }">
              <el-tag :type="getTagType(row.industryIncrease)">{{ row.industryIncrease }}%</el-tag>
            </template>
          </el-table-column>
        </el-table-column>
        <!--下降幅度最大的区间-->
        <el-table-column label="最大跌幅" width="260">
          <el-table-column prop="stockIncrease" label="个股" width="80">
            <template #default="{ row }">
              <el-tag :type="getTagType1(row.stockIncrease)">{{ row.stockIncrease }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="indexIncrease" label="交易所指数" width="100">
            <template #default="{ row }">
              <el-tag :type="getTagType1(row.indexIncrease)">{{ row.indexIncrease }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="industryIncrease" label="行业指数" width="80">
            <template #default="{ row }">
              <el-tag :type="getTagType1(row.industryIncrease)">{{ row.industryIncrease }}%</el-tag>
            </template>
          </el-table-column>
        </el-table-column>
        <!-- 未来表现比例 - 饼状图 -->
        <el-table-column label="未来表现比例" width="150px">
          <template #default="{ $index }">
            <div :ref="(el) => setChartRef1(el, $index, 0)" style="width: 100px; height: 100px; margin-top: -5px; margin-bottom: -5px; margin-left: 20px;"></div>
          </template>
        </el-table-column>
        <el-table-column label="综合评分" prop="score"></el-table-column>
      </el-table>


    <!--结果详情展示-->
    <div style="text-align: left; margin-top: 40px; background-color:aliceblue; height: 30px; margin-top: 5px; display: inline-flex; width: 95%; margin-left: -5px;">
      <span style="font-weight: bold; margin-top: 5px; margin-left: 20px; font-size: 14px;">模式相似性查找结果详情（见下表）</span>
    </div>

    <el-table :data="tableData" border style="width: 95%; margin-left: 28px; margin-top: 5px;" stripe class="result-table" 
      :cell-style="{ textAlign: 'center' }" :header-cell-style="{ textAlign: 'center' }">
      <el-table-column fixed label="股票名称" prop="stockName" width="120px"></el-table-column>
      <el-table-column fixed label="股票代码" prop="stockCode" width="120px"></el-table-column>
      <el-table-column label="股票来源" prop="stockFrom" width="120px"></el-table-column>
      <el-table-column label="起始时间" prop="startDate"  width="120px"></el-table-column>
      <el-table-column label="终止时间" prop="endDate"  width="120px"></el-table-column>
      <el-table-column label="模式目标检测结果" width="300px">
        <template #default="{ row }">
          <div style="width: 180px; height: 200px; margin-top: -20px; margin-bottom: -30px; display: flex; justify-content: center; align-items: center;">
            <img 
              v-if="row.imagePath"
              :src="row.imagePath" 
              alt="检测结果图片" 
              style="max-width: 180px; max-height: 100%; object-fit: contain; margin-left: 40px;"
            >
          </div>
        </template>
      </el-table-column>
      <el-table-column fixed label="检测类别" prop="stockType" width="120px"></el-table-column>
      <el-table-column label="相似度" prop="similarity" ></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, toRaw, reactive } from 'vue';
import { useStore } from "vuex";
import * as echarts from 'echarts';

const store = useStore();

// 根据涨幅正负设置标签样式
const getTagType = (value) => {
  return value < 0 ? 'success' : value > 0 ? 'danger' : 'info'
}

// 根据涨幅正负设置标签样式
const getTagType1 = (value) => {
  return value > 0 ? 'success' : value < 0 ? 'danger' : 'info'
}

const setChartRef1 = (el, rowIndex, colIndex) => {
  if (el) {
    nextTick(() => {
      initChart1(el, rowIndex)
    })
  }
}

const initChart1 = (el, rowIndex) => {
  const chart = echarts.init(el)
  const data = resultData.value[rowIndex].riseFallRatio
  const option = {
    series: [
      {
        name: '涨跌比例',
        type: 'pie',
        radius: ['30%', '80%'],
        avoidLabelOverlap: true, // 开启标签重叠避免
        label: {
          show: true,
          position: 'inside', // 标签放在饼图内部
          formatter: '{b}\n{c}%', // 名称和百分比分行显示
          fontSize: 11,
          color: '#fff', // 白色文字，确保在深色区域可见
          backgroundColor: 'transparent', // 透明背景
          fontWeight: 'bold'
        },
        labelLine: {
          show: false // 不显示指示线
        },
        data: [
          { value: data[0], name: '跌', itemStyle: { color: '#10b981' } }, // 绿色
          { value: data[1], name: '涨', itemStyle: { color: '#ef4444' } }  // 红色
        ]
      }
    ]
  }
  chart.setOption(option)
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

const dataObjects = ref([]);
const dataObjects2 = ref([
  {
    searchType: '', // 模式没有历史查找
    searchCount: 0,
    futureTime: '3',
    showCustomInput: false,
    customDays: '',
    stockIncrease: 5.2,
    indexIncrease: 2.1,
    industryIncrease: 3.8,
    score: 85,
    riseFallRatio: [65, 35] // 上涨65%，下跌35%
  }
])

// 处理选择器变化
const handleSelectChange = (row) => {
  row.showCustomInput = false
  row.customDays = ''
  if (row.futureTime === 'custom') {
    row.showCustomInput = true
  }
  console.log(`用户选择了: ${row.futureTime}`)
}

// 处理自定义时间输入
const handleCustomInput = (row) => {
  if (row.customDays && !isNaN(Number(row.customDays))) {
    row.futureTime = Number(row.customDays)
    console.log(`用户自定义时间: ${row.futureTime}天`)
  } else {
    row.futureTime = '3' // 默认恢复为3天
    row.customDays = ''
    console.log('输入无效，恢复默认值')
  }
}

// 监听store中的resultList变化
watch(() => store.state.resultList, (newValue) => {
  updateTableData(newValue);
}, { deep: true });

// 提取为独立函数以便在多处调用
const updateTableData = (resultList) => {
  if (!resultList || !Object.keys(resultList).length) {
    console.log('结果列表为空，不更新表格数据');
    return;
  }
  
  console.log('更新表格数据:', resultList);
  
  // 创建新的数据数组，避免直接修改响应式对象
  const newDataObjects = [];
  let totalSearchCount = 0;

  for (const stockCode in resultList) {
    if (resultList.hasOwnProperty(stockCode)) {
      console.log("处理股票代码:", stockCode);
      // 获取该股票的所有相似区间数据
      const intervals = resultList[stockCode];
      totalSearchCount += intervals.length;

      // 遍历每个相似区间
      intervals.forEach((interval) => {
        const stock = store.state.stockList.find(stock => stock.code === stockCode.slice(0, 6));
        const newData = {
          stockName: stock ? stock.name : '未知股票',
          stockCode: stockCode.slice(0, 6),
          stockFrom: '系统模式',
          startDate: interval.start,
          endDate: interval.end,
          imagePath: '',
          stockType: '多头排列类2',
          similarity: 1
        };

        let imagePath = interval.chart_path;
        if (imagePath) {
          // 使用API代理 (推荐)
          const fileName = imagePath.split(/[\\/]/).pop();
          imagePath = `/detect_result/${fileName}`;
        }
        newData.imagePath = imagePath;

        newDataObjects.push(newData);
      });
    }
  }

  // 创建新的统计数据对象
  const newResultData = [{
    searchType: '多股票横向查找',
    searchCount: totalSearchCount,
    futureTime: '10',
    showCustomInput: false,
    customDays: '',
    stockIncrease: 5.2,
    indexIncrease: 2.1,
    industryIncrease: 3.8,
    score: 85,
    riseFallRatio: [65, 35]
  }];

  // 使用nextTick确保DOM更新完成后执行
  nextTick(() => {
    // 一次性更新所有数据，触发组件重新渲染
    dataObjects.value = newDataObjects;
    resultData.value = newResultData;
    
    // 重置表格引用
    chartRefs.value = Array(newDataObjects.length * 3).fill(null);
    
    console.log('表格数据已更新');
  });
};

// 页面加载时检查是否已有数据
onMounted(() => {
  if (store.state.resultList && Object.keys(store.state.resultList).length > 0) {
    updateTableData(store.state.resultList);
  }
});

// 监听API调用的相关状态
watch(() => store.state.baseInfo.isMode && store.state.baseInfo.isCross && store.state.modeInfo.index === "BA2", (newValue) => {
  if (newValue) {
    console.log('检测条件满足，等待API结果...');
  }
});

const tableData = ref([]);
const resultData = ref(dataObjects2.value);
const chartRefs = ref(Array(dataObjects.value.length * 3).fill(null));

// 监听dataObjects变化，更新表格数据
watch(dataObjects, (newValue) => {
  tableData.value = newValue;
});

const setChartRef = (el, rowIndex, colIndex) => {
  const index = rowIndex * 4 + colIndex;
  chartRefs.value[index] = el;
  if (el) {
    initChart(index, rowIndex, colIndex);
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
      } else if (colIndex === 2) {
        chartData = dataObjects.value[rowIndex].chartData3;
      } else if (colIndex === 3) {
        chartData = dataObjects.value[rowIndex].chartData4;
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
        legend: {
          data: ['MA4', 'MA12', 'MA20'],
          top: '20%',
          left: 'left',
          orient: 'vertical',
          itemWidth: 8,
          itemHeight: 8,
          iconSize: 8,
          textStyle: {
            color: '#000',
            fontSize: 9
          }
        },
        series: [
          {
            name: 'MA4',
            data: chartData[0],
            type: 'line',
            lineStyle: { width: 1 },// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA12',
            data: chartData[1],
            type: 'line',
            lineStyle: { width: 1 },// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          },
          {
            name: 'MA20',
            data: chartData[2],
            type: 'line',
            lineStyle: { width: 1 },// 减小曲线粗细
            showSymbol: false // 新增配置，去掉数据圆点
          }
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
</script>

<style scoped>
/* 可根据需要添加样式 */
.result-table {
  margin-left: 30px;
  margin-top: 20px;
}
</style>