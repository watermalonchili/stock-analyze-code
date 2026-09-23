<template>
  <div id="current-page">
     <!-- 新手指引按钮 -->
    <div style="position: fixed; top: 70px; right: 20px; z-index: 9999; margin-top: 10px;">
      <el-dropdown trigger="hover">
        <el-button type="success" plain size="small">
          新手指引
          <i class="el-icon-arrow-down el-icon--right"></i>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="startStockTour">个股</el-dropdown-item>
            <el-dropdown-item @click="startModeTour">推荐模式</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <!-- 个股指引 -->
    <el-tour
      v-model="stockTourVisible"
      v-model:step="tourStep"
      :show-buttons="false"   
      @close="stockTourVisible = false"
      @change="handleTourChange"
    >
      <el-tour-step
        target=".btn-base-stock"
        title="STEP 1 : 设置基准股票"
        description="点击设置为基准股票按钮，选择当前要分析的个股。"
      />
      <el-tour-step
        title="STEP 2 : 进行专业配置"
        description="进行查找范围设置"
      />
      <el-tour-step
        target=".stock-mode-step2-1"
        title="STEP 2.1 : 当前功能"
        description="显示当前功能，设置为基准股票后，当前功能为个股分析，进行个股模式查找"
      />
      <el-tour-step
        target=".stock-mode-step2-2"
        title="STEP 2.2 : 基准股票名称"
        description="显示设置的基准股票名称"
      />
      <el-tour-step
        target=".stock-mode-step2"
        title="STEP 2.3 : 设置区间"
        description="选择适合的股票时间区间"
      />
      <el-tour-step
        title="STEP 3 : 选用均线类型设置"
        description="进行均线类型设置，可以选择合适均线来进一步分析"
      />
      <el-tour-step
        target=".tour-ma-config"
        title="STEP 3.1 : 配置基础MA指标"
        description="选择需要的基础MA指标。"
      />
      <el-tour-step
        target=".tour-Market-index"
        title="STEP 3.2 : 设置上证/深证指数"
        description="选择需要的上证/深证指数。"
      />
      <el-tour-step
        target=".tour-career-index"
        title="STEP 3.3 : 设置行业指数"
        description="选择需要的行业指数。"
      />
      <el-tour-step
        title="STEP 4 : 查找功能参数设置"
        description="可以进行自定义模式评价和相似模式选股"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-1"
        title="STEP 4.1 : 子功能设置"
        description="可以选择自定义模式评价和相似模式选股"
      />
      <el-tour-step
        target=".custom-evaluation-button"
        title="STEP 4.2 : 自定义模式评价"
        description="选择本股历史区间或多股票对比两种模式进行查找。"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-2-1"
        title="STEP 4.2.1 : 本股票历史行情"
        description="选择本股历史区间进行时间区间查找。"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-2-2"
        title="STEP 4.2.2 : 多股票横向查找"
        description="选择多股票横向查找模式。"
      />
      <el-tour-step
        target=".btn-search-range"
        title="STEP 4.2.2 : 选择待查找股票集"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-3"
        title="STEP 4.3 : 相似模式选股"
        description="选择相似模式选股模式。"
      />
      <el-tour-step
        target=".btn-search-range"
        title="STEP 4.3 : 请选择待查找股票集合"
        description="选择待查找股票集合。"
      />
    </el-tour>
    <!-- 推荐模式指引 -->
    <el-tour
      v-model="modeTourVisible"
      v-model:step="modeTourStep"
      @close="modeTourVisible = false"
      @change="handleModeTourChange"
      :z-index="9999"
    >
      <el-tour-step
        target=".mode-card-title"
        title="STEP 1 : 点击推荐模式名称"
        description="在推荐模式卡片中，点击你感兴趣的模式名称。"
      />
      <el-tour-step
        target=".modecards-dialog-tour .apply-mode-btn-step2"
        title="STEP 2 : 应用推荐模式"
        description="在弹窗中点击此按钮应用推荐模式。"
      />
      <el-tour-step
        target=".stock-mode-step2-1"
        title="STEP 3.1 : 当前功能"
        description="显示当前功能，设置为基准股票后，当前功能为个股分析，进行个股模式查找"
      />
      <el-tour-step
        target=".mode-card-step3-2"
        title="STEP 3.2 : 基准模式名称"
        description="显示设置的基准模式名称"
      />
      <el-tour-step
        target=".mode-card-step3-3"
        title="STEP 3.3 : 基准模式区间长度"
      />
      <el-tour-step
        target=".tour-ma-config"
        title="STEP 4.1 : 配置基础MA指标"
        description="选择需要的基础MA指标。"
      />
      <el-tour-step
        target=".tour-Market-index"
        title="STEP 4.2 : 设置上证/深证指数"
        description="选择需要的上证/深证指数。"
      />
      <el-tour-step
        target=".tour-career-index"
        title="STEP 4.3 : 设置行业指数"
        description="选择需要的行业指数。"
      />
      <el-tour-step
        title="STEP 5 : 查找功能参数设置"
        description="可以进行自定义模式评价和相似模式选股"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-1"
        title="STEP 5.1 : 子功能设置"
        description="可以选择自定义模式评价和相似模式选股"
      />
      <el-tour-step
        target=".custom-evaluation-button"
        title="STEP 5.2 : 自定义模式评价"
        description="选择本股历史区间或多股票对比两种模式进行查找。"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-2-2"
        title="STEP 5.2 : 多股票横向查找"
        description="选择多股票横向查找模式。"
      />
      <el-tour-step
        target=".btn-search-range"
        title="STEP 5.2 : 选择待查找股票集"
      />
      <el-tour-step
        target=".custom-evaluation-button-4-3"
        title="STEP 5.3 : 相似模式选股"
        description="选择相似模式选股模式。"
      />
      <el-tour-step
        target=".btn-search-range"
        title="STEP 5.3 : 请选择待查找股票集合"
        description="选择待查找股票集合。"
      />
    </el-tour>

    <div style="margin: -8px">
      <el-container class="container">
        <div class="logo">MA均线分析平台</div>
        <!--检索（代码 or 名称）-->
      </el-container>
      <el-container style="height: 94vh;">
        <el-container style="height: 100%;">
          <!--左侧股票检索部分-->
          <el-aside
            :width="sidebarWidth + 'px'"
            style=" position: relative; height: 100%; min-height: 0;"
            class="hide-scrollbar"
          >
            <!--关注股票列表-->
            <div class="scrollable-div11" style="border: #a9a9a9 0.5px solid;">
              <el-tabs
                v-model="activeName1" style="width: calc(95%); margin-left: 5px;"
              >
                <el-tab-pane label="全部股票" name="near" style="">
                  <el-input
                    v-model="searchQuery"
                    style="height: 25px; width: calc(95%); font-size: 12px;"
                    placeholder="搜索全部股票"
                  />
                  <el-table
                    :data="filteredTableData1(item)"
                    class="scrollable-div"
                    max-height="230"
                    border
                  >
                    <el-table-column
                      fixed="left"
                      label="股票名称"
                      :width="getColumnWidth(0.4)"
                      header-align="center"
                    >
                      <template #default="scope">
                        <div style="display: flex; flex-direction: column">
                          <span
                            style="font-size: 14px"
                            @click="handleRowClick(scope.row)"
                            >{{ scope.row.name }}</span
                          >
                          <span
                            style="
                              font-size: 10px;
                              color: #999;
                              margin-top: -7px;
                            ">{{ scope.row.code }}</span>
                        </div>
                      </template>
                    </el-table-column>
                    <el-table-column
                      property="ratio"
                      label="涨跌幅"
                      :width="getColumnWidth(0.3)"
                      header-align="center"
                    >
                      <template #default="scope">
                        <span style="font-size: 13px">{{
                          scope.row.ratio
                        }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column
                      property="value"
                      label="涨跌额"
                      :width="getColumnWidth(0.3)"
                      header-align="center"
                    >
                      <template #default="scope">
                        <span style="font-size: 13px">{{
                          scope.row.value
                        }}</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-tab-pane>
                <el-tab-pane label="我的自选" name="self">
                  <el-input
                    v-model="searchQuery"
                    style="height: 25px; width: calc(95%); font-size: 12px;"
                    placeholder="搜索我的自选"
                  />
                  <el-table
                    :data="filteredTableData2(item)"
                    style="
                      height: 230px;
                      font-size: 12px;
                      margin-top: 5px;
                    "
                    max-height="230"
                    border
                  >
                    <el-table-column
                      fixed="left"
                      label="股票名称"
                      :width="getColumnWidth(0.4)"
                      header-align="center"
                    >
                      <template #default="scope">
                        <div style="display: flex; flex-direction: column">
                          <span
                            style="font-size: 14px;"
                            @click="handleRowClick(scope.row)"
                          >{{ scope.row.name }}</span>
                          <span
                            style="
                              font-size: 10px;
                              color: #999;
                              margin-top: -7px;
                            "
                            >{{ scope.row.code }}</span
                          >
                        </div>
                      </template>
                    </el-table-column>
                    <el-table-column
                      property="ratio"
                      label="涨跌幅"
                      :width="getColumnWidth(0.3)"
                      header-align="center"
                    >
                      <template #default="scope">
                        <span style="font-size: 13px">{{
                          scope.row.ratio
                        }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column
                      property="value"
                      label="涨跌额"
                      :width="getColumnWidth(0.3)"
                      header-align="center"
                    >
                      <template #default="scope">
                        <span style="font-size: 13px">{{
                          scope.row.value
                        }}</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-tab-pane>
              </el-tabs>
            </div>
            <!--相似性对比设置部分-->
            <div class="div-custom" style="border: #a9a9a9 0.5px solid;">
              <div style="margin-left: 15px; margin-top: -5px">
                <div style="display: flex; margin-left: -20px;">
                  <div class="div2 stock-mode-step2-1">当前功能：</div>
                  <div class="div3 tour-mode-name">{{ store.state.baseInfo.currentFunction}}</div>
                </div>
                <!--选择用股票作为基准项，设置基准股票的时间区间-->
                <div v-if="isBaseStock" style="margin-top: 10px; margin-left: -3px;">
                  <div style="display: flex; margin-left: -4px; margin-top: -25px;">
                    <div class="div2 stock-mode-step2-2">基准股票名称：</div>
                    <div class="div3 tour-mode-name">{{store.state.modeInfo.name}}</div>
                  </div>
                  <div class="div4 stock-mode-step2" style="margin-left: 5px; width: 130px; margin-top: 5px;">基准股票时间区间设置</div>
                  <div>
                    <el-date-picker
                      v-model="value1"
                      type="daterange"
                      range-separator="To"
                      start-placeholder="Start date"
                      end-placeholder="End date"
                      size="small"
                      style="
                        width: calc(100% - 30px);
                        margin-top: 5px;
                        margin-left: -7px;
                      "
                      @change="handleDateChange"/>
                  </div>
                </div>
                <!--选择用模板作为基准项，设置模板的区间长度-->
                <div v-if="isBaseMode" style="margin-top: 10px; margin-left: -3px;">
                  <div style="display: flex; margin-left: -5px; margin-top: -20px;">
                    <div class="div2 mode-card-step3-2">基准模式名称：</div>
                    <div class="div3 tour-mode-name">{{store.state.modeInfo.name}}</div>
                  </div>
                  <div style="display: flex; margin-left: 8px; margin-top: -10px;">
                    <div class="div2 mode-card-step3-3">基准模式区间长度：</div>
                    <div class="div3 tour-mode-name">{{store.state.modeInfo.minDays}}</div>
                  </div>
                </div>

                <!--指标选择多选框-->
                <div style="font-size: 13px; font-weight: 700; color:#a9a9a9; background-color: #ededed; padding: 1px; width: 275px; margin-left: -13px; margin-top: 20px;">|    选用均线类型设置 ————————————</div>
                <div class="div5 tour-ma-config">
                  <div
                    style="
                      font-size: 13px;
                      font-weight: bold;
                      margin-left: -180px;
                      margin-top: 0px;
                    "
                  >
                    基础 MA 指标:
                  </div>
                  <el-checkbox-group
                    v-model="store.state.modeInfo.lines"
                    class="custom-checkbox-group"
                    style="margin-top: 0px"
                  >
                    <el-checkbox
                      v-for="item in maList"
                      :key="item"
                      :label="item"
                      :value="item"
                      class="custom-checkbox"
                    ></el-checkbox>
                  </el-checkbox-group>
                </div>
                <div class="div7 tour-Market-index">
                  <div
                    style="
                      font-size: 13px;
                      font-weight: bold;
                      margin-left: -180px;
                      margin-top: 6px;
                    "
                  >
                    上证/深证指数:
                  </div>
                  <el-checkbox-group
                    v-model="store.state.modeInfo.lines1"
                    class="custom-checkbox-group"
                  >
                    <el-checkbox
                      v-for="item in maList"
                      :key="item"
                      :label="item"
                      :value="item"
                      class="custom-checkbox"
                    ></el-checkbox>
                  </el-checkbox-group>
                </div>

                <div class="div7 tour-career-index">
                  <div
                    style="
                      font-size: 13px;
                      font-weight: bold;
                      margin-left: -210px;
                      margin-top: 6px;
                    "
                  >
                    行业指数:
                  </div>
                  <el-checkbox-group
                    v-model="store.state.modeInfo.lines2"
                    class="custom-checkbox-group"
                  >
                    <el-checkbox
                      v-for="item in maList"
                      :key="item"
                      :label="item"
                      :value="item"
                      class="custom-checkbox"
                    ></el-checkbox>
                  </el-checkbox-group>
                </div>
                <div style="font-size: 13px; font-weight: 700; color:#a9a9a9; background-color: #ededed; padding: 1px; width: 275px; margin-left: -13px; margin-top: 30px;">|    查找功能参数设置 ————————————</div>
                

                <div style="display: flex; margin-left: -22px; margin-top: 0px;">
                  <div class="div2 custom-evaluation-button-4-1">子功能设置：</div>
                    <el-button
                      class="custom-evaluation-button"
                      :class="{ 'is-active': baseInfo.isSection }"
                      @click="toggleButton1('isSection')"
                      style="margin-top: 15px; width: 90px; margin-left: -30px; height: 30px; font-size: 12px;"
                    >
                      自定义<br>模式评价
                    </el-button>
                    <el-button
                      class="custom-evaluation-button-4-3"
                      :class="{ 'is-active': baseInfo.isChoose }"
                      @click="toggleButton1('isChoose')"
                      style="margin-top: 15px; width: 90px; margin-left: 5px; height: 30px; font-size: 12px;"
                    >
                      相似<br>模式选股
                    </el-button>
                </div>

                <el-button
                  v-if="baseInfo.isChoose"
                  plain
                  @click="dialogVisible = true"
                  class="custom-button btn-search-range"
                  style="margin-top: 5px; width: 250px; margin-left: -20px;"
                >
                  请选择待查找股票集合
                </el-button>
                <!--Dialog-->
                <DialogChoose2
                  :visible="dialogVisible"
                  @close="dialogVisible = false"
                />

                
                <div v-if="baseInfo.isSection" style="display: flex; margin-left: -22px; margin-top: 0px;">
                  <div class="div2">查找方案：</div>
                    <el-button
                      :disabled="isDisabled"
                      class="custom-evaluation-button-4-2-1"
                      :class="{ 'is-active': baseInfo.isHistory }"
                      @click="toggleButton('isHistory')"
                      style="margin-top: 15px; width: 90px; margin-left: -30px; height: 30px; font-size: 12px;"
                    >
                      本股票<br>历史查找
                    </el-button>
                    <el-button
                      class="custom-evaluation-button-4-2-2"
                      :class="{ 'is-active': baseInfo.isCross }"
                      @click="toggleButton('isCross')"
                      style="margin-top: 15px; width: 90px; margin-left: 5px; height: 30px; font-size: 12px;"
                    >
                      多股票<br>横向查找
                    </el-button>
                </div>

                <div v-if="baseInfo.isCross" style="margin-top: 10px; margin-left: -3px;">
                  <div  style="margin-top: 10px">
                      <el-button
                        plain
                        @click="dialogVisible = true"
                        class="custom-button btn-search-range"
                        style="margin-top: 5px; width: 250px; margin-left: -20px;"
                      >
                        请选择待查找股票集
                      </el-button> 
                    <el-date-picker
                        v-model="value2"
                        type="daterange"
                        range-separator="To"
                        start-placeholder="Start date"
                        end-placeholder="End date"
                        size="small"
                        style="
                          width: calc(100% - 30px);
                          margin-top: 5px;
                          margin-left: -15px;
                        "
                        @change="handleDateChange2"
                      />
                    <!--Dialog-->
                    <DialogChoose2
                      :visible="dialogVisible"
                      @close="dialogVisible = false"
                    />
                  </div>
                </div>

                <div v-if="baseInfo.isHistory">
                  <div class="div2" style="width: 200px; margin-left: -30px;">设置查找历史时间范围：</div>
                  <el-date-picker
                        v-model="value2"
                        type="daterange"
                        range-separator="To"
                        start-placeholder="Start date"
                        end-placeholder="End date"
                        size="small"
                        style="
                          width: calc(100% - 30px);
                          margin-top: 5px;
                          margin-left: -15px;
                        "
                        @change="handleDateChange2"
                      />
                </div>
                <!--展示对比股票-->
                <el-table
                  :data="tableDataRecent"
                  class="scrollable-div"
                  max-height="200"
                  style="margin-left: -8px; margin-top: 10px;"
                  border
                >
                  <el-table-column
                    property="index"
                    fixed="left"
                    label="股票名称"
                    :width="getColumnWidth(0.5)"
                    header-align="center"
                  >
                    <template #default="scope">
                        <span style="font-size: 14px" @click="handleRowClick(scope.row)">{{ scope.row.name }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    property="code"
                    label="股票代码"
                    :width="getColumnWidth(0.5)"
                    header-align="center"
                  >
                    <template #default="scope">
                      <span style="font-size: 13px">{{ scope.row.code }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div class="my-button">
                <el-button type="primary" plain>查看配置项</el-button>
                <el-button type="primary" plain @click="getResult">生成结果</el-button>
              </div>

              <!-- 拖动条 -->
              <div class="resize-handle" @mousedown="startResize"></div>
            </div>
          </el-aside>
          <!--右侧中央均线展示部分-->
          <el-main
            style="background-color: white; padding: 0; position: relative; height: 100%; min-height: 0;"
            class="hide-scrollbar"
          >
            <!--选中股票信息展示部分-->
            <div
              style="
                display: flex;
                background-color: #f7f7f7;
                height: 80px;
                position: sticky;
                top: 0;
                z-index: 100;
                width: 100%;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
              "
            >
              <div style="display: flex; flex-direction: column; justify-content: flex-start; min-width: 900px;">
                <!-- 股票名、代码、现手等单独一行（7列） -->
                <div style="display: flex; align-items: center; padding-top: 10px;">
                  <span style="font-weight: bold; margin-left: 14px; display: inline-block;">{{ stockShowInfo.name }} </span>
                  <span style="font-weight: bold;  margin-left: 5px; display: inline-block;">({{ stockShowInfo.code }})</span>
                  <span style="margin-left: 10px; display: inline-block; font-weight: bold;" :style="{color: valueColor, 'font-weight': 'bold'}">{{ stockShowInfo.value }}</span>
                  <span style="margin-left: 2px; display: inline-block;" :style="{color: valueColor, 'font-weight': 'bold'}">↑</span>
                  <span style="margin-left: 15px; display: inline-block; font-weight: bold;" :style="{color: ratioColor, 'font-weight': 'bold'}">{{ stockShowInfo.ratio }}</span>
                  <span style="margin-left: 10px; display: inline-block;"></span>
                  <span style="margin-left: 10px; display: inline-block;">
                    <el-tooltip :content="isSelected ? '已添加' : '添加到自选'" placement="top">
                      <el-icon size="20" style="margin-top: 2px; cursor: pointer;" @click="toggleFavorite" :color="isSelected ? '#222' : '#aaa'">
                        <component :is="isSelected ? StarFilled : Star" />
                      </el-icon>
                    </el-tooltip>
                  </span>
                </div>
                <!-- 第一行标签（7列） -->
                <div style="display: flex; align-items: left; padding-top: 5px; font-size: 12px; margin-left: 7px;">
                  <span style="min-width: 90px; margin-left: 7px; display: inline-block;">日期：2025-05-23</span>
                  <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA4：19.560</span>
                  <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA8：19.959</span>
                  <span style="min-width: 90px; margin-left: 14px; display: inline-block;">MA12：19.935</span>
                  <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA16：20.054</span>
                  <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA20：20.179</span>
                  <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA47：19.899</span>
                </div>
                <!-- 第二行标签（7列） -->
                <div style="display: flex; align-items: left; padding-top: 2px; font-size: 12px; margin-left: 15px;">
                  <span style="min-width: 90px; margin-left: -15px; display: inline-block;">板块：主板</span>
                  <span style="min-width: 90px; margin-left: 6px; display: inline-block;">行业：计算机、通信和其他电子设备制造业</span>
                </div>
              </div>
              <div>
                
                <el-button
                  type="warning"
                  plain
                  class="btn-base-stock"
                  style="margin-top: 8px; margin-left: -1020px; height: 25px;"
                  @click="handleAnalyze"
                >设置为基准股票</el-button>

                <el-button type="success" plain size="small" style="margin-right: -80px; margin-top: 10px;"
                 @click="showDialog = true">
                  多头排列测试
                </el-button>
                <DialogBullish
                  :visible ="showDialog"
                  @close="showDialog = false"
                />
              </div>
            </div>
            <!--MA曲线展示部分-->
            <div style="display: flex; margin-top: 20px; width: 100%; justify-content: center; align-items: flex-start;">
              <!-- 三个K线图 -->
              <div style="width: 1000px; gap: 0px; margin-top: -40px; margin-left: -60px;">
                <Graph style="position: relative; z-index: 3;" :code="graphCode1" :startDate="modeInfo.startDate" :endDate="modeInfo.endDate" :checkListMAOption="store.state.modeInfo.lines" :width="1050" :height="240" :legendData="store.state.modeInfo.lines" />
                
                <Graph style="position: relative; z-index: 2; margin-top: -40px;" :code="graphCode3" :startDate="modeInfo.startDate" :endDate="modeInfo.endDate" :checkListMAOption="store.state.modeInfo.lines2" :width="1050" :height="240" :legendData="store.state.modeInfo.lines2" />
                <Graph style="position: relative; z-index: 1; margin-top: -40px;" :code="graphCode2" :startDate="modeInfo.startDate" :endDate="modeInfo.endDate" :checkListMAOption="store.state.modeInfo.lines1" :width="1050" :height="240" :legendData="store.state.modeInfo.lines1" />
              </div>
              <!-- 推荐模式/自定义模式卡片 -->
              <div style="margin-left: 10px;"><ModeCards /></div>
            </div>
            <hr style="margin-top: 40px;"/>
            <!--结果展示部分-->
            <ResultShow v-if="resultType"/>
            <ResultShowMode v-if="resultMode"/>
            <ResultShowStock v-if="resultStock"/>
          </el-main>
        </el-container>
      </el-container>
    </div>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { nextTick, ref, onMounted, watch, computed, reactive } from "vue";
import axios from "axios";
import { useStore } from "vuex";

// 引入子组件
import DialogChoose2 from "@/nouse/DialogChoose2.vue";
import ModeCards from "@/views/ModeCards.vue";
import ResultShow from "@/views/ResultShow.vue";
import ResultShowMode from "@/nouse/ResultShowMode.vue";
import ResultShowStock from "@/nouse/ResultShowStock.vue";
import DialogBullish from "@/nouse/DialogBullish.vue";
import Graph from "@/views/Graph.vue";
import {Star, StarFilled} from "@element-plus/icons";


// dialog测试数据 ********************************
const showDialog = ref(false);


// 设置全局store数据
const store = useStore();
const resultType = ref(false);
const resultMode = ref(false);
const resultStock = ref(false);
const dialogVisible = ref(false);
const graphCode1 = ref("000021");
const graphCode2 = ref("000001");
const graphCode3 = ref("600746");
const maList = ref(["MA4", "MA8", "MA12", "MA16", "MA20", "MA47"]);
const isBaseStock = computed(() => {
  return store.state.baseInfo.isStock === true;
});
const isBaseMode = computed(() => {
  return store.state.baseInfo.isMode === true;
});
const isDisabled = computed(() => {
  return store.state.baseInfo.isDisabled === true;
});
const isSelected = computed(() => {
  const code = stockShowInfo.value?.code;
  return store.state.stockList.some(item => item.code === code && item.isSelected);
});

// 定义响应式状态
const baseInfo = reactive({
  isHistory: false, // 是否为历史查找
  isCross: false,   // 是否为横向对比查找
  isSection: false, // 是否为区间
  isChoose: false,  // 是否为选股
});
// 状态重置函数
const resetBaseInfo = () => {
  baseInfo.isHistory = false;
  baseInfo.isCross = false;
  baseInfo.isSection = false;
  baseInfo.isChoose = false;
};

// 收藏/取消收藏逻辑
const toggleFavorite = () => {
  const code = stockShowInfo.value?.code;
  if (!code) return;
  const idx = store.state.stockList.findIndex(item => item.code === code);
  if (idx !== -1) {
    if (!store.state.stockList[idx].isSelected) {
      // 加入自选
      store.state.stockList[idx].isSelected = true;
      // 可选：弹窗提示"已添加到自选"
    } else {
      // 已在自选，再次点击则移除
      store.state.stockList[idx].isSelected = false;
      // 可选：弹窗提示"已移除自选"
    }
  }
};

// 切换按钮状态的方法
const toggleButton = (key) => {
  console.log("切换按钮状态------------------", key);
  // 如果点击的按钮当前为true，则点击后设为false
  if (baseInfo[key]) {
    baseInfo[key] = false;
  } else {
    // 否则将点击的设为true，另一个设为false
    baseInfo.isHistory = key === 'isHistory';
    baseInfo.isCross = key === 'isCross';
  }
};

const toggleButton1 = (key) => {
  console.log("切换第一序列按钮状态------------------", key);
  // 如果点击的按钮当前为true，则点击后设为false
  if (baseInfo[key]) {
    baseInfo[key] = false;
  } else {
    // 否则将点击的设为true，另一个设为false
    baseInfo.isChoose = key === 'isChoose';
    baseInfo.isSection = key === 'isSection';
  }
};

// 在组件 setup 函数中添加监听
watch(() => baseInfo.isSection,(newValue) => {
    if (newValue === false) {
      baseInfo.isHistory = false;
      baseInfo.isCross = false;
    }
  }
);

// 新手指引--------------------------------------------------
// 导入ref
const stockTourVisible = ref(false);   // 个股指引显示状态
const modeTourVisible = ref(false);    // 推荐模式指引显示状态
const tourStep = ref(0);
const modeTourStep = ref(0);

// 开启指引方法
const startStockTour = () => {
  console.log("点击了个股新手指引");
  setTimeout(() => {
    stockTourVisible.value = true;
  }, 80);
};

const startModeTour = () => {
  console.log("点击了推荐模式新手指引");
  setTimeout(() => {
    modeTourVisible.value = true;
  }, 80);
};


// input查找目标股票--------------------------------------------------
const searchQuery = ref("");
const filteredTableData1 = (item) => {
  return store.state.stockList.filter((row) => {
    return (
      row.code.includes(searchQuery.value) ||
      row.name.includes(searchQuery.value)
    );
  });
};
const filteredTableData2 = (item) => {
  return store.state.stockList.filter((row) => {
    return (
      (row.code.includes(searchQuery.value) ||
        row.name.includes(searchQuery.value)) &&
      row.isSelected === true
    );
  });
};

const tableDataRecent = ref(store.state.stockList1);

// 界面展示股票信息
const stockShowInfo = ref();
stockShowInfo.value = store.state.stockShowInfo;

// 用户当前设置的模式信息
const modeInfo = store.state.modeInfo;
const searchInfo = store.state.searchInfo;

const getDialog = () => {
  console.log("点击了多头排列测试按钮");
  showDialog.value = true;
};

// 处理生成结果按钮的点击事件
const getResult = async() => {
  console.log("生成结果------------------------");
  const timestamp = new Date().getTime();
  const newLines = store.state.modeInfo.lines.map(item => parseInt(item.replace('MA', ''), 10));

  console.log("当前的modeInfo------------------", store.state.modeInfo);

  try {
    // **************** 个股模式匹配 ****************
    if(store.state.baseInfo.isStock === true)
    {
      resultType.value = true;
      console.log("modeInfo----", store.state.modeInfo)
      console.log("searchInfo----", store.state.searchInfo)
      // 获取股票模式检测结果
      const response = await axios.post(
        `http://127.0.0.1:5000/detect_stock_mode?timestamp=${timestamp}`,
        {
          pool: searchInfo.stockList, // 备选股票池
          base_code: store.state.modeInfo.index,
          base_start_date: store.state.modeInfo.startDate,
          base_end_date: store.state.modeInfo.endDate,
          start_date: searchInfo.searchStartDate, // 开始时间
          end_date: searchInfo.searchEndDate, // 结束时间
          ma_list: newLines.slice(1), // MA列表
        },
        {
          withCredentials: true,  // 如果需要携带凭证
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      console.log("获取到的结果列表------------------", response.data);
      
      store.state.resultInfo.futureIncome = response.data.overall_return;
      store.state.resultList2 =  response.data.result;
      
    }

    // **************** 系统模式匹配 ****************
    // 【黄金交叉】
    if(store.state.baseInfo.isMode === true && baseInfo.isCross === true && store.state.modeInfo.index === "GC")
    {
      resultType.value = true;
      // 获取金叉检测结果
      const response = await axios.post(
        `http://127.0.0.1:5000/detect_golden_cross?timestamp=${timestamp}`,
        {
          pool: searchInfo.stockList, // 备选股票池
          start_date: searchInfo.searchStartDate, // 开始时间
          end_date: searchInfo.searchEndDate, // 结束时间
          ma_list: newLines.slice(1), // MA列表
        },
        {
          withCredentials: true,  // 如果需要携带凭证
          headers: {
            // 设置请求头，根据实际情况设置
            'Content-Type': 'application/json'
          }
        }
      );
      console.log("获取到的结果列表------------------", response.data);
      store.state.resultInfo.futureIncome = response.data.overall_return;
      store.state.resultList =  response.data.result;
    }
    // 多头排列检测结果
    if(store.state.baseInfo.isMode === true && baseInfo.isCross === true && store.state.modeInfo.index === "BA") {
      try {
        resultMode.value = true;
        const response = await axios.post(
          `http://127.0.0.1:5000/detect_bullish_arrangement?timestamp=${timestamp}`,
          {
            pool: searchInfo.stockList, // 备选股票池
            start_date: searchInfo.searchStartDate, // 开始时间
            end_date: searchInfo.searchEndDate, // 结束时间
            ma_list: newLines.slice(1), // MA列表
          },
          {
            withCredentials: true,  // 如果需要携带凭证
            headers: {
              'Content-Type': 'application/json'
            },
            timeout: 3000000000000, // 设置超时时间（根据实际需求调整）
          }
        );
        const twoDimensionalArray = Object.values(response.data)[0];
        store.state.resultList = twoDimensionalArray;
        console.log("获取到的结果列表------------------", twoDimensionalArray);
      } catch (error) {
        if (axios.isCancel(error)) {
          console.log('请求被取消:', error.message);
        } else if (error.code === 'ECONNABORTED') {
          // 超时处理
          console.error('请求超时:', error.message);
          // 这里可以添加自定义逻辑，如重试机制或提示用户
          alert('请求超时，请稍后再试');
        } else {
          console.error('请求错误:', error.message);
        }
      }
}
    
  } catch (error) {
    console.error('errors:', error);
  }
};

// 处理分析按钮的点击事件,设置当前股票为基准股票【更新modeInfo的数据】
const handleAnalyze = () => {
  resetBaseInfo();
  const foundStock = store.state.stockList.find(
    (item) => item.code === stockShowInfo.value.code
  );
  console.log("设置为基准股票--------------", foundStock);
  store.commit("updateModeInfo", {
    index: foundStock.code,
    name: foundStock.name,
    startDate: "2025-01-17",
    endDate: "2025-01-23",
    isMode: false, // 不是模式而是股票
    lines: ["个股", "MA4", "MA8", "MA12"],
    lines1: ["深证指数", "MA4", "MA8", "MA12"],
    lines2: ["行业指数", "MA4", "MA8", "MA12"],
  });
  store.commit("updateBaseInfo", {
    isMode: false,
    isStock: true,
    currentFunction: "个股模式查找"
  });
  value1.value = ['2025-01-17', '2025-01-23'];
};

// 定义点击事件处理函数
const handleRowClick = async (row) => {
  const code = row.code;
  graphCode1.value = code; // 修改子图的数据
  // 通过code的起始值判断上证指数 or 深证指数
  if (code.startsWith('0')) {
    graphCode2.value =  '000001'; // 上证指数
  } else if (code.startsWith('6')) {
    graphCode2.value =  '399001'; // 深证指数
  }
  const foundStock = store.state.stockList.find((item) => item.code === code);
  stockShowInfo.value = { ...foundStock };
};

// -------------------------------------------------------------------------------
const activeName1 = ref("near");
const value1 = ref([store.state.modeInfo.startDate, store.state.modeInfo.endDate]); // 选择的日期范围
const value2 = ref([searchInfo.searchStartDate, searchInfo.searchEndDate]); // 选择的日期范围
const value3 = ref([]); // 选择的日期范围

watch(baseInfo.isHistory, () => {
  if(baseInfo.isHistory === true && store.state.baseInfo.isStock === true) {
    store.commit("updateStockList1", {
      stockList1: [{
        code: store.state.modeInfo.index,
        name: store.state.modeInfo.name,
      }],
    });
  }
});

// 监听基准股票日期范围的变化
watch(value1, () => {
  store.state.modeInfo.startDate = value1.value[0];
  store.state.modeInfo.endDate = value1.value[1];
  value3.value = value1.value;
  value2.value = value1.value;
  tableDataRecent.value = [{
    code: store.state.modeInfo.index,
    name: store.state.modeInfo.name,
  }];
  
});

// 监听带查找股票池日期范围的变化
watch(searchInfo, () => {
    value2.value = [searchInfo.searchStartDate, searchInfo.searchEndDate];
    if(baseInfo.isHistory === false)
    {
      tableDataRecent.value = searchInfo.stockList;
    }
});

watch(() => store.state.baseInfo.isMode,(newValue) => {
    if (newValue === true && store.state.modeInfo.index === "BA2") {
      resultType.value = false;
      resultMode.value = true;
      resultStock.value = false;
    }
    if(newValue === false){
      resultType.value = true;
      resultMode.value = false;
      resultStock.value = false;
    }
  }
);

watch(() => baseInfo.isChoose,(newValue) => {
    if (newValue === true) {
      resultType.value = false;
      resultMode.value = false;
      resultStock.value = true;
    }
    else
    {
      resultType.value = true;
      resultMode.value = false;
      resultStock.value = false;
    }
  }
);

const newStartDate = ref(new Date("2016-01-02"));
const newEndDate = ref(new Date("2016-06-20"));

function formatDateToLocal(date) {
  const year = date.getFullYear();
  // 月份从 0 开始，需要 +1
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 时间选择触发刷选+缩放
function handleDateChange(val) {
  if (!val || val.length !== 2) return;
  let [startDate, endDate] = val;

  // 【1】保证 startDate endDate 都转成 'yyyy-MM-dd' 字符串
  if (startDate instanceof Date) {
    startDate = formatDateToLocal(startDate);
    newStartDate.value = startDate;
    modeInfo.startDate = startDate; // 更新模式信息中的开始日期
  }
  if (endDate instanceof Date) {
    endDate = formatDateToLocal(endDate);
    newEndDate.value = endDate;
    modeInfo.endDate = endDate; // 更新模式信息中的结束日期
  }
}

// 侧边栏宽度状态
const sidebarWidth = ref(290);
const minWidth = 330;
const maxWidth = 570;

// 拖动相关方法
const startResize = (e) => {
  e.preventDefault();
  const startX = e.clientX;
  const startWidth = sidebarWidth.value;

  const handleResize = (e) => {
    const newWidth = startWidth + (e.clientX - startX);
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      sidebarWidth.value = newWidth;
    } else if (newWidth < minWidth) {
      sidebarWidth.value = minWidth;
    } else if (newWidth > maxWidth) {
      sidebarWidth.value = maxWidth;
    }
  };
  const stopResize = () => {
    document.removeEventListener("mousemove", handleResize);
    document.removeEventListener("mouseup", stopResize);
  };
  document.addEventListener("mousemove", handleResize);
  document.addEventListener("mouseup", stopResize);
};

// 计算表格列宽
const getColumnWidth = (percentage) => {
  return (sidebarWidth.value - 30) * percentage;
};

// 监听侧边栏宽度变化，强制更新表格
watch(sidebarWidth, () => {
  nextTick(() => {
    // 触发表格重新渲染
    const currentPage = document.getElementById("current-page");
    if (currentPage) {
      const tables = currentPage.querySelectorAll(".el-table__header-wrapper");
      tables.forEach((table) => {
        const event = new Event("resize");
        window.dispatchEvent(event);
      });
    }
  });
});


const handleTourChange = async (current, prev) => {
  // STEP 1: 自动点击"设置基准股票"按钮
  if (current === 1) {
    handleAnalyze();

    // 等待 DOM 更新完毕
    await nextTick();

    // 再延迟进入 Step 2
    setTimeout(() => {
      tourStep.value = 2;
    }, 3000); // 建议 2~3 秒最合适
  }

  // STEP 4.1: 自动点击"自定义模式评价"按钮，并延迟跳转到下一个step
  if (current === 11) {
    const customEvaluationButton = document.querySelector('.custom-evaluation-button');
    if (customEvaluationButton) {
      customEvaluationButton.click();
      await nextTick();
      setTimeout(() => {
        tourStep.value = 12; // 跳转到下一个step
      }, 800);
    }
  }

  // STEP 4.2.1: 自动点击"本股票历史行情"按钮，并延迟跳转到下一个step
  if (current === 13) {
    const customEvaluationButton = document.querySelector('.custom-evaluation-button-4-2-2');
    if (customEvaluationButton) {
      customEvaluationButton.click();
      await nextTick();
    }
  }

  if (current === 15) {
    const customEvaluationButton = document.querySelector('.btn-search-range');
    if (customEvaluationButton) {
      customEvaluationButton.click();
      await nextTick();
    }
  }

  // STEP 4.3: 自动点击相似模式选股按钮，并延迟点击"请选择待查找股票集合"按钮
  if (current === 16) {
    const similarModeBtn = document.querySelector('.custom-evaluation-button-4-3');
    if (similarModeBtn) {
      similarModeBtn.click();
      await nextTick();
      setTimeout(() => {
        const searchRangeBtn = document.querySelector('.btn-search-range');
        if (searchRangeBtn) {
          searchRangeBtn.click();
          tourStep.value = 17; // 跳转到下一个step
        }
      }, 800); // 可根据需要调整延迟
    }
  }
};

function handleDateChange2(val) {
  if (!val || val.length !== 2) return;
  let [startDate, endDate] = val;
  if (startDate instanceof Date) {
    startDate = formatDateToLocal(startDate);
    newStartDate.value = startDate;
    searchInfo.searchStartDate = startDate; // 更新模式信息中的开始日期
  }
  if (endDate instanceof Date) {
    endDate = formatDateToLocal(endDate);
    newEndDate.value = endDate;
    searchInfo.searchEndDate = endDate; // 更新模式信息中的结束日期
  }
}


const handleModeTourChange = async (current, prev) => {
  // STEP 1: 自动点击推荐模式卡片标题，弹出弹窗
  if (current === 1) {
    const card = document.querySelector('.mode-card-title');
    if (card) {
      card.click();
    }
    setTimeout(() => {
      modeTourStep.value = 1; // 保证 el-tour 继续在第二步
    }, 9999);
  }
  // STEP 2: 自动点击应用推荐模式按钮，并延迟跳转到下一个step
  if (current === 2) {
    const applyModeBtn = document.querySelector('.apply-mode-btn-step2');
    if (applyModeBtn) {
      applyModeBtn.click();
      await nextTick();
      setTimeout(() => {
        modeTourStep.value = 3; // 跳转到下一个step
      }, 800); // 可根据需要调整延迟
    }
  }
  // 自定义模式评价
  if (current === 11) {
    const customEvaluationButton = document.querySelector('.custom-evaluation-button');
    if (customEvaluationButton) {
      customEvaluationButton.click();
      await nextTick();
    }
  }
  // 多股票横向查找
  if (current === 12) {
    const customEvaluationButton = document.querySelector('.btn-search-range');
    if (customEvaluationButton) {
      customEvaluationButton.click();
      await nextTick();
    }
  }

  // STEP 4.3: 自动点击相似模式选股按钮，并延迟点击"请选择待查找股票集合"按钮
  if (current === 15) {
    const similarModeBtn = document.querySelector('.custom-evaluation-button-4-3');
    if (similarModeBtn) {
      similarModeBtn.click();
      await nextTick();
      setTimeout(() => {
        const searchRangeBtn = document.querySelector('.btn-search-range');
        if (searchRangeBtn) {
          searchRangeBtn.click();
          tourStep.value = 17; // 跳转到下一个step
        }
      }, 800); // 可根据需要调整延迟
    }
  }
};

// 计算涨跌颜色和样式
const upColor = '#ec0000'; // 红色
const downColor = '#00da3c'; // 绿色
const isUp = computed(() => {
  // 只要value或ratio有+号或为正数就认为是涨
  const v = stockShowInfo.value?.value || stockShowInfo.value?.ratio || '';
  return (typeof v === 'string' && v.includes('+')) || (parseFloat(v) > 0);
});
const valueColor = computed(() => {
  const v = stockShowInfo.value?.value || '';
  if (typeof v === 'string' && v.includes('-')) return downColor;
  if (typeof v === 'string' && v.includes('+')) return upColor;
  return parseFloat(v) >= 0 ? upColor : downColor;
});
const ratioColor = computed(() => {
  const v = stockShowInfo.value?.ratio || '';
  if (typeof v === 'string' && v.includes('-')) return downColor;
  if (typeof v === 'string' && v.includes('+')) return upColor;
  return parseFloat(v) >= 0 ? upColor : downColor;
});

</script>

<style src="@/styles/basic.css"></style>   
