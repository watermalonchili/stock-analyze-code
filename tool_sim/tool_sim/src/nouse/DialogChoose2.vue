 <!-- 
  选择待查找股票集合组件 
  -->
<template>
  <div id="dialog-page">
    <!-- 修改为 v-bind 和 v-on 的形式 -->
    <el-dialog
      :model-value="visible"
      @update:model-value="onUpdateVisible"
      :title="dialogTitle"
      :width="dialogWidth"
      :before-close="handleClose"
      style="margin-top: 60px;"
    >
      
      <hr />
      <span>在下列表格中选择参与横向查找的股票集合</span>

      <!-- 查找内容区域 -->
      <div>
        <!-- 原有三种模式查找设置 -->
        <div style="height: 400px; display: inline-flex; margin-top: 20px;">
          <el-collapse
            accordion
            v-model="activeNames"
            @change="handleChange"
            style="width: 550px; margin-left: 15px; margin-top: 5px"
          >
            <el-collapse-item :name="3">
              <template #title>
                <el-checkbox v-model="checkedItems[3]" @change="val => handleSelectAll(val, 3)">我的自选</el-checkbox>
              </template>
              <div style="height: 160px; overflow-y: auto">
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
              <div style="height: 160px; overflow-y: auto">
                <el-table :ref="el => tableRefs[4].value = el" :data="tableData2" @selection-change="val => handleSelectionChange(val, 4)">
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
              <div style="height: 160px; overflow-y: auto">
                <el-table :ref="el => tableRefs[5].value = el" :data="tableData3" @selection-change="val => handleSelectionChange(val, 5)">
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

      <!-- 推荐模式/自定义模式卡片滑动区 -->
      <template #footer>
        <div style="margin-top: -48px;">
          <el-button @click="onUpdateVisible(false)">取消</el-button>
          <el-button type="primary" @click="onConfirm" class="apply-mode-btn">
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { nextTick, ref} from "vue";

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
    default: "650",
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
  { code: '002484', name: "江海股份", from:"自选股票" },
  { code: "002528", name: "ST英飞拓",from:"自选股票"},
  { code: "002655", name: "共达电声",from:"自选股票" },
  { code: "002759", name: "天际股份",from:"自选股票" },
  { code: '300088', name: "长信科技", from:"自选股票" },
  { code: "300109", name: "新开源",from:"自选股票"},
  { code: "300610", name: "晨化股份",from:"自选股票" },
  { code: "300641", name: "正丹股份",from:"自选股票" },
];


const tableData2 = [
  { code: "002092", name: "ST中泰", from: "同板块" },
  { code: "002106", name: "莱宝高科", from: "同板块" },
  { code: "002119", name: "康强电子", from: "同板块" },
  { code: "002134", name: "天津普林", from: "同板块" },
  { code: "600378", name: "昊华科技", from: "同板块" },
  { code: "600389", name: "江山股份", from: "同板块" },
  { code: "600409", name: "三友化工", from: "同板块" },
  { code: "600435", name: "北方导航", from: "同板块" },
];

const tableData3 = [
  { code: "001255", name: "博菲电气", from: "同行业" },
  { code: "001308", name: "康冠科技", from: "同行业" },
  { code: "001309", name: "德明利", from: "同行业" },
  { code: "001333", name: "光华股份", from: "同行业" },
  { code: "603052", name: "可川科技", from: "同行业" },
  { code: "603078", name: "江化微", from: "同行业" },
  { code: "603110", name: "东方材料", from: "同行业" },
  { code: "603125", name: "常青科技", from: "同行业" },
]

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
        if(idx === 3) {
          tableData.forEach(row => table.toggleRowSelection(row, true));
        } else if(idx === 4) {
          tableData2.forEach(row => table.toggleRowSelection(row, true));
        } else if(idx === 5) {
          tableData3.forEach(row => table.toggleRowSelection(row, true));
        }
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
.el-carousel__item h3 {
  color: #475669;
  opacity: 0.75;
  line-height: 200px;
  margin: 0;
  text-align: center;
}
</style>    