<template>
  <div id="dialog-page">
    <!-- 修改为 v-bind 和 v-on 的形式 -->
    <el-dialog
      :model-value="visible"
      @update:model-value="onUpdateVisible"
      :title="dialogTitle"
      :width="dialogWidth"
      :before-close="handleClose"
      class="choose-dialog-tour"
    >
      <span>选择待查找的股票集合</span>
      <hr />

      <!-- 查找方式切换和时间范围选择 -->
      <div class="dialog-content-step1" style="display: flex; align-items: center; margin-bottom: 10px; margin-top: 10px;">
        <el-radio-group v-model="searchMode" size="small">
          <el-radio-button label="multi" class="multi-radio-btn">多股票对比查找</el-radio-button>
          <el-radio-button label="history" class="history-radio-btn">本股票历史行情查找</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          style="margin-left: 20px; width: 260px;"
          @change="handleDateChange"
        />
      </div>

      <!-- 查找内容区域 -->
      <div v-if="searchMode === 'multi'">
        <!-- 原有三种模式查找设置 -->
        <div style="height: 300px; display: inline-flex">
          <el-collapse
            accordion
            v-model="activeNames"
            @change="handleChange"
            style="width: 600px; margin-left: 15px; margin-top: 5px"
          >
            <el-collapse-item :name="3">
              <template #title>
                <el-checkbox v-model="checkedItems[3]" @change="val => handleSelectAll(val, 3)">我的自选</el-checkbox>
              </template>
              <div style="height: 100px; overflow-y: auto">
                <el-table :ref="el => tableRefs[3].value = el" :data="tableData" @selection-change="val => handleSelectionChange(val, 3)">
                  <el-table-column
                    type="selection"
                    :selectable="selectable"
                    width="55"
                  />
                  <el-table-column prop="name" label="name"></el-table-column>
                  <el-table-column prop="code" label="code"></el-table-column>
                  <el-table-column prop="from" label="from">自选股票</el-table-column>
                </el-table>
              </div>
            </el-collapse-item>
            <el-collapse-item :name="4">
              <template #title>
                <el-checkbox v-model="checkedItems[4]" @change="val => handleSelectAll(val, 4)">同板块</el-checkbox>
              </template>
              <div style="height: 100px; overflow-y: auto">
                <el-table :ref="el => tableRefs[4].value = el" :data="tableData" @selection-change="val => handleSelectionChange(val, 4)">
                  <el-table-column
                    type="selection"
                    :selectable="selectable"
                    width="55"
                  />
                  <el-table-column prop="name" label="name"></el-table-column>
                  <el-table-column prop="code" label="code"></el-table-column>
                  <el-table-column prop="from" label="from">同板块</el-table-column>
                </el-table>
              </div>
            </el-collapse-item>
            <el-collapse-item :name="5">
              <template #title>
                <el-checkbox v-model="checkedItems[5]" @change="val => handleSelectAll(val, 5)">同行业</el-checkbox>
              </template>
              <div style="height: 100px; overflow-y: auto">
                <el-table :ref="el => tableRefs[5].value = el" :data="tableData" @selection-change="val => handleSelectionChange(val, 5)">
                  <el-table-column
                    type="selection"
                    :selectable="selectable"
                    width="55"
                  />
                  <el-table-column prop="name" label="name"></el-table-column>
                  <el-table-column prop="code" label="code"></el-table-column>
                  <el-table-column prop="from" label="from">同行业</el-table-column>
                </el-table>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
      <div v-else>
        <!-- 本股票历史行情查找设置，可扩展 -->
        <div style="margin-bottom: 10px; color: #666;">可查找本股票在不同历史区间的行情表现</div>
      </div>

      <!-- 推荐模式/自定义模式卡片滑动区 -->
      <div style="margin-top: 20px; width: 100%; display: flex; justify-content: center;">
        <el-carousel height="200px" indicator-position="outside" arrow="always" style="width: 600px;">
          <!--根据searchMode确定是本股票历史查找还是多股票对比-->
          <el-carousel-item v-for="(item, idx) in (searchMode === 'multi' ? multiResultList : historyResultList)" :key="idx">
            <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center;">
              <div style="font-weight: bold; font-size: 18px;">{{ item.title }}</div>
              <div style="margin-top: 10px; color: #888;">{{ item.desc }}</div>
              <div style="margin-top: 10px; color: #333;">股票代码：{{ item.code }}</div>
            </div>
          </el-carousel-item>
        </el-carousel>
      </div>

      <template #footer>
        
        <div class="dialog-footer">
          <el-button @click="onUpdateVisible(false)">Cancel</el-button>
          <el-button type="primary" @click="onConfirm" class="apply-mode-btn btn-search-range-1">
            Confirm
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { nextTick, ref, onMounted, watch, computed } from "vue";

import { useStore } from "vuex";
import { ElMessageBox } from "element-plus";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  dialogTitle: {
    type: String,
    default: "查找范围设置",
  },
  dialogWidth: {
    type: [String, Number],
    default: "700",
  },
});

const emit = defineEmits(["close", "update:model-value"]);

const activeNames = ref([]);
const checkedItems = ref({
  1: false,
  2: false,
  3: false,
  4: false,
  5: false,
});

const store = useStore();

const tableData = [
  { code: '000021', name: "深科技", from:"自选股票" },
  { code: "210395", name: "恒大地产",from:"自选股票"},
  { code: "210396", name: "恒大汽车",from:"自选股票" },
  { code: "210397", name: "恒大科技",from:"自选股票" },
  { code: "210398", name: "恒大金融",from:"自选股票" },
];

const selectable = (row, index) => {
  return true;
};

const handleChange = (value) => {
  console.log(value);
};

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

function handleSelectAll(val, idx) {
  nextTick(() => {
    const table = tableRefs[idx].value;
    if (table) {
      if (val) {
        table.clearSelection();
        tableData.forEach(row => table.toggleRowSelection(row, true));
      } else {
        table.clearSelection();
      }
    }
  });
}

function handleSelectionChange(val, idx) {
  // 可根据需要处理选中项变化
}

// 查找方式切换
const searchMode = ref('multi'); // multi: 多股票对比查找, history: 本股票历史行情查找
const dateRange = ref([new Date('2016-01-02'), new Date('2016-06-20')]);

// 多股票对比查找结果示例
const multiResultList = ref([
  { title: '推荐模式A', desc: '多股票对比结果A', code: '000001' },
  { title: '推荐模式B', desc: '多股票对比结果B', code: '000002' },
  { title: '自定义模式C', desc: '多股票对比结果C', code: '000003' },
]);
// 本股票历史行情查找结果示例
const historyResultList = ref([
  { title: '历史区间1', desc: '本股票2018-2020年行情', code: '000021' },
  { title: '历史区间2', desc: '本股票2020-2022年行情', code: '000021' },
]);

const handleDateChange = (value) => {
  // 处理日期范围变化
};

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
/* 可以在这里添加子组件的样式 */
</style>    