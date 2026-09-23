<template>
  <div id="current-page">
    <div style="margin: -8px">
      <el-container class="container">
        <div class="logo">MA均线分析平台</div>
      </el-container>

      <el-container style="height: 94vh;">
        <!-- ================= 左侧栏 (保持不变) ================= -->
        <el-aside>
          <div style="height: 290px; background-color: #f3f3f3; border-radius: 10px; margin-top: 5px; margin-left: 5px;">
            <el-tabs class="custom-tabs" v-model="activeName1" style="margin-left: 10px; width: 275px; ">
              <el-tab-pane label="全部股票" name="near" style="">
                <el-input v-model="searchQuery" style="height: 25px; font-size: 12px; width: calc(98.5%);" placeholder="搜索全部股票" />
                <el-table :data="filteredTableData1(item)" class="scrollable-div" max-height="200" style="border-radius: 8px; cursor: pointer;" border @row-click="handleRowClick">
                  <el-table-column fixed="left" label="股票名称" :width="getColumnWidth(0.4)" header-align="center">
                    <template #default="scope">
                      <div style="display: flex; flex-direction: column">
                        <span style="font-size: 13px" @click="handleRowClick(scope.row)">{{ scope.row.name }}</span>
                        <span style="font-size: 10px; color: #999; margin-top: -7px;">{{ scope.row.code }}</span>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column property="ratio" label="涨跌幅" :width="getColumnWidth(0.3)" header-align="center">
                    <template #default="scope"><span style="font-size: 13px">{{ scope.row.ratio }}</span></template>
                  </el-table-column>
                  <el-table-column property="value" label="涨跌额" :width="getColumnWidth(0.3)" header-align="center">
                    <template #default="scope"><span style="font-size: 13px">{{ scope.row.value }}</span></template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="我的自选" name="self">
                <el-input v-model="searchQuery" style="height: 25px; width: calc(98.5%); font-size: 12px;" placeholder="搜索我的自选" />
                <el-table :data="filteredTableData2(item)" style="height: 200px; font-size: 12px; margin-top: 5px; border-radius: 8px; cursor: pointer;" max-height="200" border @row-click="handleRowClick">
                  <el-table-column fixed="left" label="股票名称" :width="getColumnWidth(0.4)" header-align="center">
                    <template #default="scope">
                      <div style="display: flex; flex-direction: column">
                        <span style="font-size: 14px;" @click="handleRowClick(scope.row)">{{ scope.row.name }}</span>
                        <span style="font-size: 10px; color: #999; margin-top: -7px;">{{ scope.row.code }}</span>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column property="ratio" label="涨跌幅" :width="getColumnWidth(0.3)" header-align="center">
                    <template #default="scope"><span style="font-size: 13px">{{ scope.row.ratio }}</span></template>
                  </el-table-column>
                  <el-table-column property="value" label="涨跌额" :width="getColumnWidth(0.3)" header-align="center">
                    <template #default="scope"><span style="font-size: 13px">{{ scope.row.value }}</span></template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </div>

          <div class="scrollable-div" style="height: 350px; background-color: #f3f3f3; margin-top: 5px; border-radius: 10px;margin-left: 5px; overflow-y: auto;">
            <div style="height: auto;">
              <div class="div5 tour-ma-config" style="padding-bottom: 10px;">
                <!-- 【新增】分析维度切换 -->
                <div style="font-size: 13px; font-weight: bold; margin-left: -160px; margin-top: 5px;">
                  分析维度选择:
                </div>
                <el-radio-group v-model="analysisMode" size="small" style="margin-left: 10px; margin-top: 5px;">
                  <el-radio-button label="MA">均线形态特征</el-radio-button>
                  <el-radio-button label="KLINE">K线趋势骨架</el-radio-button>
                </el-radio-group>

                <!-- 【修改】当选择均线模式时才显示均线选项 -->
                <div v-show="analysisMode === 'MA'">
                  <div style="font-size: 13px; font-weight: bold; margin-left: -160px; margin-top: 15px;">
                    基础 MA 指标选择:
                  </div>
                  <el-checkbox-group v-model="store.state.modeInfo.lines" class="custom-checkbox-group" style="margin-top: 5px; margin-left: 15px;">
                    <el-checkbox v-for="item in maList" :key="item" :label="item" :value="item" class="custom-checkbox"></el-checkbox>
                  </el-checkbox-group>
                </div>
              </div>

              <div style="margin-top: 10px;">
                <div class="div2" style="width: 200px; margin-left: -15px; margin-top: 5px;">设置查找历史时间范围：</div>
                <el-date-picker
                    v-model="value2"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    size="small"
                    style="width: calc(100% - 35px); margin-top: 5px; margin-left: 10px;"
                    @change="handleDateChange2"
                />
              </div>
              <div>
                <div style="margin-top: 10px; margin-left: -3px;">
                  <div style="margin-top: 10px">
                    <el-button plain @click="dialogVisible = true" class="custom-button btn-search-range" style="margin-top: 0px; width: 270px; margin-left: -5px; font-size: 12px;">
                      请选择待查找股票集（默认为全部）
                    </el-button>
<!--                    <DialogChoose2 :visible="dialogVisible" @close="dialogVisible = false" />-->
                    <el-table :data="tableDataRecent" class="scrollable-div" :max-height="tableDataRecent.length > 0 ? 180 : 100" style="margin-left: 8px; margin-top: 10px; border-radius: 10px; width: 280px; margin-bottom: 10px;" border>
                      <el-table-column property="index" fixed="left" label="股票名称" width="140px" header-align="center" align="center">
                        <template #default="scope">
                          <span style="font-size: 14px" @click="handleRowClick(scope.row)">{{ scope.row.name }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column property="code" label="股票代码" width="140px" header-align="center" align="center">
                        <template #default="scope">
                          <span style="font-size: 13px">{{ scope.row.code }}</span>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </div>
              </div>
<!--              <DialogBullish :visible="showDialog" @close="showDialog = false" />-->
            </div>
          </div>
<!--          <el-button @click="getShowDialog" type="primary" plain style="font-size: 12px; width: 140px; height: 30px; margin-left: 0px; margin-top: 5px;" >相似特征确认</el-button>-->
<!--          <el-button type="success" plain style="margin-left: 0px; font-size: 12px; width: 140px;height: 30px; margin-left: 5px;margin-top: 5px;" @click="getResult">开始查找</el-button>-->
        </el-aside>

        <!-- ================= 主工作区 ================= -->
        <el-main
            style="background-color: white; padding: 0; display: flex; flex-direction: row; height: 100%; min-height: 0; overflow: hidden;"
            class="hide-scrollbar"
        >
          <!-- ==== 1. 中间栏 ==== -->
          <div style="flex: 1; min-width: 900px; height: 100%; overflow-y: auto; overflow-x: auto; position: relative;">
            <el-tabs v-model="mainTab" style="margin-left: 10px; margin-top: 5px;">

              <!-- 标签一：模型生成 -->
              <el-tab-pane label="模型生成" name="generate">

                <!-- ====== 核心新增：进度步骤条 ====== -->
                <div style="padding: 15px 20px 5px 20px; background-color: #fff; margin: 0 5px 15px 5px; border-radius: 8px; border: 1px solid #e4e7ed; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);">
                  <el-steps :active="currentStep" finish-status="success" align-center>
                    <el-step title="骨架生成" description="框选片段并微调趋势拐点" />
                    <el-step title="指标提取" description="勾选与补充多模态语义指标" />
                    <el-step title="查找相似片段" description="全市场扫描历史走势并匹配" />
                    <el-step title="训练个性化模型" description="筛选结果样本并生成个性化模型" />
                  </el-steps>
                </div>
                <!-- =============================== -->

                <!-- 顶部股票信息栏 -->
                <div style="display: flex; background-color: #e1f0ff; height: 80px; position: sticky; top: 0; z-index: 100; width: 99%; border-radius: 10px; margin-left: 5px;">
                  <div style="display: flex; flex-direction: column; justify-content: flex-start; min-width: 900px;">
                    <div style="display: flex; align-items: center; padding-top: 5px;">
                      <span style="margin-top:-3px; font-weight: bold; margin-left: 14px; display: inline-block;">{{ stockShowInfo?.name }} </span>
                      <span style="font-weight: bold;  margin-left: 5px; display: inline-block;">({{ stockShowInfo?.code }})</span>
                      <span style="margin-left: 10px; display: inline-block; font-weight: bold;" :style="{color: valueColor, 'font-weight': 'bold'}">{{ stockShowInfo?.value }}</span>
                      <span style="margin-left: 2px; display: inline-block;" :style="{color: valueColor, 'font-weight': 'bold', 'margin-top':'-5px'}">↑</span>
                      <span style="margin-left: 15px; display: inline-block; font-weight: bold;" :style="{color: ratioColor, 'font-weight': 'bold'}">{{ stockShowInfo?.ratio }}</span>
                      <span style="margin-left: 10px; display: inline-block;">
                        <el-tooltip :content="isSelected ? '已添加' : '添加到自选'" placement="top">
                         <el-icon size="20" style="margin-top: 2px; cursor: pointer;" @click="toggleFavorite" :color="isSelected ? '#222' : '#aaa'">
  <StarFilled v-if="isSelected" />
  <Star v-else />
</el-icon>
                        </el-tooltip>
                      </span>
                    </div>

                    <div style="display: flex; align-items: left; padding-top: 5px; font-size: 12px; margin-left: 7px;">
                      <span style="min-width: 90px; margin-left: 7px; display: inline-block;">日期：2025-05-23</span>
                      <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA4：19.560</span>
                      <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA8：19.959</span>
                      <span style="min-width: 90px; margin-left: 14px; display: inline-block;">MA12：19.935</span>
                      <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA16：20.054</span>
                      <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA20：20.179</span>
                      <span style="min-width: 90px; margin-left: 10px; display: inline-block;">MA47：19.899</span>
                    </div>
                    <div style="display: flex; align-items: left; padding-top: 2px; font-size: 12px; margin-left: 15px;">
                      <span style="min-width: 90px; margin-left: -15px; display: inline-block;">板块：主板</span>
                      <span style="min-width: 90px; margin-left: 6px; display: inline-block;">行业：计算机、通信和其他电子设备制造业</span>
                    </div>
                  </div>
                </div>

                <!-- 容器使用 flex-column 垂直排版 -->
                <div style="width: 1000px; display: flex; flex-direction: column; gap: 5px; margin-top: 10px;">

                  <!-- 1. 操作按钮组：通过 justify-content: flex-end 实现右对齐 -->
                  <div style="display: flex; justify-content: flex-end; gap: 8px; padding: 5px; background: #f9f9f9; border-radius: 4px; border: 1px solid #eee;">
                    <el-button size="small" @click="setDateRange('daily')">日线</el-button>
                    <el-button size="small" @click="setDateRange('weekly')">周线</el-button>
                    <el-button size="small" @click="setDateRange('monthly')">月线</el-button>
                    <el-button size="small" @click="toggleZoomLock">{{ isZoomLocked ? '取消锁定' : '锁定缩放比' }}</el-button>
                    <el-button size="small" type="primary" @click="handleExtract" :disabled="!activeBrushData">
                      {{ analysisMode === 'MA' ? '提取均线特征' : '生成K线骨架' }}
                    </el-button>
                    <el-button size="small" type="danger" @click="deleteServerFiles">清空所有标记</el-button>
                    <el-button size="small" type="warning" @click="handleTrainCustomMode" :disabled="savedBrushTimeRanges.length === 0"> 生成个性化模型 </el-button>
                  </div>

                  <!-- 2. 图表区域 -->
                  <div style="width: 100%; background: #fff;">
                    <Graph
                        ref="graphRef"
                        :code="graphCode1"
                        :startDate="modeInfo.startDate"
                        :endDate="modeInfo.endDate"
                        :checkListMAOption="store.state.modeInfo.lines"
                        :analysisMode="analysisMode"
                        :width="1000"
                        :height="500"
                        :isZoomLocked="isZoomLocked"
                        @brush-updated="handleBrushUpdated"
                        :savedBrushes="savedBrushAreas"
                    />
                  </div>

                  <!-- 3. 截图展示区：通过 margin-top: -200px 强行上移 -->
                  <div style="border: 1px solid #cbcbcb; height: 140px; width: 100%; border-radius: 5px; background: rgba(255,255,255,0.8); margin-top: -100px; z-index: 15; position: relative; display: flex; flex-direction: column;">
    <span style="font-size: 12px; color: #666; padding: 4px 10px; background-color: #f5f5f5; border-bottom: 1px solid #eee;">
      本区域展示相似查找基准选区，可点击下方截图复用该片段：
    </span>
                    <div style="display: flex; height: 100%; align-items: center; overflow-x: auto; padding: 0 10px; cursor: pointer;">
                      <div v-for="img in imageList" :key="img.filename" class="image-gallery" style="margin-right: 10px;" @click="handleImageClick(img)">
                        <img :src="img.url" class="screenshot-img" style="width: 100px; height: 100px; object-fit: cover; border: 2px solid transparent;"
                             @mouseover="e => e.target.style.borderColor = '#409EFF'"
                             @mouseout="e => e.target.style.borderColor = 'transparent'"
                             @error="handleImageError(img)">
                      </div>
                    </div>
                  </div>
                </div>
                <hr style="margin-top:20px; margin-bottom: 0px;"/>

                <!-- 底部结果展示区 -->
                <ResultShow v-if="resultType" :key="store.state.sim_stock_list.length + new Date().getTime()" />

                <!-- ====== 特征提取与查找弹窗 ====== -->
                <el-dialog v-model="featureDialogVisible" :title="analysisMode === 'MA' ? '均线形态特征提取' : 'K线骨架与语义特征提取'" width="650px" :append-to-body="false" top="130px" destroy-on-close @opened="renderDialogChart">
                  <div v-if="extractedFeatures" style="font-size: 14px; line-height: 1.6;">
                    <div style="display: flex; justify-content: space-between;">
                      <span><strong>股票代码：</strong> {{ stockShowInfo?.name }} ({{ stockShowInfo?.code }})</span>
                      <span><strong>选区时间：</strong> {{ extractedFeatures.startDate }} 至 {{ extractedFeatures.endDate }}</span>
                    </div>

                    <!-- 【新增】展示用户选取的片段均线走势图 -->
                    <div style="margin-top: 15px; border: 1px solid #EBEEF5; padding: 10px; border-radius: 4px; background: #fff;">
                      <h4 style="margin-top: 0; margin-bottom: 5px; color: #303133; font-size: 13px;">
                        {{ analysisMode === 'MA' ? '所选片段走势预览 (点击交叉点添加特征)' : '已确认的 K线趋势骨架预览' }}
                      </h4>
                      <!-- 图表容器 -->
                      <div ref="dialogChartRef" style="width: 100%; height: 180px;"></div>
                    </div>

                    <!-- 【修改】重构特征列表，支持取消勾选和权重调节 -->
                    <div style="margin-top: 15px; border: 1px solid #EBEEF5; padding: 15px; border-radius: 4px; background: #fafafa;">
                      <h4 style="margin-top: 0; margin-bottom: 10px; color: #303133;">
                        系统与手动提取特征 <span style="font-size: 12px; color: #909399; font-weight: normal;">(勾选并设置权重)</span>
                      </h4>

                      <!-- 滚动列表容器 -->
                      <div style="display: flex; flex-direction: column; gap: 8px; max-height: 180px; overflow-y: auto; padding-right: 5px;" class="hide-scrollbar">
                        <div v-for="(feat, index) in dynamicFeatures" :key="index" style="display: flex; align-items: center; justify-content: space-between;">
                          <!-- 左侧：复选框，监听 change 事件以同步图表上的圆点颜色 -->
                          <!-- 左侧：复选框与动态数值输入 -->
                          <el-checkbox v-model="feat.selected" @change="updateGraphicPoints" style="margin-right: 10px; flex: 1; display: flex; align-items: center;" :title="feat.desc">

                            <!-- 如果是带数值参数的特征（如波动率、拐点数） -->
                            <div v-if="feat.hasValue" style="display: inline-flex; align-items: center;" @click.stop>
                              <span style="margin-right: 5px;">{{ feat.desc }}</span>
                              <!-- 阻止点击事件冒泡，防止点击输入框时触发复选框切换 -->
                              <div @click.stop.prevent>
                                <el-input-number
                                    v-model="feat.value"
                                    :min="0" :step="feat.unit === '%' ? 1 : 1"
                                    size="small"
                                    controls-position="right"
                                    style="width: 85px;"
                                ></el-input-number>
                              </div>
                              <span style="margin-left: 5px;">{{ feat.unit }}</span>
                            </div>

                            <!-- 如果是普通的纯文本特征（如均线交叉、上行趋势） -->
                            <div v-else style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                              {{ feat.desc }}
                            </div>

                          </el-checkbox>

                          <!-- 右侧：权重调节器（仅在选中时出现） -->
                          <div v-if="feat.selected" style="display: flex; align-items: center; gap: 5px;">
                            <span style="font-size: 12px; color: #909399;">权重:</span>
                            <el-input-number
                                v-model="feat.weight"
                                :min="0.1" :max="10" :step="0.5"
                                size="small"
                                style="width: 100px;"
                            ></el-input-number>
                          </div>
                        </div>

                        <div v-if="dynamicFeatures.length === 0" style="color: #999; font-size: 12px; text-align: center; padding: 10px 0;">
                          暂无特征，请在上方图表中点击交叉点添加
                        </div>
                      </div>
                    </div>

                    <div style="margin-top: 20px;">
                      <h4 style="margin-bottom: 10px; color: #303133;">自定义补充特征</h4>
                      <el-input v-model="customFeatureText" type="textarea" :rows="3" placeholder="请输入系统未识别到的其他形态特征，例如：各均线开口逐渐放大..."></el-input>
                      <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
                        <el-button
                          type="success"
                          size="small"
                          :loading="aiParsing"
                          @click="parseCustomPrompt"
                          :disabled="!customFeatureText.trim()"
                        >
                          <el-icon style="margin-right: 4px;"><MagicStick /></el-icon>
                          {{ aiParsing ? 'AI 正在解析...' : 'AI 智能解析特征' }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                  <template #footer>
                    <span class="dialog-footer">
                      <el-button @click="featureDialogVisible = false">取消</el-button>
                      <el-button type="primary" @click="confirmFeatureAndSearch">确认特征并进行历史查找</el-button>
                    </span>
                  </template>
                </el-dialog>

                <!-- ====== AI 解析特征确认弹窗 ====== -->
                <el-dialog v-model="aiFeatureConfirmVisible" title="AI 智能解析结果确认" width="520px" :append-to-body="true" top="20vh">
                  <div v-if="aiParsedFeatures.length > 0">
                    <p style="margin-top: 0; color: #606266; font-size: 13px;">AI 已从您的描述中提取以下特征，请勾选需要引入的特征并可微调数值：</p>
                    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 12px;">
                      <div v-for="(feat, idx) in aiParsedFeatures" :key="idx"
                           style="display: flex; align-items: center; gap: 10px; padding: 8px 12px; border: 1px solid #ebeef5; border-radius: 6px; background: #fafafa;">
                        <el-checkbox v-model="feat.checked" style="flex-shrink: 0;" />
                        <div style="flex: 1; display: flex; align-items: center; gap: 6px;">
                          <span style="font-size: 14px; color: #303133;">{{ feat.desc }}</span>
                          <template v-if="feat.hasValue">
                            <el-input-number
                              v-model="feat.value"
                              :min="0"
                              :step="feat.unit === '%' ? 1 : 1"
                              size="small"
                              controls-position="right"
                              style="width: 90px;"
                            />
                            <span style="font-size: 13px; color: #909399;">{{ feat.unit }}</span>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else style="text-align: center; color: #909399; padding: 20px 0;">暂无解析结果</div>
                  <template #footer>
                    <el-button @click="aiFeatureConfirmVisible = false">取消</el-button>
                    <el-button type="primary" @click="confirmAiFeatures" :disabled="aiParsedFeatures.every(f => !f.checked)">
                      确认引入 ({{ aiParsedFeatures.filter(f => f.checked).length }} 条)
                    </el-button>
                  </template>
                </el-dialog>

                <!-- ====== 步骤一：交互式 K线趋势骨架生成弹窗 ====== -->
                <el-dialog v-model="skeletonDialogVisible" title="步骤一：交互式 K线趋势骨架生成" width="1000px" :append-to-body="false" top="100px" destroy-on-close @opened="renderDialogCharts">

                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-size: 13px; color: #606266; line-height: 1.5;">
                      <span v-if="skeletonViewMode === 'overlay'">
                        <b>【叠加编辑模式】</b>您可以自由微调骨架：<br>
                        1. <b>左键点击图表任意位置</b>：添加一个新的骨架转折点。<br>
                        2. <b>按住红点拖拽</b>：自由移动位置（不再强制吸附）。<br>
                        3. <b>右键点击红点</b>：删除该转折点。
                      </span>
                      <span v-else>
                        <b>【对比只读模式】</b>仅供视觉核对，如需修改请切换回叠加模式。
                      </span>
                    </div>

                    <!-- 视图切换开关 -->
                    <el-radio-group v-model="skeletonViewMode" size="small" @change="renderDialogCharts">
                      <el-radio-button label="overlay"><el-icon><CopyDocument /></el-icon> 叠加编辑</el-radio-button>
                      <el-radio-button label="split"><el-icon><DataAnalysis /></el-icon> 左右对比</el-radio-button>
                    </el-radio-group>
                  </div>

                  <!-- 视图 1：叠加模式 (自由编辑) -->
                  <div v-if="skeletonViewMode === 'overlay'" style="border: 1px solid #EBEEF5; padding: 10px; border-radius: 4px; background: #fff; position: relative;">
                    <div ref="combinedChartRef" style="width: 100%; height: 400px;"></div>
                  </div>

                  <!-- 视图 2：对比模式 (只读) -->
                  <div v-if="skeletonViewMode === 'split'" style="display: flex; gap: 15px; margin-bottom: 5px;">
                    <div style="flex: 1; border: 1px solid #EBEEF5; padding: 10px; border-radius: 4px; background: #fff;">
                      <h4 style="margin: 0 0 5px 0; font-size: 13px; text-align: center; color: #909399;">原始 K线图</h4>
                      <div ref="splitLeftRef" style="width: 100%; height: 350px;"></div>
                    </div>
                    <div style="flex: 1; border: 1px solid #EBEEF5; padding: 10px; border-radius: 4px; background: #fff;">
                      <h4 style="margin: 0 0 5px 0; font-size: 13px; text-align: center; color: #F56C6C;">纯净趋势骨架</h4>
                      <div ref="splitRightRef" style="width: 100%; height: 350px;"></div>
                    </div>
                  </div>

                  <template #footer>
                    <span class="dialog-footer">
                      <el-button @click="skeletonDialogVisible = false">取消</el-button>
                      <el-button type="success" @click="confirmSkeletonAndNext">确认骨架，下一步: 指标提取</el-button>
                    </span>
                  </template>
                </el-dialog>
                <!-- ============================== -->
                <!-- ====== 步骤三前置：全市场检索配置确认弹窗 ====== -->
                <el-dialog v-model="searchConfigDialogVisible" title="检索参数最终确认" width="750px" :append-to-body="true" destroy-on-close @opened="renderConfigPreviewChart">

                  <div style="display: flex; flex-direction: column; gap: 20px;">
                    <!-- 上半部分：形态与特征回顾 -->
                    <div style="border: 1px solid #EBEEF5; padding: 15px; border-radius: 8px; background: #fafafa; display: flex; gap: 20px;">

                      <!-- 左侧：骨架预览 -->
                      <div style="flex: 1;">
                        <h4 style="margin: 0 0 10px 0; font-size: 13px; color: #606266;">
                          <el-icon><Picture /></el-icon> 已确认形态骨架
                        </h4>
                        <!-- 迷你骨架预览图容器 -->
                        <div ref="configPreviewChartRef" style="width: 100%; height: 160px; background: #fff; border-radius: 4px; border: 1px solid #ebeef5;"></div>
                      </div>

                      <!-- 右侧：语义标签预览 -->
                      <div style="flex: 1;">
                        <h4 style="margin: 0 0 10px 0; font-size: 13px; color: #606266;">
                          <el-icon><CollectionTag /></el-icon> 提取的语义特征
                        </h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; max-height: 160px; overflow-y: auto;" class="hide-scrollbar">
                          <el-tag v-for="(feat, index) in confirmedFeaturesList" :key="index" type="success" size="small" style="white-space: normal; height: auto; text-align: left; padding: 5px;">
                            {{ feat }}
                          </el-tag>
                          <div v-if="confirmedFeaturesList.length === 0" style="color: #999; font-size: 12px; margin-top: 10px;">未提取任何特征，将纯依赖物理骨架相似度进行检索。</div>
                        </div>
                      </div>
                    </div>

                    <!-- 下半部分：检索范围配置 -->
                    <div style="border: 1px solid #e4e7ed; padding: 15px; border-radius: 8px;">
                      <h4 style="margin: 0 0 15px 0; font-size: 14px; color: #303133;">
                        <el-icon><Filter /></el-icon> 设置扫描范围
                      </h4>

                      <el-form label-width="110px">
                        <el-form-item label="目标股票池：">
                          <div style="display: flex; align-items: center; gap: 15px;">
                            <span style="font-size: 14px; font-weight: bold; color: #409EFF;">共 {{ targetPoolCount }} 只股票</span>
                            <el-button size="small" plain @click="dialogVisible = true">修改股票池</el-button>
                            <span style="font-size: 12px; color: #909399;">(默认使用左侧选定的股票集或自选股)</span>
                          </div>
                        </el-form-item>

                        <el-form-item label="历史时间段：">
                          <!-- 复用左侧边栏绑定的时间变量，这里改了左侧也会同步改！ -->
                          <el-date-picker
                              v-model="value2"
                              type="daterange"
                              range-separator="至"
                              start-placeholder="开始日期"
                              end-placeholder="结束日期"
                              size="default"
                              style="width: 350px;"
                              @change="handleDateChange2"
                          />
                        </el-form-item>

                        <el-form-item v-if="extractedSegmentData.length > 0" label="形态长度：" style="margin-bottom: 0;">
                          <div style="display: flex; align-items: center; gap: 15px;">
                            <el-slider
                                v-model="windowScale"
                                :min="0.5"
                                :max="2"
                                :step="0.05"
                                show-input
                                :show-input-controls="false"
                                input-size="small"
                                style="width: 280px;"
                            />
                            <span style="font-size: 12px; color: #909399; white-space: nowrap;">
                              已框选 {{ extractedSegmentData.length }} 天 × {{ windowScale.toFixed(2) }}倍 = {{ windowDays }} 天
                            </span>
                          </div>
                        </el-form-item>
                      </el-form>
                    </div>
                  </div>

                  <template #footer>
                    <span class="dialog-footer">
                      <el-button @click="searchConfigDialogVisible = false">返回修改特征</el-button>
                      <el-button type="primary" @click="executeFinalSearch">
                        <el-icon style="margin-right: 5px;"><Search /></el-icon> 确认无误，开始全市场扫描
                      </el-button>
                    </span>
                  </template>
                </el-dialog>
                <!-- ============================== -->
              </el-tab-pane>

              <!-- ====== 标签二：模型使用 ====== -->
              <el-tab-pane label="模型使用" name="use">
                <ModelUsage />
              </el-tab-pane>

            </el-tabs>
          </div>

          <!-- ==== 2. 右侧栏 (静态卡片区域，不受Tabs影响) ==== -->
          <div style="width: 290px; flex-shrink: 0; padding-top: 40px; border-left: 1px solid #ebeef5; overflow-y: auto;" class="hide-scrollbar">
            <ModeCards style="margin-left: 10px;" />
          </div>

        </el-main>
      </el-container>
    </div>

    <!-- ====== 训练集最终管理舱 ====== -->
    <el-dialog v-model="trainCleanDialogVisible" title="训练集最终管理舱" width="950px" :append-to-body="true" top="8vh" @opened="renderCleanPodCharts">
      <div style="display: flex; gap: 20px; min-height: 300px;">
        <!-- 正样本盒 -->
        <div style="flex: 1; border: 1px solid #67C23A; border-radius: 8px; padding: 12px; background: #f0f9eb;">
          <div style="font-weight: bold; color: #67C23A; margin-bottom: 10px;">
            ✓ 正样本盒 ({{ positiveSamples.length }} 个)
          </div>
          <div style="max-height: 450px; overflow-y: auto;">
            <div v-for="(sample, idx) in positiveSamples" :key="'pos_'+idx"
                 style="display: flex; align-items: center; gap: 8px; padding: 6px; margin-bottom: 8px; background: #fff; border-radius: 6px; border: 1px solid #e4e7ed;">
              <el-tag size="small" :type="sample.sourceTag" style="flex-shrink: 0; width: 70px; text-align: center;">{{ sample.source }}</el-tag>
              <div :ref="el => setCleanChartRef(el, 'pos', idx)" style="width: 140px; height: 60px; flex-shrink: 0; border: 1px solid #ebeef5; border-radius: 4px;"></div>
              <div style="flex: 1; display: flex; flex-direction: column; min-width: 0;">
                <span style="font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  {{ sample.stockName || sample.stockCode }}
                </span>
                <span v-if="sample.userRating" style="font-size: 11px; color: #F7BA2A;">★{{ sample.userRating }}</span>
              </div>
              <el-button type="danger" size="small" circle @click="removeSample('positive', idx)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div v-if="positiveSamples.length === 0" style="color: #c0c4cc; text-align: center; padding: 20px;">
              暂无正样本
            </div>
          </div>
          <el-button size="small" type="primary" plain style="width: 100%; margin-top: 8px;" @click="aiSynthesizeMore">
            + AI 再合成几个
          </el-button>
        </div>

        <!-- 负样本盒 -->
        <div style="flex: 1; border: 1px solid #F56C6C; border-radius: 8px; padding: 12px; background: #fef0f0;">
          <div style="font-weight: bold; color: #F56C6C; margin-bottom: 10px;">
            ✗ 负样本盒 ({{ negativeSamples.length }} 个)
          </div>
          <div style="max-height: 450px; overflow-y: auto;">
            <div v-for="(sample, idx) in negativeSamples" :key="'neg_'+idx"
                 style="display: flex; align-items: center; gap: 8px; padding: 6px; margin-bottom: 8px; background: #fff; border-radius: 6px; border: 1px solid #e4e7ed;">
              <el-tag size="small" :type="sample.sourceTag" style="flex-shrink: 0; width: 70px; text-align: center;">{{ sample.source }}</el-tag>
              <div :ref="el => setCleanChartRef(el, 'neg', idx)" style="width: 140px; height: 60px; flex-shrink: 0; border: 1px solid #ebeef5; border-radius: 4px;"></div>
              <div style="flex: 1; display: flex; flex-direction: column; min-width: 0;">
                <span style="font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  {{ sample.stockName || sample.stockCode }}
                </span>
                <span v-if="sample.userRating" style="font-size: 11px; color: #F56C6C;">★{{ sample.userRating }}</span>
              </div>
              <el-button type="danger" size="small" circle @click="removeSample('negative', idx)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div v-if="negativeSamples.length === 0" style="color: #c0c4cc; text-align: center; padding: 20px;">
              暂无负样本
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="trainCleanDialogVisible = false">取消</el-button>
        <el-button type="warning" @click="confirmYoloTrain" :loading="yoloTraining" :disabled="positiveSamples.length === 0">
          YOLO训练 (含数据增强)
        </el-button>
<!--        <el-button type="primary" @click="confirmTrainFromCleanPod" :disabled="positiveSamples.length === 0">-->
<!--          确认训练 (小样本, 正{{ positiveSamples.length }} 负{{ negativeSamples.length }})-->
<!--        </el-button>-->
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// ==================== 导入 ====================
import * as echarts from "echarts";
import { nextTick, ref, watch, computed, reactive, onMounted, toRaw } from "vue";
import axios from "axios";
import { useStore } from "vuex";
import { StarFilled, Star, DataAnalysis, List, VideoPlay, CopyDocument, Search, Picture, CollectionTag, Filter, MagicStick, Close } from '@element-plus/icons-vue';
import html2canvas from 'html2canvas';
import { ElMessageBox, ElMessage } from 'element-plus';

import ModeCards from "@/views/ModeCards.vue";
import ResultShow from "@/views/ResultShow.vue";
import Graph from "@/views/Graph.vue";
// import DialogBullish from "@/nouse/DialogBullish.vue";
// import DialogChoose2 from "@/nouse/DialogChoose2.vue";
import ModelUsage from "@/views/ModelUsage.vue";


// ==================== 全局状态与常量 ====================
const store = useStore();

const API_BASE_URL = 'http://127.0.0.1:5000';
const upColor = '#ec0000';
const downColor = '#00da3c';
const BRUSH_HISTORY_FILE = 'brush_history.json';

const analysisMode = ref('MA');

// 分析维度切换时同步到 store
watch(analysisMode, (newMode) => {
  store.state.newSearchInfo.analysisMode = newMode;
}, { immediate: true });
const recentNDaysValue = ref('');
const maList = ref(["MA4", "MA8", "MA12", "MA16", "MA20", "MA47"]);


// ==================== Vuex Store 快捷引用 ====================
const modeInfo = store.state.modeInfo;
const searchInfo = store.state.searchInfo;


// ==================== 股票信息与展示 ====================
const stockShowInfo = ref();
stockShowInfo.value = store.state.stockShowInfo;

const isSelected = computed(() => {
  const code = stockShowInfo.value?.code;
  return store.state.stockList.some(item => item.code === code && item.isSelected);
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

const toggleFavorite = () => {
  const code = stockShowInfo.value?.code;
  if (!code) return;
  const idx = store.state.stockList.findIndex(item => item.code === code);
  if (idx !== -1) {
    store.state.stockList[idx].isSelected = !store.state.stockList[idx].isSelected;
  }
};


// ==================== 股票列表与搜索 ====================
const searchQuery = ref("");
const activeName1 = ref("near");
const dialogVisible = ref(false);
const tableDataRecent = ref([]);
const sidebarWidth = ref(290);
const selectedDatePreset = ref(null);

const filteredTableData1 = () => {
  return store.state.stockList.filter((row) => {
    return (row.code.includes(searchQuery.value) || row.name.includes(searchQuery.value));
  });
};

const filteredTableData2 = () => {
  return store.state.stockList.filter((row) => {
    return ((row.code.includes(searchQuery.value) || row.name.includes(searchQuery.value)) && row.isSelected === true);
  });
};

const handleRowClick = async (row) => {
  const code = row.code;
  graphCode1.value = code;
  const foundStock = store.state.stockList.find((item) => item.code === code);
  if (foundStock) {
    stockShowInfo.value = { ...foundStock };
  }
  selectedDatePreset.value = null;
};

const getColumnWidth = (percentage) => {
  return (sidebarWidth.value - 30) * percentage;
};


// ==================== 日期与时间配置 ====================
const value1 = ref([
  store.state.modeInfo.startDate ? new Date(store.state.modeInfo.startDate) : null,
  store.state.modeInfo.endDate ? new Date(store.state.modeInfo.endDate) : null
]);

const value2 = ref([
  searchInfo.searchStartDate ? new Date(searchInfo.searchStartDate) : null,
  searchInfo.searchEndDate ? new Date(searchInfo.searchEndDate) : null
]);

const value3 = ref([]);
const newStartDate = ref(new Date("2016-01-02"));
const newEndDate = ref(new Date("2016-06-20"));

function formatDateToLocal(date) {
  if (!date) return null;
  let processedDate = date;
  if (!(processedDate instanceof Date) || isNaN(processedDate.getTime())) {
    try {
      const parsedDate = new Date(date);
      if (!isNaN(parsedDate.getTime())) processedDate = parsedDate;
      else return null;
    } catch (e) {
      return null;
    }
  }
  const year = processedDate.getFullYear();
  const month = String(processedDate.getMonth() + 1).padStart(2, '0');
  const day = String(processedDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function handleDateChange2(val) {
  if (!val || val.length !== 2) {
    searchInfo.searchStartDate = null;
    searchInfo.searchEndDate = null;
    newStartDate.value = null;
    newEndDate.value = null;
    return;
  }
  let [startDateRaw, endDateRaw] = val;
  const startDateFormatted = formatDateToLocal(startDateRaw);
  const endDateFormatted = formatDateToLocal(endDateRaw);
  searchInfo.searchStartDate = startDateFormatted;
  searchInfo.searchEndDate = endDateFormatted;
  newStartDate.value = startDateFormatted;
  newEndDate.value = endDateFormatted;
}

const setDateRange = (preset) => {
  ElMessageBox.confirm(
      '相似性查找需在同一周期下进行，切换均线周期会清空已有截图，是否切换？',
      '周期切换确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    const today = new Date();
    let startDate = new Date();
    let endDate = new Date();

    switch (preset) {
      case 'daily':
        if (graphCode1.value.length > 6) graphCode1.value = graphCode1.value.slice(0, 6);
        startDate.setDate(today.getDate() - 200);
        break;
      case 'weekly':
        startDate.setMonth(today.getMonth() - 200);
        if (graphCode1.value.length > 6) graphCode1.value = graphCode1.value.slice(0, 6);
        graphCode1.value = graphCode1.value + "_week";
        break;
      case 'monthly':
        startDate.setFullYear(today.getFullYear() - 200);
        if (graphCode1.value.length > 6) graphCode1.value = graphCode1.value.slice(0, 6);
        graphCode1.value = graphCode1.value + "_month";
        break;
    }
    value1.value = [startDate, endDate];
    selectedDatePreset.value = preset;

    try {
      const response = await axios.post(`${API_BASE_URL}/delete-files`, { folderPath: '/public/savepng' });
      if (response.data.success) {
        ElMessage.success('服务器文件夹数据已成功删除');
        fetchImages();
        currentStep.value = 0;
        resultType.value = false;
      } else {
        ElMessage.error('删除失败：' + response.data.msg);
      }
    } catch (err) {
      ElMessage.error('删除操作失败，请重试');
    }
  }).catch(() => {});
};


// ==================== 图表与选区状态 ====================
const graphCode1 = ref("000021");
const graphRef = ref(null);
const isZoomLocked = ref(false);
const activeBrushData = ref(null);
const savedBrushAreas = ref([]);
const savedBrushTimeRanges = ref([]);

const toggleZoomLock = () => {
  isZoomLocked.value = !isZoomLocked.value;
  if (!isZoomLocked.value) {
    if (graphRef.value) graphRef.value.clearActiveBrush();
    activeBrushData.value = null;
  }
};

const handleBrushUpdated = (data) => {
  activeBrushData.value = data;
  if (data && currentStep.value === 0) {
    currentStep.value = 1;
  } else if (!data && currentStep.value === 1) {
    currentStep.value = 0;
  }
};


// ==================== Tabs、步骤条与弹窗状态 ====================
const mainTab = ref('generate');
const currentStep = ref(0);
const resultType = ref(false);
const resultMode = ref(false);
const resultStock = ref(false);
const showDialog = ref(false);
const baseInfo = reactive({
  isHistory: false,
  isCross: false,
  isSection: false,
  isChoose: false,
});

// ==================== 特征提取（均线模式） ====================
const featureDialogVisible = ref(false);
const extractedFeatures = ref(null);
const dynamicFeatures = ref([]);
const customFeatureText = ref('');
const aiParsing = ref(false);
const aiFeatureConfirmVisible = ref(false);
const aiParsedFeatures = ref([]);
const dialogChartRef = ref(null);
let dialogChartInstance = null;
const extractedSegmentData = ref([]);
let updateGraphicPoints = null;

const openFeatureDialog = () => {
  if (!activeBrushData.value || !graphRef.value) {
    ElMessage.warning('请先在图表上框选一段均线片段');
    return;
  }

  const { startDate, endDate } = activeBrushData.value;
  const segmentData = graphRef.value.getDataByRange(startDate, endDate);

  if (!segmentData || segmentData.length === 0) {
    ElMessage.error('无法获取选区数据');
    return;
  }
  extractedSegmentData.value = segmentData;

  const autoFeats = [];
  const activeMAs = store.state.modeInfo.lines.filter(l => l.startsWith('MA'));

  if (activeMAs.length >= 3) {
    autoFeats.push({ desc: `均线密集纠缠 (${activeMAs.slice(0, 3).join(', ')})`, weight: 1.0, selected: true });
  }

  if (activeMAs.includes('MA12') && activeMAs.includes('MA20')) {
    let allAbove = true;
    for (let i = 0; i < segmentData.length; i++) {
      if (segmentData[i]['MA12'] <= segmentData[i]['MA20']) {
        allAbove = false; break;
      }
    }
    if (allAbove) autoFeats.push({ desc: 'MA12 始终位于 MA20 上方', weight: 1.0, selected: true });
  }

  if (activeMAs.includes('MA4') && segmentData.length > 3) {
    const firstHalf = segmentData[0]['MA4'];
    const mid = segmentData[Math.floor(segmentData.length / 2)]['MA4'];
    const last = segmentData[segmentData.length - 1]['MA4'];
    if (firstHalf > mid && last > mid) {
      autoFeats.push({ desc: 'MA4 斜率由负转正 (出现向上拐点)', weight: 1.0, selected: true });
    } else if (firstHalf < mid && last < mid) {
      autoFeats.push({ desc: 'MA4 斜率由正转负 (出现向下拐点)', weight: 1.0, selected: true });
    }
  }

  extractedFeatures.value = { startDate, endDate };
  dynamicFeatures.value = autoFeats;
  customFeatureText.value = '';
  featureDialogVisible.value = true;
};

const renderDialogChart = () => {
  if (!dialogChartRef.value || !extractedSegmentData.value || extractedSegmentData.value.length === 0) return;
  if (dialogChartInstance) dialogChartInstance.dispose();

  dialogChartInstance = echarts.init(dialogChartRef.value);
  const dates = extractedSegmentData.value.map(item => item.trade_date);

  if (analysisMode.value === 'KLINE') {
    const klineData = extractedSegmentData.value.map(item => [
      item.open !== undefined ? item.open : (item.close || 0),
      item.close || 0,
      item.low !== undefined ? item.low : (item.close || 0),
      item.high !== undefined ? item.high : (item.close || 0)
    ]);
    const smoothedPrices = extractedSegmentData.value.map(item => item.MA4);

    let allValues = [...smoothedPrices];
    extractedSegmentData.value.forEach(item => {
      if (item.high != null) allValues.push(item.high);
      if (item.low != null) allValues.push(item.low);
    });
    const validValues = allValues.filter(v => v != null && !isNaN(v));
    const minVal = Math.min(...validValues);
    const maxVal = Math.max(...validValues);
    const padding = (maxVal - minVal) * 0.05;

    dialogChartInstance.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, textStyle: { fontSize: 10 }, padding: [4, 8] },
      grid: { left: 10, right: 10, top: 15, bottom: 10, containLabel: false },
      xAxis: { type: 'category', data: dates, show: false },
      yAxis: { type: 'value', min: minVal - padding, max: maxVal + padding, show: false },
      series: [
        {
          name: 'K线', type: 'candlestick', data: klineData,
          itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' }, z: 1
        },
        {
          type: 'line', data: smoothedPrices, smooth: true,
          lineStyle: { type: 'dashed', color: '#ccc', width: 1.5 }, symbol: 'none', z: 2
        },
        {
          type: 'line',
          data: skeletonPoints.value.map(p => [p.date, p.price]),
          lineStyle: { color: '#409EFF', width: 2 },
          symbol: 'circle', symbolSize: 6,
          itemStyle: { color: '#F56C6C', borderColor: '#fff', borderWidth: 1 }, z: 3
        }
      ]
    });
    return;
  }

  // MA 均线模式渲染逻辑 (带点击交叉点添加特征)
  const activeMAs = store.state.modeInfo.lines.filter(l => l.startsWith('MA'));
  const colorMap = {
    'MA4': '#cd1f0e', 'MA8': '#edbf09', 'MA12': '#62c613',
    'MA16': '#1286ff', 'MA20': '#9f12ff', 'MA47': '#000000'
  };

  const series = activeMAs.map(ma => ({
    name: ma, type: 'line',
    data: extractedSegmentData.value.map(item => item[ma]),
    showSymbol: false, lineStyle: { width: 1.5 },
    itemStyle: { color: colorMap[ma] || '#000' }
  }));

  let allValues = [];
  series.forEach(s => {
    const validData = s.data.filter(v => v != null && !isNaN(v));
    allValues = allValues.concat(validData);
  });

  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const padding = (maxVal - minVal) * 0.1;

  dialogChartInstance.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 }, padding: [4, 8], backgroundColor: 'rgba(255, 255, 255, 0.9)' },
    grid: { left: 10, right: 10, top: 15, bottom: 10, containLabel: false },
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', min: minVal - padding, max: maxVal + padding, show: false },
    series: series
  });

  const crossPoints = [];
  const totalLength = extractedSegmentData.value.length;

  for (let i = 1; i < totalLength; i++) {
    const prev = extractedSegmentData.value[i - 1];
    const curr = extractedSegmentData.value[i];

    let stage = '中段';
    const progress = i / totalLength;
    if (progress <= 0.33) stage = '前段';
    else if (progress >= 0.67) stage = '后段';

    for (let j = 0; j < activeMAs.length; j++) {
      for (let k = j + 1; k < activeMAs.length; k++) {
        const maA = activeMAs[j], maB = activeMAs[k];
        const numA = parseInt(maA.replace('MA', '')), numB = parseInt(maB.replace('MA', ''));
        const fastMA = numA < numB ? maA : maB;
        const slowMA = numA < numB ? maB : maA;

        const fPrev = prev[fastMA], sPrev = prev[slowMA], fCurr = curr[fastMA], sCurr = curr[slowMA];
        if (fPrev == null || sPrev == null || fCurr == null || sCurr == null) continue;

        let type = null;
        if (fPrev <= sPrev && fCurr > sCurr) type = '上穿';
        else if (fPrev >= sPrev && fCurr < sCurr) type = '下穿';

        if (type) {
          const ratio = Math.abs(fPrev - sPrev) / (Math.abs(fPrev - sPrev) + Math.abs(fCurr - sCurr));
          crossPoints.push({
            prevDate: prev.trade_date, currDate: curr.trade_date, fPrev, fCurr, ratio,
            fastMA, slowMA, type, labelDate: curr.trade_date, stage: stage
          });
        }
      }
    }
  }

  // ========== 均线纠缠点检测：相邻均线对间距持续 <1% 的区间 ==========
  const entanglePoints = [];
  if (activeMAs.length >= 2) {
    const sortedMAs = [...activeMAs].sort((a, b) => parseInt(a.replace('MA', '')) - parseInt(b.replace('MA', '')));
    const rawEntangles = [];

    for (let j = 0; j < sortedMAs.length - 1; j++) {
      const maA = sortedMAs[j], maB = sortedMAs[j + 1];
      let runStart = -1;

      for (let i = 0; i < totalLength; i++) {
        const row = extractedSegmentData.value[i];
        const a = row[maA], b = row[maB];
        const ref = row.close != null ? row.close : ((a != null ? a : 0) + (b != null ? b : 0)) / 2;
        const isTight = a != null && b != null && ref > 0 && Math.abs(a - b) / ref * 100 < 1.0;

        if (isTight) {
          if (runStart === -1) runStart = i;
        } else {
          if (runStart !== -1 && i - runStart >= 5) {
            rawEntangles.push({ startIdx: runStart, endIdx: i - 1, maPair: [maA, maB] });
          }
          runStart = -1;
        }
      }
      if (runStart !== -1 && totalLength - runStart >= 5) {
        rawEntangles.push({ startIdx: runStart, endIdx: totalLength - 1, maPair: [maA, maB] });
      }
    }

    // 合并重叠 ≥50% 的纠缠区间（均线组取并集）
    rawEntangles.sort((x, y) => x.startIdx - y.startIdx);
    const merged = [];
    for (const ent of rawEntangles) {
      const target = merged.find(m => {
        const overlap = Math.min(m.endIdx, ent.endIdx) - Math.max(m.startIdx, ent.startIdx) + 1;
        if (overlap <= 0) return false;
        const shorter = Math.min(m.endIdx - m.startIdx + 1, ent.endIdx - ent.startIdx + 1);
        return overlap / shorter >= 0.5;
      });
      if (target) {
        target.endIdx = Math.max(target.endIdx, ent.endIdx);
        ent.maPair.forEach(ma => { if (!target.maSet.includes(ma)) target.maSet.push(ma); });
      } else {
        merged.push({ startIdx: ent.startIdx, endIdx: ent.endIdx, maSet: [...ent.maPair] });
      }
    }

    merged.forEach(m => {
      const midIdx = Math.floor((m.startIdx + m.endIdx) / 2);
      const midRow = extractedSegmentData.value[midIdx];
      const vals = m.maSet.map(ma => midRow[ma]).filter(v => v != null && !isNaN(v));
      if (vals.length === 0) return;
      const midPrice = vals.reduce((s, v) => s + v, 0) / vals.length;
      const days = m.endIdx - m.startIdx + 1;

      const progress = midIdx / totalLength;
      const entStage = progress <= 0.33 ? '前段' : (progress >= 0.67 ? '后段' : '中段');

      entanglePoints.push({
        midIdx,
        midDate: midRow.trade_date,
        midPrice,
        days,
        maGroup: [...m.maSet].sort((a, b) => parseInt(a.replace('MA', '')) - parseInt(b.replace('MA', ''))),
        stage: entStage
      });
    });
  }

  updateGraphicPoints = () => {
    if (!dialogChartInstance) return;
    const crossGraphics = crossPoints.map((cp, index) => {
        const posPrev = dialogChartInstance.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [cp.prevDate, cp.fPrev]);
        const posCurr = dialogChartInstance.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [cp.currDate, cp.fCurr]);
        const exactX = posPrev[0] + cp.ratio * (posCurr[0] - posPrev[0]);
        const exactY = posPrev[1] + cp.ratio * (posCurr[1] - posPrev[1]);

        const featText = `在形态【${cp.stage}】，${cp.fastMA} ${cp.type} ${cp.slowMA} (参考:${cp.labelDate})`;
        const targetFeat = dynamicFeatures.value.find(f => f.desc === featText);
        const isSelected = targetFeat && targetFeat.selected;

        return {
          type: 'circle',
          id: `cross-point-${index}`,
          x: exactX, y: exactY,
          shape: { r: isSelected ? 6.5 : 5 },
          style: {
            fill: isSelected ? (cp.type === '上穿' ? '#f56c6c' : '#5cb87a') : 'rgba(200, 200, 200, 0.6)',
            stroke: isSelected ? '#fff' : 'transparent',
            lineWidth: 1.5, shadowBlur: isSelected ? 4 : 0, shadowColor: 'rgba(0,0,0,0.3)'
          },
          z: isSelected ? 100 : 50,
          cursor: 'pointer',
          onclick: function () {
            const existingIndex = dynamicFeatures.value.findIndex(f => f.desc === featText);
            if (existingIndex !== -1) {
              dynamicFeatures.value[existingIndex].selected = !dynamicFeatures.value[existingIndex].selected;
            } else {
              dynamicFeatures.value.push({ desc: featText, weight: 1.0, selected: true });
            }
            updateGraphicPoints();
          }
        };
    });

    const entangleGraphics = entanglePoints.map((ep, index) => {
        const pos = dialogChartInstance.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [ep.midDate, ep.midPrice]);

        const featText = `在形态【${ep.stage}】，均线密集纠缠 (${ep.maGroup.join(',')} 持续${ep.days}天)`;
        const targetFeat = dynamicFeatures.value.find(f => f.desc === featText);
        const isSelected = targetFeat && targetFeat.selected;

        const r = isSelected ? 8 : 6;
        return {
          type: 'polygon',
          id: `entangle-point-${index}`,
          shape: {
            points: [
              [pos[0], pos[1] - r],
              [pos[0] + r, pos[1]],
              [pos[0], pos[1] + r],
              [pos[0] - r, pos[1]]
            ]
          },
          style: {
            fill: isSelected ? '#e6a23c' : 'rgba(230, 162, 60, 0.45)',
            stroke: isSelected ? '#fff' : 'transparent',
            lineWidth: 1.5, shadowBlur: isSelected ? 4 : 0, shadowColor: 'rgba(0,0,0,0.3)'
          },
          z: isSelected ? 100 : 50,
          cursor: 'pointer',
          onclick: function () {
            const existingIndex = dynamicFeatures.value.findIndex(f => f.desc === featText);
            if (existingIndex !== -1) {
              dynamicFeatures.value[existingIndex].selected = !dynamicFeatures.value[existingIndex].selected;
            } else {
              dynamicFeatures.value.push({
                desc: featText, weight: 1.0, selected: true,
                hasValue: true, value: ep.days, unit: '天'
              });
            }
            updateGraphicPoints();
          }
        };
    });

    const graphicOption = { graphic: [...crossGraphics, ...entangleGraphics] };
    dialogChartInstance.setOption(graphicOption);
  };
  updateGraphicPoints();
};


// ==================== K线骨架（K线模式） ====================
const skeletonDialogVisible = ref(false);
const skeletonPoints = ref([]);
const skeletonViewMode = ref('overlay');
const combinedChartRef = ref(null);
const splitLeftRef = ref(null);
const splitRightRef = ref(null);

let combinedChartInstance = null;
let splitLeftInstance = null;
let splitRightInstance = null;
let refreshGraphicAndLine = null;

const generateUid = () => 'uid-' + Math.random().toString(36).substring(2, 9);

const openSkeletonDialog = async () => {
  const { startDate, endDate } = activeBrushData.value;
  const segmentData = graphRef.value.getDataByRange(startDate, endDate);
  if (!segmentData || segmentData.length === 0) return;
  extractedSegmentData.value = segmentData;

  const loading = ElMessage({ message: '正在提取真实 K线骨架...', type: 'warning', duration: 0 });

  try {
    const res = await axios.post(`${API_BASE_URL}/api/extract_skeleton`, {
      target_code: graphCode1.value, start_date: startDate, end_date: endDate
    });
    loading.close();

    if (res.data.success && res.data.points) {
      skeletonPoints.value = res.data.points;
      skeletonViewMode.value = 'overlay';
      skeletonDialogVisible.value = true;
    } else {
      ElMessage.error('骨架提取失败');
    }
  } catch (err) {
    loading.close();
    ElMessage.error('骨架提取接口请求失败');
  }
};

const renderDialogCharts = () => {
  if (combinedChartInstance) { combinedChartInstance.dispose(); combinedChartInstance = null; }
  if (splitLeftInstance) { splitLeftInstance.dispose(); splitLeftInstance = null; }
  if (splitRightInstance) { splitRightInstance.dispose(); splitRightInstance = null; }

  nextTick(() => {
    if (skeletonViewMode.value === 'overlay') {
      renderOverlayChart();
    } else {
      renderSplitCharts();
    }
  });
};

const renderOverlayChart = () => {
  if (!combinedChartRef.value || !extractedSegmentData.value) return;
  combinedChartInstance = echarts.init(combinedChartRef.value);

  const dates = extractedSegmentData.value.map(item => item.trade_date);
  const klineData = extractedSegmentData.value.map(item => [
    item.open !== undefined ? item.open : (item.close || 0), item.close || 0,
    item.low !== undefined ? item.low : (item.close || 0), item.high !== undefined ? item.high : (item.close || 0)
  ]);

  let allValues = [];
  extractedSegmentData.value.forEach(item => {
    if (item.high != null) allValues.push(item.high);
    if (item.low != null) allValues.push(item.low);
  });
  const minVal = Math.min(...allValues) * 0.98;
  const maxVal = Math.max(...allValues) * 1.02;

  const baseOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: 40, right: 20, top: 20, bottom: 25 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', min: minVal, max: maxVal },
    series: [{
      name: 'K线', type: 'candlestick', data: klineData,
      itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' }, z: 1
    }]
  };
  combinedChartInstance.setOption(baseOption);

  refreshGraphicAndLine = () => {
    if (!combinedChartInstance) return;
    combinedChartInstance.setOption({
      series: [{
        id: 'skeleton-line', type: 'line',
        data: skeletonPoints.value.map(p => [p.date, p.price]),
        lineStyle: { color: '#409EFF', width: 2.5 },
        symbolSize: 0, z: 2
      }],
      graphic: echarts.util.map(skeletonPoints.value, (dataItem) => {
        const pos = combinedChartInstance.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [dataItem.date, dataItem.price]);
        return {
          type: 'circle', id: dataItem.id,
          x: pos[0], y: pos[1], shape: { r: 7 },
          draggable: true,
          style: { fill: 'rgba(245, 108, 108, 0.9)', stroke: '#fff', lineWidth: 2 }, z: 100,

          ondrag: function () {
            const logicalPos = combinedChartInstance.convertFromPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [this.x, this.y]);
            if (!logicalPos) return;

            let dateIndex = Math.round(logicalPos[0]);
            if (dateIndex < 0) dateIndex = 0;
            if (dateIndex >= extractedSegmentData.value.length) dateIndex = extractedSegmentData.value.length - 1;

            const dataIndex = skeletonPoints.value.findIndex(p => p.id === dataItem.id);
            let minIndex = 0, maxIndex = extractedSegmentData.value.length - 1;
            if (dataIndex > 0) {
              minIndex = extractedSegmentData.value.findIndex(item => item.trade_date === skeletonPoints.value[dataIndex - 1].date) + 1;
            }
            if (dataIndex < skeletonPoints.value.length - 1) {
              maxIndex = extractedSegmentData.value.findIndex(item => item.trade_date === skeletonPoints.value[dataIndex + 1].date) - 1;
            }
            if (dateIndex < minIndex) dateIndex = minIndex;
            if (dateIndex > maxIndex) dateIndex = maxIndex;

            const newDate = extractedSegmentData.value[dateIndex].trade_date;
            const freePrice = logicalPos[1];

            skeletonPoints.value[dataIndex].date = newDate;
            skeletonPoints.value[dataIndex].price = freePrice;

            const exactX = combinedChartInstance.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [newDate, 0])[0];
            this.x = exactX;

            combinedChartInstance.setOption({
              series: [{ id: 'skeleton-line', data: skeletonPoints.value.map(p => [p.date, p.price]) }]
            });
          },
          ondragend: function () { refreshGraphicAndLine(); },
          oncontextmenu: function (e) {
            e.event.preventDefault();
            if (skeletonPoints.value.length <= 2) { ElMessage.warning('至少需要保留两个关键点'); return; }
            skeletonPoints.value = skeletonPoints.value.filter(p => p.id !== dataItem.id);
            combinedChartInstance.setOption({ graphic: { id: dataItem.id, $action: 'remove' } });
            refreshGraphicAndLine();
          }
        };
      })
    });
  };

  refreshGraphicAndLine();

  combinedChartInstance.getZr().off('click');
  combinedChartInstance.getZr().on('click', function (params) {
    if (params.target && params.target.type === 'circle') return;

    const pointInPixel = [params.offsetX, params.offsetY];
    if (combinedChartInstance.containPixel('grid', pointInPixel)) {
      const logicalPos = combinedChartInstance.convertFromPixel({ xAxisIndex: 0, yAxisIndex: 0 }, pointInPixel);
      let dateIndex = Math.round(logicalPos[0]);

      if (dateIndex >= 0 && dateIndex < extractedSegmentData.value.length) {
        const targetDate = extractedSegmentData.value[dateIndex].trade_date;
        const freeTargetPrice = logicalPos[1];

        if (!skeletonPoints.value.some(p => p.date === targetDate)) {
          skeletonPoints.value.push({
            id: generateUid(), date: targetDate, price: freeTargetPrice, weight: 1.0
          });
          skeletonPoints.value.sort((a, b) => new Date(a.date) - new Date(b.date));
          refreshGraphicAndLine();
        }
      }
    }
  });

  if (combinedChartRef.value) combinedChartRef.value.oncontextmenu = () => false;
};

const renderSplitCharts = () => {
  if (!splitLeftRef.value || !splitRightRef.value) return;

  splitLeftInstance = echarts.init(splitLeftRef.value);
  splitRightInstance = echarts.init(splitRightRef.value);

  const dates = extractedSegmentData.value.map(item => item.trade_date);
  const klineData = extractedSegmentData.value.map(item => [
    item.open !== undefined ? item.open : (item.close || 0), item.close || 0,
    item.low !== undefined ? item.low : (item.close || 0), item.high !== undefined ? item.high : (item.close || 0)
  ]);

  let allValues = [];
  extractedSegmentData.value.forEach(item => {
    if (item.high != null) allValues.push(item.high);
    if (item.low != null) allValues.push(item.low);
  });
  const minVal = Math.min(...allValues) * 0.98;
  const maxVal = Math.max(...allValues) * 1.02;

  splitLeftInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: 40, right: 10, top: 10, bottom: 25 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', min: minVal, max: maxVal },
    series: [{
      name: 'K线', type: 'candlestick', data: klineData,
      itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#ec0000', borderColor0: '#00da3c' }
    }]
  });

  splitRightInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: 10, right: 40, top: 10, bottom: 25 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', min: minVal, max: maxVal, position: 'right' },
    series: [{
      type: 'line',
      data: skeletonPoints.value.map(p => [p.date, p.price]),
      lineStyle: { color: '#409EFF', width: 2.5 },
      symbol: 'circle', symbolSize: 8,
      itemStyle: { color: '#F56C6C', borderColor: '#fff', borderWidth: 1.5 }
    }]
  });

  echarts.connect([splitLeftInstance, splitRightInstance]);
};

const updateGraphicPosition = () => {
  if (combinedChartInstance) combinedChartInstance.resize();
  if (splitLeftInstance) splitLeftInstance.resize();
  if (splitRightInstance) splitRightInstance.resize();
  if (skeletonViewMode.value === 'overlay' && typeof refreshGraphicAndLine === 'function') {
    refreshGraphicAndLine();
  }
};

window.addEventListener('resize', updateGraphicPosition);

const confirmSkeletonAndNext = () => {
  skeletonDialogVisible.value = false;

  store.commit("updateNewSearchInfoProperty", {
    key: 'customSkeleton',
    value: skeletonPoints.value
  });

  let maxPrice = -Infinity, minPrice = Infinity;
  skeletonPoints.value.forEach(p => {
    if (p.price > maxPrice) maxPrice = p.price;
    if (p.price < minPrice) minPrice = p.price;
  });

  const autoFeats = [];
  const physicalAmplitude = ((maxPrice - minPrice) / minPrice * 100).toFixed(1);
  let targetAmplitude = Number(physicalAmplitude);

  const existFeat = dynamicFeatures.value.find(f => f.desc === '该形态的整体波动幅度约为');
  if (existFeat && existFeat.hasValue) {
    targetAmplitude = existFeat.value;
  }

  autoFeats.push({
    desc: `该形态的整体波动幅度约为`,
    hasValue: true, value: targetAmplitude, unit: '%', weight: 1.0, selected: true
  });

  autoFeats.push({
    desc: skeletonPoints.value[skeletonPoints.value.length - 1].price > skeletonPoints.value[0].price ? `走势整体呈震荡上行趋势` : `走势整体呈震荡下行趋势`,
    hasValue: false, weight: 1.0, selected: true
  });

  autoFeats.push({
    desc: `共包含 ${skeletonPoints.value.length} 个关键骨架拐点`,
    hasValue: false, weight: 1.0, selected: true
  });

  // 从片段数据计算振幅比和最大回撤
  const segData = extractedSegmentData.value || [];
  if (segData.length >= 2) {
    const closes = segData.map(d => Number(d.close || 0)).filter(v => v > 0);
    const highs = segData.map(d => Number(d.high || 0)).filter(v => v > 0);
    const lows = segData.map(d => Number(d.low || 0)).filter(v => v > 0);
    if (closes.length >= 2 && highs.length > 0 && lows.length > 0) {
      const avgClose = closes.reduce((a, b) => a + b, 0) / closes.length;
      // 振幅比
      const ampRatio = ((Math.max(...highs) - Math.min(...lows)) / avgClose * 100).toFixed(1);
      autoFeats.push({
        desc: `该形态的振幅比约为`, hasValue: true, value: Number(ampRatio), unit: '%', weight: 1.0, selected: true
      });
      // 最大回撤
      let peak = closes[0], maxDD = 0;
      for (const c of closes) {
        if (c > peak) peak = c;
        const dd = (peak - c) / peak;
        if (dd > maxDD) maxDD = dd;
      }
      autoFeats.push({
        desc: `该形态的最大回撤约为`, hasValue: true, value: Number((maxDD * 100).toFixed(1)), unit: '%', weight: 1.0, selected: true
      });
    }
  }

  const { startDate, endDate } = activeBrushData.value;
  extractedFeatures.value = { startDate, endDate };
  dynamicFeatures.value = autoFeats;
  customFeatureText.value = '';

  currentStep.value = 1;
  featureDialogVisible.value = true;
};

const handleExtract = () => {
  if (!activeBrushData.value || !graphRef.value) {
    ElMessage.warning('请先在图表上框选一段片段');
    return;
  }

  if (analysisMode.value === 'MA') {
    openFeatureDialog();
  } else {
    openSkeletonDialog();
  }
};

// ==================== 搜索配置确认弹窗 ====================
const searchConfigDialogVisible = ref(false);
const configPreviewChartRef = ref(null);
let configPreviewChartInstance = null;

// ===== 形态长度倍数（弹窗内"形态长度"滑块），第3步检索确认弹窗使用：窗口天数 = 框选长度 × 倍数 =====
const windowScale = ref(1);
// 实际窗口天数：按框选长度乘倍数取整，并夹取到与后端一致的 [5, 250]
const windowDays = computed(() => {
  const len = extractedSegmentData.value.length;
  if (!len) return 0;
  return Math.min(250, Math.max(5, Math.round(len * windowScale.value)));
});

// 每次进入检索确认弹窗前，重置倍数为 1（即按框选原始长度扫描）
const resetWindowScale = () => {
  windowScale.value = 1;
};

const confirmedFeaturesList = computed(() => {
  const autoFeats = dynamicFeatures.value.filter(f => f.selected).map(f => f.desc);
  const customFeat = customFeatureText.value ? [customFeatureText.value] : [];
  return [...autoFeats, ...customFeat].filter(f => f.trim() !== '');
});

// ======== AI 智能解析特征 ========
const parseCustomPrompt = async () => {
  if (!customFeatureText.value.trim()) return;
  aiParsing.value = true;
  try {
    const res = await axios.post(`${API_BASE_URL}/api/parse_custom_prompt`, {
      text: customFeatureText.value.trim()
    });
    if (res.data.success && res.data.features) {
      aiParsedFeatures.value = res.data.features.map(f => ({
        ...f,
        checked: true
      }));
      aiFeatureConfirmVisible.value = true;
    } else {
      ElMessage.warning(res.data.msg || 'AI 解析失败');
    }
  } catch (e) {
    ElMessage.error('AI 解析请求失败');
  } finally {
    aiParsing.value = false;
  }
};

const confirmAiFeatures = () => {
  const selected = aiParsedFeatures.value.filter(f => f.checked);
  selected.forEach(f => {
    dynamicFeatures.value.push({
      desc: f.desc,
      selected: true,
      weight: 1.0,
      hasValue: f.hasValue || false,
      value: f.hasValue ? f.value : undefined,
      unit: f.hasValue ? f.unit : undefined
    });
  });
  aiFeatureConfirmVisible.value = false;
  aiParsedFeatures.value = [];
  customFeatureText.value = '';
  ElMessage.success(`已引入 ${selected.length} 条 AI 解析特征`);
};

const confirmFeatureAndSearch = () => {
  featureDialogVisible.value = false;
  skeletonDialogVisible.value = false;

  const timestamp = new Date().getTime();
  const { startDate, endDate } = activeBrushData.value;
  saveCurrentBrushInternal(timestamp, startDate, endDate);

  const finalFeatures = dynamicFeatures.value.filter(f => f.selected).map(f => ({
    desc: f.desc, value: f.value, unit: f.unit, hasValue: f.hasValue, weight: f.weight, selected: f.selected
  }));

  store.commit("updateNewSearchInfoProperty", {
    key: 'extractedFeatures',
    value: { auto: finalFeatures, custom: customFeatureText.value }
  });

  resetWindowScale();
  searchConfigDialogVisible.value = true;
  ElMessage.success('形态特征已保存，请确认检索范围和股票池');
};

const renderConfigPreviewChart = () => {
  if (!configPreviewChartRef.value || !extractedSegmentData.value) return;
  if (configPreviewChartInstance) configPreviewChartInstance.dispose();

  configPreviewChartInstance = echarts.init(configPreviewChartRef.value);

  const dates = extractedSegmentData.value.map(item => item.trade_date);
  const prices = extractedSegmentData.value.map(item => item.MA4);

  const minVal = Math.min(...prices) * 0.98;
  const maxVal = Math.max(...prices) * 1.02;

  configPreviewChartInstance.setOption({
    grid: { left: 10, right: 10, top: 10, bottom: 10 },
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', min: minVal, max: maxVal, show: false },
    series: [
      {
        type: 'line', data: prices, smooth: true,
        lineStyle: { type: 'dashed', color: '#e4e7ed', width: 2 },
        symbol: 'none'
      },
      {
        type: 'line',
        data: skeletonPoints.value.map(p => [p.date, p.price]),
        lineStyle: { color: '#409EFF', width: 2 },
        symbol: 'circle', symbolSize: 6,
        itemStyle: { color: '#F56C6C', borderColor: '#fff', borderWidth: 1 }
      }
    ]
  });
};

// ==================== 截图管理 ====================
const imageList = ref([]);
const loading = ref(true);

const handleImageError = (img) => {
  img.url = 'https://picsum.photos/300/200?grayscale&blur=2';
};

const fetchImages = async () => {
  const timestamp = new Date().getTime();
  const folderName = store.state.newSearchInfo.baseFolder;

  try {
    loading.value = true;
    const params = new URLSearchParams();
    params.append('timestamp', timestamp);
    params.append('folder', folderName);
    const response = await axios.get(`${API_BASE_URL}/get_all_screenshots`, { params });
    if (response.data.success) {
      imageList.value = response.data.images.map(image => ({
        ...image,
        url: `${API_BASE_URL}/get_screenshot/${encodeURIComponent(image.filename)}`
      }));
    }
  } catch (err) {
    console.error('获取图片失败:', err);
  } finally {
    loading.value = false;
  }
};

const deleteServerFiles = () => {
  ElMessageBox.confirm(
      '确定要删除服务器上的指定文件夹数据吗？此操作不可恢复。',
      '警告',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/delete-files`, { folderPath: '/public/savepng' });
      if (response.data.success) {
        ElMessage.success('服务器文件夹数据已成功删除');
        fetchImages();
        savedBrushAreas.value = [];
        savedBrushTimeRanges.value = [];
        currentStep.value = 0;
        resultType.value = false;
      } else {
        ElMessage.error('删除失败：' + response.data.msg);
      }
    } catch (err) {
      ElMessage.error('删除操作失败，请重试');
    }
  }).catch(() => {});
};


// ==================== 保存选区与截图 ====================
const saveCurrentBrushInternal = (timestamp, startDate, endDate) => {
  if (!startDate || !endDate || !timestamp) {
    console.error("保存失败：缺少关键参数", { timestamp, startDate, endDate });
    return;
  }

  savedBrushTimeRanges.value.push({
    code: graphCode1.value,
    startDate: startDate,
    endDate: endDate,
    saveTime: timestamp
  });

  if (graphRef.value && graphRef.value.$refs.chartRef111) {
    const chartDom = graphRef.value.$refs.chartRef111;
    html2canvas(chartDom, { useCORS: true, scale: 2 }).then(canvas => {
      canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('file', blob, `${graphCode1.value}_brush_${timestamp}.png`);

        axios.post(`${API_BASE_URL}/save_screenshot?timestamp=${timestamp}`, formData);

        axios.post(`${API_BASE_URL}/save_brush_record`, {
          timestamp: timestamp,
          startDate: startDate,
          endDate: endDate,
          dynamicFeatures: dynamicFeatures.value,
          analysisMode: analysisMode.value,
          segmentData: extractedSegmentData.value,
          custom_skeleton: skeletonPoints.value.map(p => ({
            date: p.date,
            price: p.price,
            weight: p.weight || 1.0
          })),
          extracted_features: dynamicFeatures.value.filter(f => f.selected).map(f => ({
            desc: f.desc,
            hasValue: f.hasValue || false,
            value: f.value,
            unit: f.unit,
            weight: f.weight
          }))
        });
      }, 'image/png');
    });
  }
};


// ==================== 搜索执行 ====================
const executeFinalSearch = async () => {
  searchConfigDialogVisible.value = false;
  currentStep.value = 2;
  await fetchImages();
  await doResultWithLLM();
};

const doResultWithLLM = async () => {
  console.log("准备触发搜索，当前 Vuex 状态:", store.state.baseInfo);

  let result = store.state.searchInfo.stockList.map(item => item.code);
  if (!result || result.length === 0) {
    result = store.state.stockList.filter(item => item.isSelected).map(item => item.code);
    if (result.length === 0) {
      result = store.state.stockList.slice(0, 100).map(item => item.code);
    }
  }

  const oriLines = store.state.modeInfo.lines;
  const maNumbers = oriLines.filter(item => item.startsWith('MA')).map(maItem => Number(maItem.slice(2)));

  let finalBrushRanges = toRaw(savedBrushTimeRanges).value;
  if (finalBrushRanges.length === 0) {
    finalBrushRanges = [{ code: graphCode1.value, startDate: '2024-01-01', endDate: '2024-02-01' }];
  }

  let searchStart = store.state.searchInfo.searchStartDate;
  let searchEnd = store.state.searchInfo.searchEndDate;

  if (searchStart instanceof Date) searchStart = formatDateToLocal(searchStart);
  if (searchEnd instanceof Date) searchEnd = formatDateToLocal(searchEnd);

  if (!searchStart || searchStart === '--') searchStart = '2016-01-01';
  if (!searchEnd || searchEnd === '--') searchEnd = '2024-12-31';

  store.commit("updateNewSearchInfo", {
    savedBrushTimeRanges: finalBrushRanges,
    recentNDaysValue: recentNDaysValue.value,
    lines: maNumbers,
  });

  store.state.newSearchInfo.analysisMode = analysisMode.value;

  store.commit("updateBaseInfo", {
    isMode: true, isStock: false, currentFunction: "推荐模式查找",
    isDisabled: true, isHistorySearch: false, isChooseStock: true,
    isHistorySearchNew: true
  });

  const updatedTarget = toRaw(store.state.newSearchInfo);
  resultType.value = true;
  const timestamp = new Date().getTime();

  const llmLoading = ElMessage({
    message: '大语言模型正在解析语义标签，生成滑窗过滤规则...',
    type: 'warning', duration: 0,
  });

  try {
    const semanticFeatures = updatedTarget.extractedFeatures || { auto: [], custom: '' };

    const requestParams = {
      target_code: updatedTarget.savedBrushTimeRanges[0].code,
      target_start_date: updatedTarget.savedBrushTimeRanges[0].startDate,
      target_end_date: updatedTarget.savedBrushTimeRanges[0].endDate,
      search_start_date: searchStart,
      search_end_date: searchEnd,
      ma_list: updatedTarget.lines,
      stock_pool: result,
      analysis_mode: updatedTarget.analysisMode || 'MA',
      window_size: windowDays.value || undefined,
      custom_skeleton: updatedTarget.customSkeleton || [],
      semantic_features: {
        tags: semanticFeatures.auto,
        custom_prompt: semanticFeatures.custom
      }
    };

    const response = await axios.post(
        `${API_BASE_URL}/find_similar_stocks_llm?timestamp=${timestamp}`,
        requestParams,
        { headers: { 'Content-Type': 'application/json' } }
    );

    llmLoading.close();

    if (response.data.result) {
      const base_periods = response.data.base_ma_periods || maNumbers;
      const maFields = base_periods.map(period => `MA${period}`);

      response.data.result.forEach(stock => {
        if (!stock.recent_data || stock.recent_data.length === 0) return;
        stock.recent_data_raw = JSON.parse(JSON.stringify(stock.recent_data));

        let twoDArray = stock.recent_data.map(item => maFields.map(field => item[field]));
        const rows = twoDArray.length;
        const cols = twoDArray[0].length;
        const transposed = [];
        for (let j = 0; j < cols; j++) {
          transposed[j] = [];
          for (let i = 0; i < rows; i++) transposed[j][i] = twoDArray[i][j];
        }
        stock.recent_data = transposed;
      });

      store.state.sim_stock_list = response.data.result;
      store.state.resultInfo = { filter_stats: response.data.filter_stats };
      store.state.newSearchInfo.baseSegmentData = response.data.base_segment || [];

      console.log("准备存入 Vuex 的数据:", response.data.filter_stats);
      store.commit("updateBaseInfo", {
        isChooseStock: true,
        isHistorySearchNew: true,
        filter_stats: response.data.filter_stats,
      });

      currentStep.value = 3;
      ElMessage.success(`历史语义检索完成！在 ${searchStart} 至 ${searchEnd} 期间共找到 ${response.data.result.length} 个匹配片段。`);
      return { success: true, data: response.data };
    }
  } catch (err) {
    console.error("前端报错:", err);
    llmLoading.close();
    ElMessage.error('检索失败，请检查控制台报错信息');
    return { success: false, message: '网络请求错误' };
  }
};


// ==================== 个性化模型训练 ====================
// ==================== 训练集清洗舱 ====================
const trainCleanDialogVisible = ref(false);
const positiveSamples = ref([]);
const negativeSamples = ref([]);

// 清洗舱走势图 ref 管理
const cleanChartRefs = { pos: [], neg: [] };
const setCleanChartRef = (el, type, idx) => {
  if (el) cleanChartRefs[type][idx] = el;
};

// 渲染清洗舱走势图
const renderCleanPodCharts = () => {
  nextTick(() => {
    setTimeout(() => {
      const mode = (store.state.newSearchInfo.analysisMode || 'MA').toUpperCase();
      [['pos', positiveSamples.value], ['neg', negativeSamples.value]].forEach(([type, samples]) => {
        samples.forEach((sample, idx) => {
          const dom = cleanChartRefs[type][idx];
          if (!dom) return;
          let chart = echarts.getInstanceByDom(dom);
          if (chart) chart.dispose();
          chart = echarts.init(dom);
          const rawData = sample.recent_data_raw;
          if (!rawData || rawData.length === 0) return;

          const allVals = [];
          if (mode === 'MA') {
            ['MA4','MA8','MA12','MA16','MA20','MA47'].forEach(ma => rawData.forEach(d => { const v = Number(d[ma]); if (v > 0) allVals.push(v); }));
          } else {
            rawData.forEach(d => ['open','close','high','low'].forEach(k => { const v = Number(d[k]); if (v > 0) allVals.push(v); }));
          }
          const dMin = allVals.length > 0 ? Math.min(...allVals) : 0;
          const dMax = allVals.length > 0 ? Math.max(...allVals) : 1;
          const pad = (dMax - dMin) * 0.1 || 1;

          let series;
          if (mode === 'MA') {
            const maFields = ['MA4','MA8','MA12','MA16','MA20','MA47'].filter(k => rawData[0] && rawData[0][k] != null);
            const colors = { MA4:'#cd1f0e', MA8:'#edbf09', MA12:'#62c613', MA16:'#1286ff', MA20:'#9f12ff', MA47:'#000000' };
            series = maFields.map(ma => ({ name: ma, type: 'line', showSymbol: false, lineStyle: { width: 1, color: colors[ma] }, data: rawData.map(d => Number(d[ma])) }));
          } else {
            series = [{ type: 'candlestick', data: rawData.map(d => [Number(d.open), Number(d.close), Number(d.low), Number(d.high)]) }];
          }

          chart.setOption({
            animation: false,
            grid: { left: 2, right: 2, top: 4, bottom: 2 },
            xAxis: { type: 'category', show: false, boundaryGap: false },
            yAxis: { type: 'value', show: false, min: dMin - pad, max: dMax + pad, scale: true },
            series
          });
        });
      });
    }, 200);
  });
};

// 监听跨组件触发的弹窗信号
watch(() => store.state.showTrainCleanDialog, (val) => {
  if (val) {
    prepareTrainingPool();
    trainCleanDialogVisible.value = true;
    store.state.showTrainCleanDialog = false; // 重置
  }
});

const prepareTrainingPool = () => {
  const pool = store.state.trainingPool || {};
  const tagMap = { '勾选': 'primary', '勾选仿真': 'primary', '低分历史': 'danger', '低分仿真': 'info' };
  const getTag = (source) => {
    if (tagMap[source]) return tagMap[source];
    if (!source) return '';
    if (source.includes('低分')) return 'danger';
    if (source.includes('勾选')) return 'primary';
    return '';
  };
  positiveSamples.value = [
    ...(pool.positiveChecked || []).map(s => ({ ...s, sourceTag: getTag(s.source) })),
    ...(pool.positiveRated || []).map(s => ({ ...s, sourceTag: getTag(s.source) })),
    ...(pool.positiveSynth || []).map(s => ({ ...s, sourceTag: getTag(s.source) })),
  ];
  negativeSamples.value = [
    ...(pool.negativeRated || []).map(s => ({ ...s, sourceTag: getTag(s.source) })),
    ...(pool.negativeSynth || []).map(s => ({ ...s, sourceTag: getTag(s.source) })),
  ];
};

const removeSample = (type, idx) => {
  if (type === 'positive') positiveSamples.value.splice(idx, 1);
  else negativeSamples.value.splice(idx, 1);
  // 重置 ref 数组以匹配新长度
  cleanChartRefs.pos = [];
  cleanChartRefs.neg = [];
  renderCleanPodCharts();
};

const aiSynthesizeMore = async () => {
  const seeds = positiveSamples.value.slice(0, 2).map(s => s.recent_data_raw).filter(Boolean);
  if (seeds.length === 0) {
    ElMessage.warning('正样本盒为空，无法合成');
    return;
  }
  try {
    const res = await axios.post(`${API_BASE_URL}/api/generate_synthetic_samples`, {
      seeds,
      condition_skeleton: store.state.newSearchInfo.customSkeleton || [],
      condition_features: (store.state.newSearchInfo.extractedFeatures?.auto || []).map(f =>
        typeof f === 'string' ? f : `${f.desc || ''} ${f.hasValue && f.value != null ? f.value + (f.unit || '') : ''}`.trim()),
      analysis_mode: analysisMode.value,
      ma_list: [4, 8, 12, 16, 20, 47],
      num_samples: 3
    });
    if (res.data.success && res.data.synthetic_results) {
      res.data.synthetic_results.forEach(s => {
        positiveSamples.value.push({
          stockCode: s.sample_id, stockName: s.sample_id,
          userRating: 0, source: '高分仿真', sourceTag: 'warning',
          recent_data_raw: s.recent_data_raw
        });
      });
      ElMessage.success(`AI 合成了 ${res.data.synthetic_results.length} 个新样本`);
      cleanChartRefs.pos = [];
      renderCleanPodCharts();
    }
  } catch (e) {
    ElMessage.error('AI 合成失败');
  }
};

// YOLO 训练（含数据增强）
const yoloTraining = ref(false);
const confirmYoloTrain = async () => {
  if (positiveSamples.value.length === 0) {
    ElMessage.warning('正样本不能为空');
    return;
  }

  try {
    const { value: modeName } = await ElMessageBox.prompt(
        `将用 ${positiveSamples.value.length} 个正样本 + 数据增强训练 YOLO 检测器。请输入模型名称：`,
        'YOLO 训练',
        { confirmButtonText: '开始训练', cancelButtonText: '取消', inputPattern: /\S+/, inputErrorMessage: '名称不能为空' }
    );

    const trainingSegments = positiveSamples.value.map(s => s.recent_data_raw).filter(Boolean);
    const negativeSegments = negativeSamples.value.map(s => s.recent_data_raw).filter(Boolean);

    yoloTraining.value = true;
    trainCleanDialogVisible.value = false;

    const res = await axios.post(`${API_BASE_URL}/api/train_yolo`, {
      mode_index: modeName,
      segments: trainingSegments,
      negative_segments: negativeSegments,
      ma_list: [4, 8, 12, 16, 20, 47],
      analysis_mode: analysisMode.value,
      custom_skeleton: store.state.newSearchInfo.customSkeleton || skeletonPoints.value || [],
      epochs: 80,
    });

    if (res.data.success) {
      ElMessage.success(`YOLO 模型【${modeName}】训练完成！正样本(含增强) ${res.data.pos_count} 张`);
      await store.dispatch('fetchModeListSelf');
    } else {
      ElMessage.error(res.data.msg || 'YOLO 训练失败');
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('YOLO 训练失败: ' + (e.response?.data?.msg || e.message));
  } finally {
    yoloTraining.value = false;
  }
};

const confirmTrainFromCleanPod = async () => {  if (positiveSamples.value.length === 0) {
    ElMessage.warning('正样本不能为空');
    return;
  }
  trainCleanDialogVisible.value = false;

  try {
    const { value: modeName } = await ElMessageBox.prompt(
        `确认使用 ${positiveSamples.value.length} 个正样本训练。请输入模式名称：`,
        '生成个性化模型',
        { confirmButtonText: '开始训练', cancelButtonText: '取消', inputPattern: /\S+/, inputErrorMessage: '名称不能为空' }
    );

    const trainingSegments = positiveSamples.value.map(s => s.recent_data_raw).filter(Boolean);
    const negativeSegments = negativeSamples.value.map(s => s.recent_data_raw).filter(Boolean);
    const res = await axios.post(`${API_BASE_URL}/train_custom_model`, {
      name: modeName,
      segments: trainingSegments,
      negative_segments: negativeSegments,
      ma_list: [4, 8, 12, 16, 20, 47],
      analysisMode: analysisMode.value,
      custom_skeleton: store.state.newSearchInfo.customSkeleton || skeletonPoints.value || [],
    });

    if (res.data.success) {
      ElMessage.success(`模式【${modeName}】训练成功！`);
      await store.dispatch('fetchModeListSelf');
      currentStep.value = 4;
      savedBrushAreas.value = [];
      savedBrushTimeRanges.value = [];
      store.state.selectedTrainingSamples = [];
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('训练失败，请检查控制台');
    }
  }
};

// 生成个性化模型按钮 → 先弹出训练集清洗舱
const handleTrainCustomMode = () => {
  const selectedSamples = store.state.selectedTrainingSamples || [];
  if (savedBrushTimeRanges.value.length === 0 && selectedSamples.length === 0) {
    // 也检查 trainingPool 是否有评分数据
    const pool = store.state.trainingPool || {};
    const poolTotal = (pool.positiveChecked?.length || 0) + (pool.positiveRated?.length || 0) + (pool.positiveSynth?.length || 0);
    if (poolTotal === 0) {
      ElMessage.warning("请先框选片段、勾选结果或对结果打分");
      return;
    }
  }
  // 如果有框选片段但 trainingPool 没有，把框选片段加入正样本
  if (savedBrushTimeRanges.value.length > 0 && (store.state.trainingPool?.positiveChecked?.length || 0) === 0) {
    const checkedSamples = [];
    for (const range of savedBrushTimeRanges.value) {
      if (graphRef.value) {
        const segmentData = graphRef.value.getDataByRange(range.startDate, range.endDate);
        if (segmentData && segmentData.length > 0) {
          checkedSamples.push({
            stockCode: range.code || graphCode1.value, stockName: '基准片段',
            startDate: range.startDate, endDate: range.endDate,
            userRating: 0, source: '勾选', recent_data_raw: segmentData
          });
        }
      }
    }
    store.commit('updateTrainingPool', { positiveChecked: checkedSamples });
  }
  prepareTrainingPool();
  trainCleanDialogVisible.value = true;
};


// ==================== 计算属性 ====================
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


// ==================== 历史图片还原 ====================
const handleImageClick = async (img) => {
  const match = (img.filename || img.url).match(/_brush_(\d+)\.png/);
  if (!match) return;
  const timestamp = parseInt(match[1]);

  try {
    const res = await axios.post(`${API_BASE_URL}/get_brush_info`, { timestamp });

    if (res.data.success) {
      const { startDate, endDate, dynamicFeatures: savedParams, skeletonPoints: savedPoints, custom_skeleton, extracted_features, segmentData, analysisMode: savedMode } = res.data.info;

      activeBrushData.value = { startDate, endDate, type: 'lineX' };
      skeletonPoints.value = custom_skeleton || savedPoints || [];
      dynamicFeatures.value = savedParams || [];
      extractedSegmentData.value = segmentData || [];
      if (savedMode) analysisMode.value = savedMode;
      extractedFeatures.value = { startDate, endDate, autoFeatures: (extracted_features || dynamicFeatures.value).map(f => f.desc || f) };

      await nextTick();
      featureDialogVisible.value = true;
      ElMessage.success('已加载历史选区参数');
    }
  } catch (e) {
    ElMessage.error('加载历史记录失败');
  }
};


// ==================== Watch 监听器 ====================
watch(value1, (newVal) => {
  if (newVal && newVal.length === 2 && newVal[0] instanceof Date && !isNaN(newVal[0].getTime()) && newVal[1] instanceof Date && !isNaN(newVal[1].getTime())) {
    const formattedStartDate = formatDateToLocal(newVal[0]);
    const formattedEndDate = formatDateToLocal(newVal[1]);
    store.state.modeInfo.startDate = formattedStartDate;
    store.state.modeInfo.endDate = formattedEndDate;
    value3.value = newVal;
    value2.value = newVal;
  } else {
    store.state.modeInfo.startDate = null;
    store.state.modeInfo.endDate = null;
    value3.value = [];
    value2.value = [];
  }
});

watch(searchInfo, (newVal) => {
  value2.value = [
    newVal.searchStartDate ? new Date(newVal.searchStartDate) : null,
    newVal.searchEndDate ? new Date(newVal.searchEndDate) : null
  ];
  if (baseInfo.isHistory === false) {
    tableDataRecent.value = newVal.stockList;
  }
});

watch(() => store.state.newSearchInfo, (newVal) => {
  recentNDaysValue.value = newVal.recentNDaysValue;
  fetchImages();
}, { immediate: true, deep: true });

watch(() => store.state.baseInfo.isMode, (newValue) => {
  if (newValue === true && store.state.modeInfo.index === "BA2") {
    resultType.value = false;
    resultMode.value = true;
    resultStock.value = false;
  }
  if (newValue === false) {
    resultType.value = true;
    resultMode.value = false;
    resultStock.value = false;
  }
});

watch(() => baseInfo.isChoose, (newValue) => {
  if (newValue === true) {
    resultType.value = false;
    resultMode.value = false;
    resultStock.value = true;
  } else {
    resultType.value = true;
    resultMode.value = false;
    resultStock.value = false;
  }
});

watch(() => baseInfo.isSection, (newValue) => {
  if (newValue === false) {
    baseInfo.isHistory = false;
    baseInfo.isCross = false;
  }
});

watch(sidebarWidth, () => {
  nextTick(() => {
    const currentPage = document.getElementById("current-page");
    if (currentPage) {
      const tables = currentPage.querySelectorAll(".el-table__header-wrapper");
      tables.forEach(() => {
        window.dispatchEvent(new Event("resize"));
      });
    }
  });
});


// ==================== 生命周期 ====================
onMounted(() => {
  fetchImages();
});

</script>

<style src="@/styles/basic.css">
.image-gallery-container {
  display: flex;
  height: 100%;
  align-items: center;
  padding: 20px 15px 0 15px;
  overflow-x: auto;
  scrollbar-width: none;
  cursor: pointer !important;
}

.image-gallery, .screenshot-img {
  cursor: pointer !important;
  pointer-events: auto !important;
}
.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 20px;
}

.screenshot-img {
  max-width: 200px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
  overflow: hidden;
}

.screenshot-img:hover {
  transform: scale(1.02);
}

.image-name {
  margin: 5px 0 0 0;
  font-size: 14px;
  color: #666;
}

.empty-state {
  width: 100%;
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading-state {
  width: 100%;
  text-align: center;
  padding: 40px;
  color: #666;
}
</style>
