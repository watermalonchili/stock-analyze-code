<!--
  页面说明：
  本页面用于展示【基准股票模式评价】的结果，包括结果表格和每条结果的均线图，支持保存配置和下载结果等操作。
-->
<template>
  <div id="app">
    <!--展示模式分析结果的表格-->
    <div style="text-align: left; margin-top: 20px; background-color:#ffe9e9; height: 60px; margin-top: 0px; width: 95%; margin-left: 28px;">
      <div style="text-align: left; display: inline-flex; ">
        <span style="font-weight: bold; margin-top: 10px; margin-left: 20px; font-size: 14px;">模式选股结果</span>
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
      <div style="text-align: left;  margin-top: 0px; margin-left: 20px; font-size: 12px; margin-bottom: 10px;">根据近期内均线系统是否有可能表现出所选模式，筛选出符合条件的股票</div>
    </div>

    <el-table :data="resultData" border style="width: 95%; margin-left: 28px; margin-top: 5px;" stripe class="result-table" 
    :cell-style="{ textAlign: 'center' }" :header-cell-style="{ textAlign: 'center' }">
<el-table-column label="选股模式" prop="searchType" width="100px"></el-table-column>
      <el-table-column label="选股结果数" prop="searchCount" width="95px"></el-table-column>
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
      <el-table-column label="平均收益率(N日)" prop="futureIncome" width="95px"></el-table-column>
      <el-table-column label="最大回撤幅度(N日)" prop="maxRange" width="115px"></el-table-column>
      <el-table-column label="最大波动率(N日)" prop="maxRate" width="100px"></el-table-column>
        <!--上升幅度最大的区间-->
        <el-table-column label="最大涨幅(N日)" prop="stockIncrease" width="90"></el-table-column>
        <!--下降幅度最大的区间-->
        <el-table-column label="最大跌幅(N日)" prop="stockDecrease" width="90"></el-table-column>
        <!-- 未来表现比例 - 饼状图 -->
        <el-table-column label="后续N日胜率比例" width="200px">
          <template #default="{ $index }">
            <div :ref="(el) => setChartRef1(el, $index, 0)" style="width: 100px; height: 100px; margin-top: -5px; margin-bottom: -5px; margin-left:40px;"></div>
          </template>
        </el-table-column>
        <el-table-column label="综合评分" prop="score"></el-table-column>
      </el-table>

    <div style="text-align: left; margin-top: 40px; background-color:#ffe9e9; height: 30px; margin-top: 5px; display: inline-flex; width: 95%; margin-left: -5px;">
      <span style="font-weight: bold; margin-top: 5px; margin-left: 20px; font-size: 14px;">模式选股结果详情（见下表）</span>
    </div>

    <el-table :data="tableData" border style="width: 95%; margin-left: 28px; margin-top: 5px;" stripe class="result-table" 
      :cell-style="{ textAlign: 'center' }" :header-cell-style="{ textAlign: 'center' }">
      <el-table-column fixed label="股票名称" prop="stockName" width="100px"></el-table-column>
      <el-table-column fixed label="股票代码" prop="stockCode" width="100px"></el-table-column>
      <el-table-column label="股票来源" prop="stockFrom" width="100px"></el-table-column>
      <el-table-column label="股票近期表现" width="210px">
        <template #default="{ $index }">
          <div :ref="(el) => setChartRef(el, $index, 0)" style="width: 180px; height: 200px; margin-top: -20px; margin-bottom: -30px;"></div>
        </template>
      </el-table-column>
      <el-table-column label="SH/SZ指数近期表现" width="210px">
        <template #default="{ $index }">
          <div :ref="(el) => setChartRef(el, $index, 1)" style="width: 180px; height: 200px; margin-top: -20px; margin-bottom: -30px;"></div>
        </template>
      </el-table-column>
      <el-table-column label="行业近期表现" width="210px">
        <template #default="{ $index }">
          <div :ref="(el) => setChartRef(el, $index, 2)" style="width: 180px; height: 200px; margin-top: -20px; margin-bottom: -30px;"></div>
        </template>
      </el-table-column>
      <el-table-column fixed label="预测分类" prop="stockType" width="120px"></el-table-column>
      <el-table-column label="预测概率" prop="similarity" ></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch,toRaw  } from 'vue';
import { useStore } from "vuex";
import * as echarts from 'echarts';

const store = useStore();

const dataObjects = ref([
  {
    stockName: '奥士康',
    stockCode: '002913',
    stockFrom: '自选股',
    stockType: '多头排列类1',
    startDate: '',
    endDate: '',
    chartData: [
    ],
    chartData2: [
    ],
    chartData3: [
    ],
    chartData4: [
    ],
    dates:[],
    similarity: 0.89
  }, 
  {
    stockName: '汉王科技',
    stockCode: '002362',
    stockFrom: '自选股',
    stockType: '多头排列类2',
    startDate: '',
    endDate: '',
    chartData: [
    ],
    chartData2: [
    ],
    chartData3: [
    ],
    chartData4: [
    ],
    dates:[],
    similarity: 0.82
  },
    {
    stockName: '远望谷',
    stockCode: '002161',
    stockFrom: '自选股',
    stockType: '多头排列类1',
    startDate: '',
    endDate: '',
    chartData: [
    ],
    chartData2: [
    ],
    chartData3: [
    ],
    chartData4: [
    ],
    dates:[],
    similarity: 0.8
  },
  {
    stockName: '康强电子',
    stockCode: '002119',
    stockFrom: '自选股',
    stockType: '多头排列类2',
    startDate: '',
    endDate: '',
    chartData: [
    ],
    chartData2: [
    ],
    chartData3: [
    ],
    chartData4: [
    ],
    dates:[],
    similarity: 0.75
  }
]);
const dataObjects2 = ref([
  {
    searchType: '历史查找',
    searchCount: 10,
    futureTime: '2023-10-01',
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

// 传入的是股票基准模式的数据
watch(() => store.state.resultList2, (newValue) => {

    console.log("接收结果数据-------------------",toRaw(newValue))
    const rawData = toRaw(newValue)
    for (const stockCode in rawData) {
      if (rawData.hasOwnProperty(stockCode)) {
        console.log("股票代码:", stockCode);
        // 获取该股票的所有相似区间数据
        const intervals = rawData[stockCode];
        
        // 遍历每个相似区间
        intervals.forEach((interval, index) => {
            dataObjects.value[index].stockCode = stockCode.slice(0,6);
            const stock = store.state.stockList.find(stock => stock.code === stockCode.slice(0,6));
            dataObjects.value[index].stockName = stock ? stock.name : '未知股票';
            const ma_values1 = transposeArray(interval.ma_values);
            const index_values = transposeArray(interval.index_ma_values);
            dataObjects.value[index].chartData = ma_values1;
            dataObjects.value[index].chartData2 = index_values;
            dataObjects.value[index].similarity = interval.similarity.toFixed(6);
            dataObjects.value[index].startDate = interval.start_date;
            dataObjects.value[index].endDate = interval.end_date;
            dataObjects.value[index].stockFrom = '基准股票';
            dataObjects.value[index].dates = interval.x_axis_dates;
        });
      }
    }
  },
  { deep: true } // 若 resultList 是对象或数组，需要深度监听
);

// 传入的是推荐模式的结果数据
watch(() => store.state.resultList, (newValue) => {
    const rawData = toRaw(newValue);
    console.log(rawData[0]) 
    dataObjects.value.forEach((item, index) => {
      const dateRange = rawData[index].interval;
    
      // 表格中展示的查找结果数据
      console.log(store.state.searchInfo.stockList[0])
      const code = store.state.searchInfo.stockList[0].code;
      const name = store.state.searchInfo.stockList[0].name;
      item.stockFrom = store.state.searchInfo.stockList[0].from;
      item.stockCode = code;
      // 在stockList中查找对应的股票名称
      const stock = store.state.stockList.find(stock => stock.code === item.stockCode);
      item.stockName = stock ? stock.name : '未知股票';
      item.startDate = dateRange[0];
      item.endDate = dateRange[dateRange.length - 1];

      const dates = rawData[index].ma_data.map(item => item[0]);
      const ma_values = rawData[index].ma_data.map(item => item.slice(1));

      const ma_values1 = transposeArray(ma_values);
      item.chartData = ma_values1;
      console.log(ma_values1)
      const lastFourDigits = dates.map(date => date.slice(-4));
      item.dates = lastFourDigits;
      console.log(dates)
    });
  },
  { deep: true } // 若 resultList 是对象或数组，需要深度监听
);

const tableData = ref(dataObjects.value);
const resultData = ref(dataObjects2.value);
const chartRefs = ref(Array(dataObjects.value.length * 3).fill(null));

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
      } else if(colIndex === 3){
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
          top: '20%' ,
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