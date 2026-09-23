 <!-- 
  选择待查找股票集合组件 
  -->
<template>
  <div id="dialog-page">
    <el-dialog
      :model-value="visible"
      @update:model-value="onUpdateVisible"
      :title="多头排列表格测试"
      width=850px
      :before-close="handleClose"
      style="margin-top: 60px;"
      class="modecards-dialog-tour"
    >
      <span>多头排列模式</span>
      <hr />

      <!-- 多头排列基本信息表格 -->
      <div>
        <el-table :data="tableData" stripe border style="font-size: 13px; text-align: center;">
          <el-table-column prop="name" label="模式名称" width="100" >多头排列</el-table-column>
          <el-table-column prop="code" label="模式代码" width="85" >BA</el-table-column>
          <el-table-column prop="ma" label="默认均线系统" width="180" >MA4，MA8，MA12，MA16，MA20，MA47</el-table-column>
          <el-table-column prop="desc" label="模式定义" width="250" >多头排列是指短期均线在中期均线之上，且中期均线在长期均线之上，形成多头排列的形态。</el-table-column>
          <el-table-column prop="class" label="模式类型" width="100" >持续形态</el-table-column>
          <el-table-column prop="minDays" label="查找区间/天" width="100">10</el-table-column>
        </el-table>
      </div>
      <div style="font-size: 13px; color:#000000; padding: 1px; width: 830px; margin-left: 0px; margin-top: 10px;">——————————————— 类别数据设置 ————————————————</div>

      <!-- 数据分类设置区 -->
      <div style="margin-top: 10px; width: 815px; display: flex;">
        <div class="card-group">
          <el-card
            v-for="item in cardList"
            :key="item.id"
            :class="{'is-active': currentCard === item.id}"
            style="width: 50px; height: 120px; font-size: 12px; cursor: pointer; font-weight: bold;"
            shadow="hover"
            @click="handleCardClick(item.id)"
          >
            {{ item.label }}
          </el-card>
        </div>
        <div class="scrollable-div" style="border: #d6d6d6 1px solid; width: 815px; height: 305px; margin-left: 10px; padding: 10px; overflow-y: auto; border-radius: 4px;">
          <div v-if="currentCard === 1">
            <span style="font-size: 13px; margin-left: -352px;"> 默认分类：基于默认聚类方法得到分类结果，类别预览如下所示</span>
            <!-- 写一个只有一行的表格，表头是【分类1、分类2】，表格内容是两张图片 -->
            <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 5px; " class="custom-table-header"
            >
              <el-table-column label="分类1" width="365px">
                <template #default="{ row }">
                  <img :src="row.imagePath1" alt="分类1图片" style="width: 340px; height: 190px; margin-left: -10px;">
                </template>
              </el-table-column>
              <el-table-column label="分类2" width="365px">
                <template #default="{ row }">
                  <img :src="row.imagePath2" alt="分类2图片" style="width: 340px; height: 190px; margin-left: -10px;">
                </template>
              </el-table-column>
            </el-table>

            <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 5px; " class="custom-table-header"
            >
              <el-table-column label="分类3" width="365px">
                <template #default="{ row }">
                  <img :src="row.imagePath3" alt="分类1图片" style="width: 340px; height: 190px; margin-left: -10px;">
                </template>
              </el-table-column>
              <el-table-column label="分类4" width="365px">
                <template #default="{ row }">
                  <img :src="row.imagePath4" alt="分类2图片" style="width: 340px; height: 190px; margin-left: -10px;">
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-if="currentCard === 2">
            <span style="font-size: 12px;"> 自定义分类：手动定义分类结果</span>
          </div>
          
        </div>
      </div>
      <template #footer>
        <div style="margin-top: 10px;">
          <el-button @click="onUpdateVisible(false)">Cancel</el-button>
          <el-button type="primary" @click="onConfirm" class="apply-mode-btn">
            Confirm
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { ref} from "vue";

import { useStore } from "vuex";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  dialogTitle: {
    type: String,
    default: "选择待查找股票集合",
  },
  dialogWidth: {
    type: [String, Number],
    default: "700",
  },
});

const emit = defineEmits(["close", "update:model-value"]);

const store = useStore();

const tableData = [
  {}
];
const tableData1 = [
  {
    imagePath1: '/stage1.png',
    imagePath2: '/stage3.png',
    imagePath3: '/stage2.png',
    imagePath4: '/stage4.png',
  }
];

const cardList = [
  { id: 1, label: '默认\n分类' }, 
  { id: 2, label: '自定义\n分类' }
]

// 默认选中第一个卡片
const currentCard = ref(1)

// 点击卡片时更新选中状态
const handleCardClick = (id) => {
  currentCard.value = id
}

const handleClose = (done) => {
  done();
  emit("close");
  emit("update:model-value", false);
};

const onUpdateVisible = (newValue) => {
  emit("close");
  emit("update:model-value", false);
};

// 新增：自动全选逻辑
const tableRefs = {
  3: ref(null),
  4: ref(null),
  5: ref(null)
};


// 查找方式切换
const searchMode = ref('multi'); // multi: 多股票对比查找, history: 本股票历史行情查找
const dateRange = ref([new Date('2016-01-02'), new Date('2016-06-20')]);

const searchInfo = store.state.searchInfo;
const onConfirm = () => {
  let selectedRows = [];
  if (searchMode.value === 'multi') {
    Object.values(tableRefs).forEach(tableRef => {
      const table = tableRef.value;
      if (table) {
        // 使用 getSelectionRows 方法获取选中的行
        selectedRows = selectedRows.concat(table.getSelectionRows()); 
        console.log("---------------------------------------------------");
        console.log(selectedRows);
      }
    });

  }
  const startDate = dateRange.value[0];
  const endDate = dateRange.value[1];
  searchInfo.searchStartDate = startDate;
  searchInfo.searchEndDate = endDate;
  searchInfo.stockList = selectedRows;
  console.log(searchInfo.stockList);
  onUpdateVisible(false);
};
</script>

<style scoped>
.card-group {
  gap: 10px;
}

.is-active {
  background-color: #81bfff;
  color: var(--el-color-white);
}

/* 使用/deep/或::v-deep选择器穿透scoped样式 */
.custom-table-header .el-table__header th {
  background-color: #f5f7fa !important;
  text-align: center;
height: 10px !important;
}

/* 或者使用::v-deep (Vue 3) */
::v-deep .custom-table-header .el-table__header th {
  background-color: #f5f7fa !important;
  text-align: center !important;
  font-size: 12px !important;
  
}

</style>    