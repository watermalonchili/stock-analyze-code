<!--
  选择待查找股票集合组件
  -->
<template>
  <div id="dialog-page">
    <el-dialog
      :model-value="visible"
      @update:model-value="onUpdateVisible"
      :title="dialogTitle"
      width="850px"
      :before-close="handleClose"
      style="margin-top: 60px;"
      class="modecards-dialog-tour"
    >
      <!-- 多头排列基本信息表格 -->
      <div style="display: flex; align-items: center; font-size: 13px; color:#000000; padding: 1px; width: 800px; margin-left: 0px; margin-top: -40px;">
        <span style="flex: 1;"></span>
        <el-button @click="toggleQaMode" size="small" type="primary" style="margin-left: 8px;">
          <div>切换问答类型</div>
        </el-button>
      </div>

      <!-- 数据分类设置区 -->
      <div style="margin-top: 10px; width: 815px; display: flex;">
        <div class="scrollable-div" style="border: #d6d6d6 1px solid; width: 815px; height: 445px; margin-left: 20px; padding: 10px; overflow-y: auto; border-radius: 4px;">
          <div v-if="currentCard === 1">
            <!-- 图片问答轮播图 - 仅当 qaMode 为 'image' 时显示 -->
            <el-carousel :interval="200000" arrow="always" style="width:100%; height: 440px;" v-if="qaMode === 'image'" indicator-position="none">
              <!-- 轮播项1 -->
              <el-carousel-item style="height: 430px;">
                <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: 10px;">以下两张图片的框选区域是否相似？</div>
                <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 7px; width: 760px;" class="custom-table-header">
                  <el-table-column label="区域1" width="380px">
                    <template #default="{ row }">
                      <img :src="row.imagePath1" alt="分类1图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                  <el-table-column label="区域2" width="380px" style="margin-left: 5px;">
                    <template #default="{ row }">
                      <img :src="row.imagePath2" alt="分类2图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                </el-table>
                <div style="display: flex;">
                  <el-button :plain="simState !== 1" @click="simState = 1" type="success" style="margin-top: 10px; margin-left: 10px; width: 370px;">是</el-button>
                  <el-button :plain="simState !== 2" @click="simState = 2" type="warning" style="margin-top: 10px; margin-left: 10px; width: 370px;">否</el-button>
                </div>

                <!-- 选择"是"时显示的内容 -->
                <div v-if="simState === 1" style="margin-top: 15px; margin-left: 20px;">
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px;">如果【10分】代表两个框选区域完全相同，请给出上述区域的相似度评分：</div>
                    <el-input-number v-model="similarityScore" :min="0" :max="10" style="width: 100px; margin-left: 10px; height: 30px; margin-bottom: 10px; margin-top: -5px;"></el-input-number>
                  </div>
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: -2px;">上述相似片段在哪些部分仍有差异？</div>
                  <el-checkbox-group v-model="similarityReasons1" style="margin-left: 10px;display: flex;" >
                    <el-checkbox :label="1">均线发散程度变化</el-checkbox>
                    <el-checkbox :label="2">均线排列方式</el-checkbox>
                    <el-checkbox :label="3">框选区域的长度</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                  </div>

                  <div v-if="similarityReasons1.includes(4)" style="margin-top: -5px; display: flex;">
                    <span style="color: black; margin-right: 10px; font-size: 13px; margin-top: -3px;">请说明其他差异情况：</span>
                    <el-input v-model="similarityReasonCustom1" placeholder="请输入差异情况描述" style="width: 300px; margin-top: -10px; font-size: 12px;"></el-input>
                  </div>
                </div>

                <!-- 选择"否"时显示的内容 -->
                <div v-if="simState === 2" style="margin-top: 15px; display: flex;">
                  <div style="color: black; font-size: 13px; margin-left: 20px; margin-top: -1px;">上述片段的主要区别是？</div>
                  <el-checkbox-group v-model="differenceReasons1" style="margin-left: 10px; margin-bottom: 10px; display: flex;">
                    <el-checkbox :label="1">均线排列方式不同</el-checkbox>
                    <el-checkbox :label="2">股价趋势相反</el-checkbox>
                    <el-checkbox :label="3">时间周期差异大</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                </div>
                <div v-if="differenceReasons1.includes(4)" style="margin-top: -15px;">
                  <span style="margin-left: -325px; font-size: 13px; color: #000000;">请说明其他区别：</span>
                  <el-input v-model="differenceReasonCustom1" placeholder="请输入区别描述" style="width: 300px;"></el-input>
                </div>
              </el-carousel-item>
              <!-- 轮播项2 -->
              <el-carousel-item style="height: 430px;">
                <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: 10px;">以下两张图片的框选区域是否相似？</div>
                <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 7px; width: 760px;" class="custom-table-header">
                  <el-table-column label="区域1" width="380px">
                    <template #default="{ row }">
                      <img :src="row.imagePath3" alt="分类1图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                  <el-table-column label="区域2" width="380px" style="margin-left: 5px;">
                    <template #default="{ row }">
                      <img :src="row.imagePath4" alt="分类2图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                </el-table>
                <div style="display: flex;">
                  <el-button :plain="simState1 !== 1" @click="simState1 = 1" type="success" style="margin-top: 10px; margin-left: 10px; width: 370px;">是</el-button>
                  <el-button :plain="simState1 !== 2" @click="simState1 = 2" type="warning" style="margin-top: 10px; margin-left: 10px; width: 370px;">否</el-button>
                </div>

                <!-- 选择"是"时显示的内容 -->
                <div v-if="simState1 === 1" style="margin-top: 15px; margin-left: 20px;">
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px;">如果【10分】代表两个框选区域完全相同，请给出上述区域的相似度评分：</div>
                    <el-input-number v-model="similarityScore1" :min="0" :max="10" style="width: 100px; margin-left: 10px; height: 30px; margin-bottom: 10px; margin-top: -5px;"></el-input-number>
                  </div>
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: -2px;">上述相似片段在哪些部分仍有差异？</div>
                  <el-checkbox-group v-model="similarityReasons2" style="margin-left: 10px;display: flex;" >
                    <el-checkbox :label="1">均线发散程度变化</el-checkbox>
                    <el-checkbox :label="2">均线排列方式</el-checkbox>
                    <el-checkbox :label="3">框选区域的长度</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                  </div>

                  <div v-if="similarityReasons2.includes(4)" style="margin-top: -5px; display: flex;">
                    <span style="color: black; margin-right: 10px; font-size: 13px; margin-top: -3px;">请说明其他差异情况：</span>
                    <el-input v-model="similarityReasonCustom2" placeholder="请输入差异情况描述" style="width: 300px; margin-top: -10px; font-size: 12px;"></el-input>
                  </div>
                </div>

                <!-- 选择"否"时显示的内容 -->
                <div v-if="simState1 === 2" style="margin-top: 15px; display: flex;">
                  <div style="color: black; font-size: 13px; margin-left: 20px; margin-top: -1px;">上述片段的主要区别是？</div>
                  <el-checkbox-group v-model="differenceReasons2" style="margin-left: 10px; margin-bottom: 10px; display: flex;">
                    <el-checkbox :label="1">均线排列方式不同</el-checkbox>
                    <el-checkbox :label="2">股价趋势相反</el-checkbox>
                    <el-checkbox :label="3">时间周期差异大</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                </div>
                <div v-if="differenceReasons2.includes(4)" style="margin-top: -15px;">
                  <span style="margin-left: -325px; font-size: 13px; color: #000000;">请说明其他区别：</span>
                  <el-input v-model="differenceReasonCustom2" placeholder="请输入区别描述" style="width: 300px;"></el-input>
                </div>
              </el-carousel-item>
              <!-- 轮播项3 -->
              <el-carousel-item style="height: 430px;">
                <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: 10px;">以下两张图片的框选区域是否相似？</div>
                <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 7px; width: 760px;" class="custom-table-header">
                  <el-table-column label="区域1" width="380px">
                    <template #default="{ row }">
                      <img :src="row.imagePath5" alt="分类1图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                  <el-table-column label="区域2" width="380px" style="margin-left: 5px;">
                    <template #default="{ row }">
                      <img :src="row.imagePath6" alt="分类2图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                </el-table>
                <div style="display: flex;">
                  <el-button :plain="simState2 !== 1" @click="simState2 = 1" type="success" style="margin-top: 10px; margin-left: 10px; width: 370px;">是</el-button>
                  <el-button :plain="simState2 !== 2" @click="simState2 = 2" type="warning" style="margin-top: 10px; margin-left: 10px; width: 370px;">否</el-button>
                </div>

                <!-- 选择"是"时显示的内容 -->
                <div v-if="simState2 === 1" style="margin-top: 15px; margin-left: 20px;">
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px;">如果【10分】代表两个框选区域完全相同，请给出上述区域的相似度评分：</div>
                    <el-input-number v-model="similarityScore2" :min="0" :max="10" style="width: 100px; margin-left: 10px; height: 30px; margin-bottom: 10px; margin-top: -5px;"></el-input-number>
                  </div>
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: -2px;">上述相似片段在哪些部分仍有差异？</div>
                  <el-checkbox-group v-model="similarityReasons3" style="margin-left: 10px;display: flex;" >
                    <el-checkbox :label="1">均线发散程度变化</el-checkbox>
                    <el-checkbox :label="2">均线排列方式</el-checkbox>
                    <el-checkbox :label="3">框选区域的长度</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                  </div>

                  <div v-if="similarityReasons3.includes(4)" style="margin-top: -5px; display: flex;">
                    <span style="color: black; margin-right: 10px; font-size: 13px; margin-top: -3px;">请说明其他差异情况：</span>
                    <el-input v-model="similarityReasonCustom3" placeholder="请输入差异情况描述" style="width: 300px; margin-top: -10px; font-size: 12px;"></el-input>
                  </div>
                </div>

                <!-- 选择"否"时显示的内容 -->
                <div v-if="simState2 === 2" style="margin-top: 15px; display: flex;">
                  <div style="color: black; font-size: 13px; margin-left: 20px; margin-top: -1px;">上述片段的主要区别是？</div>
                  <el-checkbox-group v-model="differenceReasons3" style="margin-left: 10px; margin-bottom: 10px; display: flex;">
                    <el-checkbox :label="1">均线排列方式不同</el-checkbox>
                    <el-checkbox :label="2">股价趋势相反</el-checkbox>
                    <el-checkbox :label="3">时间周期差异大</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                </div>
                <div v-if="differenceReasons3.includes(4)" style="margin-top: -15px;">
                  <span style="margin-left: -325px; font-size: 13px; color: #000000;">请说明其他区别：</span>
                  <el-input v-model="differenceReasonCustom3" placeholder="请输入区别描述" style="width: 300px;"></el-input>
                </div>
              </el-carousel-item>
              <!-- 轮播项4 -->
              <el-carousel-item style="height: 430px;">
                <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: 10px;">以下两张图片的框选区域是否相似？</div>
                <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 7px; width: 760px;" class="custom-table-header">
                  <el-table-column label="区域1" width="380px">
                    <template #default="{ row }">
                      <img :src="row.imagePath7" alt="分类1图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                  <el-table-column label="区域2" width="380px" style="margin-left: 5px;">
                    <template #default="{ row }">
                      <img :src="row.imagePath8" alt="分类2图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                </el-table>
                <div style="display: flex;">
                  <el-button :plain="simState3 !== 1" @click="simState3 = 1" type="success" style="margin-top: 10px; margin-left: 10px; width: 370px;">是</el-button>
                  <el-button :plain="simState3 !== 2" @click="simState3 = 2" type="warning" style="margin-top: 10px; margin-left: 10px; width: 370px;">否</el-button>
                </div>

                <!-- 选择"是"时显示的内容 -->
                <div v-if="simState3 === 1" style="margin-top: 15px; margin-left: 20px;">
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px;">如果【10分】代表两个框选区域完全相同，请给出上述区域的相似度评分：</div>
                    <el-input-number v-model="similarityScore3" :min="0" :max="10" style="width: 100px; margin-left: 10px; height: 30px; margin-bottom: 10px; margin-top: -5px;"></el-input-number>
                  </div>
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: -2px;">上述相似片段在哪些部分仍有差异？</div>
                  <el-checkbox-group v-model="similarityReasons4" style="margin-left: 10px;display: flex;" >
                    <el-checkbox :label="1">均线发散程度变化</el-checkbox>
                    <el-checkbox :label="2">均线排列方式</el-checkbox>
                    <el-checkbox :label="3">框选区域的长度</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                  </div>

                  <div v-if="similarityReasons4.includes(4)" style="margin-top: -5px; display: flex;">
                    <span style="color: black; margin-right: 10px; font-size: 13px; margin-top: -3px;">请说明其他差异情况：</span>
                    <el-input v-model="similarityReasonCustom4" placeholder="请输入差异情况描述" style="width: 300px; margin-top: -10px; font-size: 12px;"></el-input>
                  </div>
                </div>

                <!-- 选择"否"时显示的内容 -->
                <div v-if="simState3 === 2" style="margin-top: 15px; display: flex;">
                  <div style="color: black; font-size: 13px; margin-left: 20px; margin-top: -1px;">上述片段的主要区别是？</div>
                  <el-checkbox-group v-model="differenceReasons4" style="margin-left: 10px; margin-bottom: 10px; display: flex;">
                    <el-checkbox :label="1">均线排列方式不同</el-checkbox>
                    <el-checkbox :label="2">股价趋势相反</el-checkbox>
                    <el-checkbox :label="3">时间周期差异大</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                </div>
                <div v-if="differenceReasons4.includes(4)" style="margin-top: -15px;">
                  <span style="margin-left: -325px; font-size: 13px; color: #000000;">请说明其他区别：</span>
                  <el-input v-model="differenceReasonCustom4" placeholder="请输入区别描述" style="width: 300px;"></el-input>
                </div>
              </el-carousel-item>
              <!-- 轮播项5 -->
              <el-carousel-item style="height: 430px;">
                <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: 10px;">以下两张图片的框选区域是否相似？</div>
                <el-table :data="tableData1" style="font-size: 12px; margin-top: 5px; margin-left: 7px; width: 760px;" class="custom-table-header">
                  <el-table-column label="区域1" width="380px">
                    <template #default="{ row }">
                      <img :src="row.imagePath9" alt="分类1图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                  <el-table-column label="区域2" width="380px" style="margin-left: 5px;">
                    <template #default="{ row }">
                      <img :src="row.imagePath10" alt="分类2图片" style="width: 380px; height: 190px;">
                    </template>
                  </el-table-column>
                </el-table>
                <div style="display: flex;">
                  <el-button :plain="simState4 !== 1" @click="simState4 = 1" type="success" style="margin-top: 10px; margin-left: 10px; width: 370px;">是</el-button>
                  <el-button :plain="simState4 !== 2" @click="simState4 = 2" type="warning" style="margin-top: 10px; margin-left: 10px; width: 370px;">否</el-button>
                </div>

                <!-- 选择"是"时显示的内容 -->
                <div v-if="simState4 === 1" style="margin-top: 15px; margin-left: 20px;">
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px;">如果【10分】代表两个框选区域完全相同，请给出上述区域的相似度评分：</div>
                    <el-input-number v-model="similarityScore4" :min="0" :max="10" style="width: 100px; margin-left: 10px; height: 30px; margin-bottom: 10px; margin-top: -5px;"></el-input-number>
                  </div>
                  <div style="display: flex;">
                    <div style="color: black; font-size: 13px; margin-bottom: 10px; margin-top: -2px;">上述相似片段在哪些部分仍有差异？</div>
                  <el-checkbox-group v-model="similarityReasons5" style="margin-left: 10px;display: flex;" >
                    <el-checkbox :label="1">均线发散程度变化</el-checkbox>
                    <el-checkbox :label="2">均线排列方式</el-checkbox>
                    <el-checkbox :label="3">框选区域的长度</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                  </div>

                  <div v-if="similarityReasons5.includes(4)" style="margin-top: -5px; display: flex;">
                    <span style="color: black; margin-right: 10px; font-size: 13px; margin-top: -3px;">请说明其他差异情况：</span>
                    <el-input v-model="similarityReasonCustom5" placeholder="请输入差异情况描述" style="width: 300px; margin-top: -10px; font-size: 12px;"></el-input>
                  </div>
                </div>

                <!-- 选择"否"时显示的内容 -->
                <div v-if="simState4 === 2" style="margin-top: 15px; display: flex;">
                  <div style="color: black; font-size: 13px; margin-left: 20px; margin-top: -1px;">上述片段的主要区别是？</div>
                  <el-checkbox-group v-model="differenceReasons5" style="margin-left: 10px; margin-bottom: 10px; display: flex;">
                    <el-checkbox :label="1">均线排列方式不同</el-checkbox>
                    <el-checkbox :label="2">股价趋势相反</el-checkbox>
                    <el-checkbox :label="3">时间周期差异大</el-checkbox>
                    <el-checkbox :label="4">其他</el-checkbox>
                  </el-checkbox-group>
                </div>
                <div v-if="differenceReasons5.includes(4)" style="margin-top: -15px;">
                  <span style="margin-left: -325px; font-size: 13px; color: #000000;">请说明其他区别：</span>
                  <el-input v-model="differenceReasonCustom5" placeholder="请输入区别描述" style="width: 300px;"></el-input>
                </div>
              </el-carousel-item>
            </el-carousel>

            <!-- 文字多选题部分保持不变 -->
            <div v-if="qaMode === 'text'" style="color: black; font-size: 14px;">
              <h4 style="margin-top: 0px;">【1】在比较两个股票片段是否相似时，您考虑到的因素是？<br>（默认为全选，每个特征默认权重值5，满分10，未选择项自动配置权重0）</h4>
              <el-table
                ref="multipleTableRef"
                :data="tableDataMultiple"
                row-key="id"
                style="width: 90%; margin-left: 40px;"
                @selection-change="handleSelectionChange"
                border
                :row-height="50"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column property="type" label="特征来源" width="120">
                  <template #default="{ row }">
                    <div style="padding: 12px 0;">{{ row.type }}</div>  <!-- 增加单元格内边距 -->
                  </template>
                </el-table-column>
                <el-table-column property="name" label="特征名称" width="130">
                  <template #default="{ row }">
                    <div style="padding: 12px 0;">{{ row.name }}</div>  <!-- 增加单元格内边距 -->
                  </template>
                </el-table-column>
                <el-table-column property="name" label="特征描述" width="270">
                  <template #default="{ row }">
                    <div style="padding: 12px 0;">{{ row.desc }}</div>  <!-- 增加单元格内边距 -->
                  </template>
                </el-table-column>
                <el-table-column label="权重设置 / 10分">
                  <template #default="{ row }">
                    <div style="padding: 8px 0;">  <!-- 增加单元格内边距 -->
                      <el-input-number
                        v-if="isRowSelected(row)"
                        v-model="row.weight"
                        :min="0"
                        :max="10"
                        style="width: 100px;"
                      />
                      <span v-else>-</span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <div style="display: flex; margin-left: 100px;">
                <div style="margin-top: 20px;">
                  <span style="margin-right: 10px;">补充选项:</span>
                  <el-input
                    v-model="supplementaryOption"
                    placeholder="请输入您的补充因素"
                    style="width: 300px;"
                  ></el-input>
                </div>
                <el-button type="primary" style="margin-top: 20px; font-size: 13px; height: 30px; margin-left: 10px;" @click="submitTextAnswer">提交补充因素（待审核）</el-button>
              </div>
              <hr style="margin-top: 20px; background-color: cadetblue;">
              <h4 style="margin-top: 20px;">【2】您可以通过如下设置，修改一条或几条均线的权重（默认权重相同，均为10）</h4>
              <el-table
                ref="multipleTableRef1"
                :data="tableDataMultiple2"
                row-key="id"
                style="width: 90%; margin-left: 40px;"
                @selection-change="handleSelectionChange2"
                border
                :row-height="50"
              >
                <el-table-column type="selection" width="60" />
                <el-table-column property="type" label="特征来源" width="150">
                  <template #default="{ row }">
                    <div style="padding: 12px 0;">{{ row.type }}</div>  <!-- 增加单元格内边距 -->
                  </template>
                </el-table-column>
                <el-table-column property="name" label="均线名称" width="150">
                  <template #default="{ row }">
                    <div style="padding: 12px 0;">{{ row.name }}</div>  <!-- 增加单元格内边距 -->
                  </template>
                </el-table-column>
                <el-table-column label="权重设置（默认10分）">
                  <template #default="{ row }">
                    <div style="padding: 8px 0;">  <!-- 增加单元格内边距 -->
                      <el-input-number
                        v-if="isRowSelected2(row)"
                        v-model="row.weight"
                        :min="0"
                        :max="100"
                        style="width: 100px;"
                      />
                      <span v-else>-</span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>

            </div>
          </div>
          <div v-if="currentCard === 2">
            <span style="font-size: 12px;"> 自定义分类：手动定义分类结果</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div style="margin-top: 10px;">
          <el-button @click="onUpdateVisible(false)">取消</el-button>
          <el-button type="primary" @click="onConfirm" class="apply-mode-btn">
            确认更新配置
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { ref } from "vue";
import { useStore } from "vuex";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  dialogTitle: {
    type: String,
    default: "相似特征确认",
  },
  dialogWidth: {
    type: [String, Number],
    default: "700",
  },
});

// 相似度状态和评分
const simState = ref(0); //
const simState1 = ref(0); //
const simState2 = ref(0); //
const simState3 = ref(0);
const simState4 = ref(0);

const similarityScore = ref(0);
const similarityScore1 = ref(0);
const similarityScore2 = ref(0);
const similarityScore3 = ref(0);
const similarityScore4 = ref(0);

// 相似度原因（改为数组存储多选结果）
const similarityReasons1 = ref([]);  // 原similarityReason1
const similarityReasons2 = ref([]);  // 原similarityReason2
const similarityReasons3 = ref([]);  // 原similarityReason3
const similarityReasons4 = ref([]);  // 原similarityReason4
const similarityReasons5 = ref([]);  // 原similarityReason5

// 相似度自定义原因
const similarityReasonCustom1 = ref('');
const similarityReasonCustom2 = ref('');
const similarityReasonCustom3 = ref('');
const similarityReasonCustom4 = ref('');
const similarityReasonCustom5 = ref('');

// 差异原因（改为数组存储多选结果）
const differenceReasons1 = ref([]);  // 原differenceReason1
const differenceReasons2 = ref([]);  // 原differenceReason2
const differenceReasons3 = ref([]);  // 原differenceReason3
const differenceReasons4 = ref([]);  // 原differenceReason4
const differenceReasons5 = ref([]);  // 原differenceReason5

// 差异自定义原因
const differenceReasonCustom1 = ref('');
const differenceReasonCustom2 = ref('');
const differenceReasonCustom3 = ref('');
const differenceReasonCustom4 = ref('');
const differenceReasonCustom5 = ref('');

// 多选表格相关
const multipleSelection = ref([])
const handleSelectionChange = (val) => {
  multipleSelection.value = val;
};
const multipleSelection2 = ref([])
const handleSelectionChange2 = (val) => {
  multipleSelection2.value = val;
};

// 表格数据包含所有因素（系统默认和用户自定义）
const tableDataMultiple = ref([
  {
    id: 1,
    tip: 'trend_direction_agreement',
    type: '单均线形态',
    name: '趋势方向',
    desc: '均线序列整体的升降趋势',
    weight: 5
  },
  {
    id: 2,
    tip:'trend_strength_similarity',
    type: '单均线形态',
    name: '趋势强度',
    desc: '均线上升或下降的陡峭程度',
    weight: 5
  },
  {
    id: 3,
    tip: 'dtw_similarity',
    type: '单均线形态',
    name: '弯曲形态',
    desc: '均线序列整体的形态轮廓',
    weight: 5
  },
  {
    id: 4,
    tip: 'volatility_similarity',
    type: '单均线数据',
    name: '波动幅度',
    desc: '均线的离散程度',
    weight: 5
  },
  {
    id: 5,
    tip: 'mean_level_similarity',
    type: '单均线数据',
    name: '均值水平',
    desc: '均线序列的整体数值水平',
    weight: 5
  },
  {
    id: 6,
    tip: 'pearson_similarity',
    type: '单均线数据',
    name: '线性同步',
    desc: '均线数值波动的线性同步关系',
    weight: 5
  },
  {
    id: 7,
    tip: 'spearman_similarity',
    type: '单均线数据',
    name: '涨跌排序',
    desc: '均线涨跌趋势的排序一致关系',
    weight: 5
  },

  {
    id: 8,
    tip: 'golden_position',
    type: '多均线形态',
    name: '金叉位置',
    desc: '中短期均线上穿长期均线的时间点分布',
    weight: 5
  },
  {
    id: 9,
    tip: 'death_position',
    type: '多均线形态',
    name: '死叉位置',
    desc: '中短期均线下穿长期均线的时间点分布',
    weight: 5
  },
  {
    id: 10,
    tip: 'golden_count',
    type: '多均线数据',
    name: '金叉频率',
    desc: '指定时间范围内金叉的发生次数',
    weight: 5
  },
  {
    id: 11,
    tip: 'death_count',
    type: '多均线形态',
    name: '死叉频率',
    desc: '指定时间范围内死叉的发生次数',
    weight: 5
  },
  {
    id: 12,
    tip: 'single_ma_features',
    type: '特征融合',
    name: '单均线特征',
    desc: '单条均线表现出的形态与数据特征',
    weight: 5
  },
  {
    id: 13,
    tip: 'crossover_features',
    type: '特征融合',
    name: '多均线组合特征',
    desc: '多条均线组合表现出的形态与数据特征',
    weight: 5
  },
])

// 均线的权重数据
const tableDataMultiple2 = ref([
  {
    id: 1,
    type: '系统默认',
    name: 'MA4',
    weight: 10
  },
  {
    id: 2,
    type: '系统默认',
    name: 'MA8',
    weight: 10
  },
  {
    id: 3,
    type: '系统默认',
    name: 'MA12',
    weight: 10
  },
  {
    id: 4,
    type: '系统默认',
    name: 'MA16',
    weight: 10
  },
  {
    id: 5,
    type: '系统默认',
    name: 'MA20',
    weight: 10
  },
  {
    id: 6,
    type: '用户自定义',
    name: 'MA47',
    weight: 10
  },
])

// 判断行是否被选中
const isRowSelected = (row) => {
  return multipleSelection.value.some(item => item.id === row.id);
};

const isRowSelected2 = (row) => {
  return multipleSelection2.value.some(item => item.id === row.id);
};

// 事件发射
const emit = defineEmits(["close", "update:model-value"]);

// 状态管理
const store = useStore();

// 表格数据
const tableData = [{}];
const tableData1 = [
  {
    imagePath1: '/stage1.png',
    imagePath2: '/stage2.png',
    imagePath3: '/stage3.png',
    imagePath4: '/stage4.png',
    imagePath5: '/stage5.png',
    imagePath6: '/stage6.png',
    imagePath7: '/stage7.png',
    imagePath8: '/stage8.png',
    imagePath9: '/stage9.png',
    imagePath10: '/stage10.png',
  }
];

// 卡片列表
const cardList = [
  { id: 1, label: '默认\n分类' },
  { id: 2, label: '自定义\n分类' }
];

// 默认选中第一个卡片
const currentCard = ref(1);

// 问答模式
const qaMode = ref('text');

// 切换问答模式
const toggleQaMode = () => {
  qaMode.value = qaMode.value === 'image' ? 'text' : 'image';
};

// 补充选项
const supplementaryOption = ref('');

// 提交文字答案
const submitTextAnswer = () => {
  const selectedFactors = multipleSelection.value.map(item => ({
    id: item.id,
    type: item.type,
    name: item.name,
    weight: item.weight
  }));

  console.log('用户选择的因素及权重:', selectedFactors);
  if (supplementaryOption.value) {
    console.log('用户补充的因素:', supplementaryOption.value);
  }
};

// 卡片点击
const handleCardClick = (id) => {
  currentCard.value = id;
};

// 关闭处理
const handleClose = (done) => {
  done();
  emit("close");
  emit("update:model-value", false);
};

// 更新可见性
const onUpdateVisible = (newValue) => {
  // 重置所有状态
  currentCard.value = 1;
  qaMode.value = 'text';
  supplementaryOption.value = '';
  multipleSelection.value = [];
  tableDataMultiple.value.forEach(item => {
    item.weight = 5;
  });

  emit("close");
  emit("update:model-value", false);
};

// 查找方式
const searchMode = ref('multi');
const dateRange = ref([new Date('2016-01-02'), new Date('2016-06-20')]);
const searchInfo = store.state.searchInfo;

const onConfirm = () => {
  store.commit("updateNewSearchInfo", {
    ifSet: true,
  });
  if (qaMode.value === 'text') {
    console.log('=== 文字问答答案 ===');

    // 【全部因素控制台输出，未选中项自动配置权重为0】-------------------------------------------------------
    const allFactorsWithWeight = tableDataMultiple.value.map(item => {
      // 检查当前项是否被选中
      const isSelected = multipleSelection.value.some(
        selected => selected.id === item.id
      );

      // 如果选中，使用修改后的权重；未选中，权重设为0
      if (isSelected) {
        const selectedItem = multipleSelection.value.find(
          selected => selected.id === item.id
        );
        return {
          ...item,
          weight: selectedItem.weight // 使用选中后修改的权重
        };
      } else {
        return {
          ...item,
          weight: 0 // 未选中项权重设为0
        };
      }
    });

    console.log('全部因素及权重:', allFactorsWithWeight);
    // 初始化权重结构
    const default_group_weights = {
        'single_ma_features': 0,
        'crossover_features': 0
    };
    const default_single_ma_weights = {};
    const default_crossover_weights = {};

    // 定义分组对应的tip集合
    const singleMaTips = [
        'trend_direction_agreement',
        'trend_strength_similarity',
        'dtw_similarity',
        'volatility_similarity',
        'mean_level_similarity',
        'pearson_similarity',
        'spearman_similarity'
    ];
    const crossoverTips = [
        'golden_position',
        'death_position',
        'golden_count',
        'death_count'
    ];

    // 第一步：收集各组权重并计算总和
    const groupWeights = {
        single_ma: 0,
        crossover: 0
    };
    const singleMaTotal = { sum: 0 };
    const crossoverTotal = { sum: 0 };

    allFactorsWithWeight.forEach(item => {
        const weightValue = item.weight;

        if (item.tip === 'single_ma_features') {
            groupWeights.single_ma = weightValue;
        } else if (item.tip === 'crossover_features') {
            groupWeights.crossover = weightValue;
        } else if (singleMaTips.includes(item.tip)) {
            singleMaTotal.sum += weightValue;
            // 临时存储原始权重
            default_single_ma_weights[item.tip] = weightValue;
        } else if (crossoverTips.includes(item.tip)) {
            crossoverTotal.sum += weightValue;
            // 临时存储原始权重
            default_crossover_weights[item.tip] = weightValue;
        }
    });

    // 第二步：归一化处理 - 组间权重
    const groupTotal = groupWeights.single_ma + groupWeights.crossover;
    if (groupTotal > 0) {
        default_group_weights['single_ma_features'] = groupWeights.single_ma / groupTotal;
        default_group_weights['crossover_features'] = groupWeights.crossover / groupTotal;
    }

    // 第三步：归一化处理 - 单均线内部特征权重
    if (singleMaTotal.sum > 0) {
        Object.keys(default_single_ma_weights).forEach(tip => {
            default_single_ma_weights[tip] /= singleMaTotal.sum;
        });
    }

    // 第四步：归一化处理 - 交叉特征内部权重
    if (crossoverTotal.sum > 0) {
        Object.keys(default_crossover_weights).forEach(tip => {
            default_crossover_weights[tip] /= crossoverTotal.sum;
        });
    }

    // 输出结果
    console.log('归一化后的组间权重:', default_group_weights);
    console.log('归一化后的单均线特征权重:', default_single_ma_weights);
    console.log('归一化后的交叉特征权重:', default_crossover_weights);
    store.commit("updateNewSearchInfo", {
      group_weights: default_group_weights,
      single_ma_weights: default_single_ma_weights,
      crossover_weights: default_crossover_weights,
    });
    // ---------------------------------------------------------

    const selectedFactors = multipleSelection.value.map(item => ({
      id: item.id,
      type: item.type,
      name: item.name,
      weight: item.weight
    }));

    console.log('选中的因素及权重:', selectedFactors);
    store.commit("updateNewSearchInfoProperty", {
      key: 'selectedFactors',
      value: selectedFactors,
    });

    if (supplementaryOption.value) {
      console.log('补充因素:', supplementaryOption.value);
      store.commit("updateNewSearchInfoProperty", {
        key: 'supplementaryOption',
        value: supplementaryOption.value,
      });
    }
  } else {
    // 收集图片问答答案，适配多选结果
    const photoOption = [
      {
        simState: simState.value,
        similarityScore: similarityScore.value,
        similarityReasons: similarityReasons1.value,  // 改为复数形式
        similarityReasonCustom: similarityReasonCustom1.value,
        differenceReasons: differenceReasons1.value,  // 改为复数形式
        differenceReasonCustom: differenceReasonCustom1.value
      },
      {
        simState: simState1.value,
        similarityScore: similarityScore1.value,
        similarityReasons: similarityReasons2.value,
        similarityReasonCustom: similarityReasonCustom2.value,
        differenceReasons: differenceReasons2.value,
        differenceReasonCustom: differenceReasonCustom2.value
      },
      {
        simState: simState2.value,
        similarityScore: similarityScore2.value,
        similarityReasons: similarityReasons3.value,
        similarityReasonCustom: similarityReasonCustom3.value,
        differenceReasons: differenceReasons3.value,
        differenceReasonCustom: differenceReasonCustom3.value
      },
      {
        simState: simState3.value,
        similarityScore: similarityScore3.value,
        similarityReasons: similarityReasons4.value,
        similarityReasonCustom: similarityReasonCustom4.value,
        differenceReasons: differenceReasons4.value,
        differenceReasonCustom: differenceReasonCustom4.value
      },
      {
        simState: simState4.value,
        similarityScore: similarityScore4.value,
        similarityReasons: similarityReasons5.value,
        similarityReasonCustom: similarityReasonCustom5.value,
        differenceReasons: differenceReasons5.value,
        differenceReasonCustom: differenceReasonCustom5.value
      }
    ];

    console.log('图片问答答案:', photoOption);
    store.commit("updateNewSearchInfoProperty", {
      key:'photoOption',
      value: photoOption,
    });
  }
  onUpdateVisible(false);
};
</script>

<style scoped>
/* 样式保持不变 */
.card-group {
  gap: 10px;
}

.is-active {
  background-color: #81bfff;
  color: var(--el-color-white);
}

::v-deep .custom-table-header .el-table__header th {
  background-color: #f5f7fa !important;
  text-align: center !important;
  font-size: 12px !important;
}

.el-carousel__item h3 {
  color: #475669;
  opacity: 0.75;
  margin: 0;
  text-align: center;
}

.el-carousel__item:nth-child(2n) {
  height: 400px;
  background-color: #e7e7e7;
}

.el-carousel__item:nth-child(2n + 1) {
  height: 400px;
  background-color: #e7e7e7;
}

.el-checkbox {
  display: block;
  margin-bottom: 8px;  /* 保持和原单选框相同的间距 */
}
</style>