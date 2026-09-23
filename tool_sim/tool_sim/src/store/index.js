import { createStore } from 'vuex';
import axios from "axios";

const store = createStore({
    state: {
        resultJson : null,

        sim_stock_list:[], // 模式相似股票列表
        sim_stock_list_weekly: [], // 周线相似股票列表
        sim_stock_list_monthly: [], // 月线相似股票列表
        // 训练集池：跨组件共享正负样本
        trainingPool: {
            positiveChecked: [],   // 用户勾选的真实片段
            positiveRated: [],     // 打分≥4星的历史结果
            positiveSynth: [],     // 打分≥4星的AI仿真样本
            negativeRated: [],     // 打分≤2星的历史结果
            negativeSynth: [],     // 打分≤2星的AI仿真样本
        },
        // 控制训练集清洗舱弹窗可见性（跨组件触发）
        showTrainCleanDialog: false,
        // 新的用户查找信息
        newSearchInfo:{
            ifSet: false, // 是否设置了自定义相似性参数
            baseFolder: 'savepng', // 基准文件夹
            selectedFactor: null, // 选择的系统默认因素
            selectedFactor2: null, // 选择的自定义因素
            supplementaryOption: null, // 补充选项
            photoOption: [], // 图片选项
            savedBrushTimeRanges: [], // 保存的刷选时间区间
            recentNDaysValue: '--', // 最近N天的值
            lines:[],
            group_weights: {},
            single_ma_weights: {},
            crossover_weights: {},
            baseSegmentData: [], // 基准均线片段（历史检索回传，供结果页左侧基准图渲染）
        },

        baseInfo:{
            isMode: false, // 是否为模式
            isStock: false, // 是否为股票
            currentFunction: '股票信息预览', // 当前功能
            isDisabled: false, // 是否禁用查找历史区间按钮
            isChooseStock: false, 
            isHistorySearch: false, 
        },
        // 【用户选择股票预览】界面展示的股票信息
        stockShowInfo: {
            "code": "000021",
            "name": "深科技",
            "value": "+1.57",
            "ratio": "+14.0%",
            "isSelected": false
        },

        // 【用户选择股票作为查找基准项】当前选中的股票信息
        stockInfo:{
            code: '--',  // 基准代码
            name: '--',  // 基准名称
            lines: [],   // 基准线条数据（默认为全选）
            lines1:[],
            lines2:[],
            startDate: '', // 基准开始日期（默认 2024-11-15）
            endDate: '',   // 基准结束日期（默认 2025-03-25）
        },

        // 【用户选择股票或模式作为查找基准项】当前配置模式的信息
        modeInfo:{
            index: '--', // 股票代码或模式的简写英文
            name: '---',  // 股票或模式的名称
            lines: ["个股", "MA4", "MA8", "MA12", "MA16", "MA20", "MA47"],   // 股票或模式的线条数据(根据模式个性化数据构建默认项)
            lines1:["深证指数","MA4", "MA8", "MA12", "MA16", "MA20", "MA47"],
            lines2:["行业指数","MA4", "MA8", "MA12", "MA16", "MA20", "MA47"],
            isMode: false, // 是否为模式
            isSelected: false,     // 是否为自定义模式
            modeClass:'--',        // 模式的类型
            modeDescription: '--', // 模式的描述
            minDays: 5,            // 模式的最小天数
            startDate: '2024-09-20',
            endDate: '2024-11-20',
        },

        // 【用户设置查找的范围】当前查找范围的信息
        searchInfo:{
            searchStartDate: '--',
            searchEndDate: '--',
            stockList:[],
        },

        // 查找结果的统计信息
        resultInfo:{
            futureDays: 5,
            futureIncome: 0.0,
            maxRange: 0.0,
            maxRate: 0.0,
            stockIncrease: 0.0,
            stockDecrease: 0.0,
            riseFallRatio: [50, 50],
        },

        resultStockInfo:{
            code: '001255',  // 股票代码
            name: '--',  // 股票名称
            startDate: '2024-09-19', // 开始日期
            endDate: '2024-11-13',   // 结束日期
        },

        // 下方表格展示的查找结果
        resultList:[
        ],

        // 股票基准查询的结果
        resultList2:[
        ],

        // 全部股票列表【自选标签为true的筛选进我的自选列表中】
        stockList: [
            {
                "code": "000021",
                "name": "深科技",
                "value": "+1.57",
                "ratio": "+14.0%",
                "isSelected": false
            },
            {
                "code": "000547",
                "name": "航天发展",
                "value": "+1.88",
                "ratio": "+12.3%",
                "isSelected": false
            },
            {
                "code": "000561",
                "name": "烽火电子",
                "value": "+1.83",
                "ratio": "+14.9%",
                "isSelected": false
            },
            {
                "code": "000830",
                "name": "鲁西化工",
                "value": "+2.02",
                "ratio": "+15.4%",
                "isSelected": false
            },
            {
                "code": "001207",
                "name": "联科科技",
                "value": "+2.06",
                "ratio": "+13.4%",
                "isSelected": false
            },
            {
                "code": "001255",
                "name": "博菲电气",
                "value": "+1.6",
                "ratio": "+13.3%",
                "isSelected": false
            },
            {
                "code": "001308",
                "name": "康冠科技",
                "value": "+1.88",
                "ratio": "+12.8%",
                "isSelected": false
            },
            {
                "code": "001309",
                "name": "德明利",
                "value": "+2.17",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "001333",
                "name": "光华股份",
                "value": "+2.19",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "001339",
                "name": "智微智能",
                "value": "+1.56",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "002025",
                "name": "航天电器",
                "value": "+1.71",
                "ratio": "15.2%",
                "isSelected": false
            },
            {
                "code": "002052",
                "name": "*ST同洲",
                "value": "+1.67",
                "ratio": "13.7%",
                "isSelected": false
            },
            {
                "code": "002057",
                "name": "中钢天源",
                "value": "+1.81",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "002092",
                "name": "ST中泰",
                "value": "+2.09",
                "ratio": "14.4%",
                "isSelected": false
            },
            {
                "code": "002106",
                "name": "莱宝高科",
                "value": "+1.87",
                "ratio": "15.5%",
                "isSelected": false
            },
            {
                "code": "002119",
                "name": "康强电子",
                "value": "+2.19",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "002134",
                "name": "天津普林",
                "value": "+1.98",
                "ratio": "14.4%",
                "isSelected": false
            },
            {
                "code": "002161",
                "name": "远望谷",
                "value": "+1.69",
                "ratio": "13.9%",
                "isSelected": false
            },
            {
                "code": "002165",
                "name": "红宝丽",
                "value": "+1.63",
                "ratio": "12.1%",
                "isSelected": false
            },
            {
                "code": "002211",
                "name": "宏达新材",
                "value": "+1.79",
                "ratio": "13.3%",
                "isSelected": false
            },
            {
                "code": "002213",
                "name": "大为股份",
                "value": "+1.99",
                "ratio": "14.9%",
                "isSelected": false
            },
            {
                "code": "002231",
                "name": "奥维通信",
                "value": "+2.06",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "002236",
                "name": "大华股份",
                "value": "+2.02",
                "ratio": "14.6%",
                "isSelected": false
            },
            {
                "code": "002246",
                "name": "北化股份",
                "value": "+2.03",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "002258",
                "name": "利尔化学",
                "value": "+2.02",
                "ratio": "13.5%",
                "isSelected": false
            },
            {
                "code": "002289",
                "name": "ST宇顺",
                "value": "+1.84",
                "ratio": "11.1%",
                "isSelected": false
            },
            {
                "code": "002361",
                "name": "神剑股份",
                "value": "+1.59",
                "ratio": "13.1%",
                "isSelected": false
            },
            {
                "code": "002362",
                "name": "汉王科技",
                "value": "+1.72",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "002376",
                "name": "新北洋",
                "value": "+1.76",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "002414",
                "name": "高德红外",
                "value": "+2.05",
                "ratio": "12.0%",
                "isSelected": false
            },
            {
                "code": "002415",
                "name": "海康威视",
                "value": "+2.12",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "002436",
                "name": "兴森科技",
                "value": "+2.14",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "002446",
                "name": "盛路通信",
                "value": "+1.55",
                "ratio": "15.0%",
                "isSelected": false
            },
            {
                "code": "002455",
                "name": "百川股份",
                "value": "+1.64",
                "ratio": "11.7%",
                "isSelected": false
            },
            {
                "code": "002465",
                "name": "海格通信",
                "value": "+1.65",
                "ratio": "15.7%",
                "isSelected": false
            },
            {
                "code": "002469",
                "name": "三维化学",
                "value": "+1.59",
                "ratio": "14.8%",
                "isSelected": false
            },
            {
                "code": "002484",
                "name": "江海股份",
                "value": "+2.18",
                "ratio": "13.9%",
                "isSelected": true
            },
            {
                "code": "002493",
                "name": "荣盛石化",
                "value": "+2.12",
                "ratio": "14.0%",
                "isSelected": false
            },
            {
                "code": "002528",
                "name": "ST英飞拓",
                "value": "+2.08",
                "ratio": "14.2%",
                "isSelected": true
            },
            {
                "code": "002587",
                "name": "奥拓电子",
                "value": "+2.18",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "002591",
                "name": "恒大高新",
                "value": "+1.61",
                "ratio": "11.5%",
                "isSelected": false
            },
            {
                "code": "002632",
                "name": "道明光学",
                "value": "+2.01",
                "ratio": "15.8%",
                "isSelected": false
            },
            {
                "code": "002643",
                "name": "万润股份",
                "value": "+1.75",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "002648",
                "name": "卫星化学",
                "value": "+1.95",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "002655",
                "name": "共达电声",
                "value": "+1.61",
                "ratio": "11.5%",
                "isSelected": true
            },
            {
                "code": "002741",
                "name": "光华科技",
                "value": "+1.7",
                "ratio": "11.5%",
                "isSelected": false
            },
            {
                "code": "002748",
                "name": "ST世龙",
                "value": "+2.09",
                "ratio": "11.2%",
                "isSelected": false
            },
            {
                "code": "002759",
                "name": "天际股份",
                "value": "+1.92",
                "ratio": "12.9%",
                "isSelected": true
            },
            {
                "code": "002792",
                "name": "通宇通讯",
                "value": "+1.71",
                "ratio": "13.9%",
                "isSelected": true
            },
            {
                "code": "002813",
                "name": "路畅科技",
                "value": "+2.16",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "002848",
                "name": "高斯贝尔",
                "value": "+2.01",
                "ratio": "14.0%",
                "isSelected": false
            },
            {
                "code": "002855",
                "name": "捷荣技术",
                "value": "+1.56",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "002859",
                "name": "洁美科技",
                "value": "+2.02",
                "ratio": "12.7%",
                "isSelected": false
            },
            {
                "code": "002861",
                "name": "瀛通通讯",
                "value": "+2.1",
                "ratio": "11.3%",
                "isSelected": false
            },
            {
                "code": "002866",
                "name": "传艺科技",
                "value": "+2.08",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "002913",
                "name": "奥士康",
                "value": "+2.19",
                "ratio": "15.8%",
                "isSelected": false
            },
            {
                "code": "002915",
                "name": "中欣氟材",
                "value": "+1.6",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "002916",
                "name": "深南电路",
                "value": "+1.65",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "002919",
                "name": "名臣健康",
                "value": "+1.72",
                "ratio": "14.5%",
                "isSelected": false
            },
            {
                "code": "002952",
                "name": "亚世光电",
                "value": "+1.95",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "002960",
                "name": "青鸟消防",
                "value": "+1.74",
                "ratio": "12.9%",
                "isSelected": false
            },
            {
                "code": "002992",
                "name": "宝明科技",
                "value": "+1.58",
                "ratio": "15.3%",
                "isSelected": false
            },
            {
                "code": "003019",
                "name": "宸展光电",
                "value": "+1.53",
                "ratio": "12.0%",
                "isSelected": false
            },
            {
                "code": "003028",
                "name": "振邦智能",
                "value": "+1.69",
                "ratio": "15.0%",
                "isSelected": false
            },
            {
                "code": "003042",
                "name": "中农联合",
                "value": "+1.72",
                "ratio": "15.5%",
                "isSelected": false
            },
            {
                "code": "300019",
                "name": "硅宝科技",
                "value": "+1.6",
                "ratio": "12.0%",
                "isSelected": false
            },
            {
                "code": "300037",
                "name": "新宙邦",
                "value": "+1.59",
                "ratio": "12.7%",
                "isSelected": false
            },
            {
                "code": "300067",
                "name": "安诺其",
                "value": "+1.93",
                "ratio": "13.2%",
                "isSelected": false
            },
            {
                "code": "300082",
                "name": "奥克股份",
                "value": "+1.6",
                "ratio": "15.0%",
                "isSelected": false
            },
            {
                "code": "300088",
                "name": "长信科技",
                "value": "+1.81",
                "ratio": "15.4%",
                "isSelected": true
            },
            {
                "code": "300109",
                "name": "新开源",
                "value": "+2.06",
                "ratio": "12.7%",
                "isSelected": true
            },
            {
                "code": "300128",
                "name": "锦富技术",
                "value": "+1.71",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "300136",
                "name": "信维通信",
                "value": "+1.8",
                "ratio": "15.8%",
                "isSelected": false
            },
            {
                "code": "300219",
                "name": "鸿利智汇",
                "value": "+2.18",
                "ratio": "13.2%",
                "isSelected": false
            },
            {
                "code": "300225",
                "name": "金力泰",
                "value": "+1.86",
                "ratio": "11.5%",
                "isSelected": false
            },
            {
                "code": "300232",
                "name": "洲明科技",
                "value": "+1.85",
                "ratio": "14.7%",
                "isSelected": false
            },
            {
                "code": "300243",
                "name": "瑞丰高材",
                "value": "+2.15",
                "ratio": "14.4%",
                "isSelected": false
            },
            {
                "code": "300279",
                "name": "和晶科技",
                "value": "+1.73",
                "ratio": "12.4%",
                "isSelected": false
            },
            {
                "code": "300285",
                "name": "国瓷材料",
                "value": "+1.59",
                "ratio": "15.3%",
                "isSelected": false
            },
            {
                "code": "300296",
                "name": "利亚德",
                "value": "+1.82",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "300301",
                "name": "*ST长方",
                "value": "+2.14",
                "ratio": "15.2%",
                "isSelected": false
            },
            {
                "code": "300327",
                "name": "中颖电子",
                "value": "+1.76",
                "ratio": "13.9%",
                "isSelected": false
            },
            {
                "code": "300331",
                "name": "苏大维格",
                "value": "+1.9",
                "ratio": "13.8%",
                "isSelected": false
            },
            {
                "code": "300373",
                "name": "扬杰科技",
                "value": "+2.15",
                "ratio": "12.1%",
                "isSelected": false
            },
            {
                "code": "300429",
                "name": "强力新材",
                "value": "+1.97",
                "ratio": "14.1%",
                "isSelected": false
            },
            {
                "code": "300437",
                "name": "清水源",
                "value": "+1.7",
                "ratio": "15.2%",
                "isSelected": false
            },
            {
                "code": "300446",
                "name": "航天智造",
                "value": "+1.91",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "300516",
                "name": "久之洋",
                "value": "+1.5",
                "ratio": "15.8%",
                "isSelected": false
            },
            {
                "code": "300531",
                "name": "优博讯",
                "value": "+2.15",
                "ratio": "12.1%",
                "isSelected": false
            },
            {
                "code": "300576",
                "name": "容大感光",
                "value": "+1.71",
                "ratio": "13.9%",
                "isSelected": false
            },
            {
                "code": "300581",
                "name": "晨曦航空",
                "value": "+1.7",
                "ratio": "11.5%",
                "isSelected": false
            },
            {
                "code": "300602",
                "name": "飞荣达",
                "value": "+2.0",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "300610",
                "name": "晨化股份",
                "value": "+1.98",
                "ratio": "15.8%",
                "isSelected": true
            },
            {
                "code": "300641",
                "name": "正丹股份",
                "value": "+1.85",
                "ratio": "15.1%",
                "isSelected": true
            },
            {
                "code": "300661",
                "name": "圣邦股份",
                "value": "+1.5",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "300666",
                "name": "江丰电子",
                "value": "+1.87",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "300698",
                "name": "万马科技",
                "value": "+1.53",
                "ratio": "11.5%",
                "isSelected": false
            },
            {
                "code": "300727",
                "name": "润禾材料",
                "value": "+1.63",
                "ratio": "15.8%",
                "isSelected": false
            },
            {
                "code": "300735",
                "name": "光弘科技",
                "value": "+1.78",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "300796",
                "name": "贝斯美",
                "value": "+1.54",
                "ratio": "12.0%",
                "isSelected": false
            },
            {
                "code": "300814",
                "name": "中富电路",
                "value": "+1.76",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "300822",
                "name": "贝仕达克",
                "value": "+1.6",
                "ratio": "14.0%",
                "isSelected": false
            },
            {
                "code": "300848",
                "name": "美瑞新材",
                "value": "+2.03",
                "ratio": "15.9%",
                "isSelected": false
            },
            {
                "code": "300866",
                "name": "安克创新",
                "value": "+1.97",
                "ratio": "11.9%",
                "isSelected": false
            },
            {
                "code": "300916",
                "name": "朗特智能",
                "value": "+1.55",
                "ratio": "13.8%",
                "isSelected": false
            },
            {
                "code": "300919",
                "name": "中伟股份",
                "value": "+2.04",
                "ratio": "16.0%",
                "isSelected": false
            },
            {
                "code": "300927",
                "name": "江天化学",
                "value": "+1.99",
                "ratio": "12.5%",
                "isSelected": false
            },
            {
                "code": "300939",
                "name": "秋田微",
                "value": "+1.82",
                "ratio": "12.2%",
                "isSelected": false
            },
            {
                "code": "300976",
                "name": "达瑞电子",
                "value": "+2.17",
                "ratio": "11.2%",
                "isSelected": false
            },
            {
                "code": "301035",
                "name": "润丰股份",
                "value": "+1.65",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "301042",
                "name": "安联锐视",
                "value": "+2.17",
                "ratio": "12.2%",
                "isSelected": false
            },
            {
                "code": "301050",
                "name": "雷电微力",
                "value": "+1.77",
                "ratio": "12.8%",
                "isSelected": false
            },
            {
                "code": "301069",
                "name": "凯盛新材",
                "value": "+2.1",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "301106",
                "name": "骏成科技",
                "value": "+1.77",
                "ratio": "14.0%",
                "isSelected": false
            },
            {
                "code": "301123",
                "name": "奕东电子",
                "value": "+2.07",
                "ratio": "+13.9%",
                "isSelected": true
            },
            {
                "code": "301157",
                "name": "华塑科技",
                "value": "+1.97",
                "ratio": "+14.8%",
                "isSelected": true
            },
            {
                "code": "301180",
                "name": "万祥科技",
                "value": "+2.07",
                "ratio": "11.2%",
                "isSelected": false
            },
            {
                "code": "301189",
                "name": "奥尼电子",
                "value": "+2.15",
                "ratio": "14.9%",
                "isSelected": false
            },
            {
                "code": "301191",
                "name": "菲菱科思",
                "value": "+1.92",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "301217",
                "name": "铜冠铜箔",
                "value": "+1.63",
                "ratio": "14.3%",
                "isSelected": false
            },
            {
                "code": "301251",
                "name": "威尔高",
                "value": "+2.16",
                "ratio": "11.7%",
                "isSelected": false
            },
            {
                "code": "301292",
                "name": "海科新源",
                "value": "+2.17",
                "ratio": "11.8%",
                "isSelected": false
            },
            {
                "code": "301319",
                "name": "唯特偶",
                "value": "+1.88",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "301328",
                "name": "维峰电子",
                "value": "+1.59",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "301348",
                "name": "蓝箭电子",
                "value": "+1.75",
                "ratio": "15.6%",
                "isSelected": false
            },
            {
                "code": "301349",
                "name": "信德新材",
                "value": "+1.69",
                "ratio": "13.9%",
                "isSelected": false
            },
            {
                "code": "301373",
                "name": "凌玮科技",
                "value": "+1.84",
                "ratio": "13.7%",
                "isSelected": false
            },
            {
                "code": "301413",
                "name": "安培龙",
                "value": "+1.96",
                "ratio": "11.8%",
                "isSelected": false
            },
            {
                "code": "301487",
                "name": "盟固利",
                "value": "+1.81",
                "ratio": "13.8%",
                "isSelected": false
            },
            {
                "code": "301489",
                "name": "思泉新材",
                "value": "+1.59",
                "ratio": "13.5%",
                "isSelected": false
            },
            {
                "code": "301536",
                "name": "星宸科技",
                "value": "+1.66",
                "ratio": "12.2%",
                "isSelected": false
            },
            {
                "code": "301571",
                "name": "国科天成",
                "value": "+1.81",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "301589",
                "name": "诺瓦星云",
                "value": "+1.63",
                "ratio": "14.0%",
                "isSelected": false
            },
            {
                "code": "301600",
                "name": "慧翰股份",
                "value": "+1.87",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "301606",
                "name": "绿联科技",
                "value": "+2.08",
                "ratio": "12.5%",
                "isSelected": false
            },
            {
                "code": "600110",
                "name": "诺德股份",
                "value": "+2.14",
                "ratio": "15.5%",
                "isSelected": false
            },
            {
                "code": "600160",
                "name": "巨化股份",
                "value": "+1.55",
                "ratio": "12.6%",
                "isSelected": false
            },
            {
                "code": "600227",
                "name": "赤天化",
                "value": "+2.19",
                "ratio": "11.8%",
                "isSelected": false
            },
            {
                "code": "600230",
                "name": "沧州大化",
                "value": "+1.66",
                "ratio": "15.3%",
                "isSelected": false
            },
            {
                "code": "600249",
                "name": "两面针",
                "value": "+1.55",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "600273",
                "name": "嘉化能源",
                "value": "+1.93",
                "ratio": "12.1%",
                "isSelected": false
            },
            {
                "code": "600319",
                "name": "亚星化学",
                "value": "+2.16",
                "ratio": "15.4%",
                "isSelected": false
            },
            {
                "code": "600328",
                "name": "中盐化工",
                "value": "+2.16",
                "ratio": "11.3%",
                "isSelected": false
            },
            {
                "code": "600330",
                "name": "天通股份",
                "value": "+2.05",
                "ratio": "13.3%",
                "isSelected": false
            },
            {
                "code": "600353",
                "name": "旭光电子",
                "value": "+1.66",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "600370",
                "name": "三房巷",
                "value": "+1.86",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "600378",
                "name": "昊华科技",
                "value": "+1.56",
                "ratio": "14.3%",
                "isSelected": false
            },
            {
                "code": "600389",
                "name": "江山股份",
                "value": "+1.75",
                "ratio": "15.5%",
                "isSelected": true
            },
            {
                "code": "600409",
                "name": "三友化工",
                "value": "+1.76",
                "ratio": "13.1%",
                "isSelected": true
            },
            {
                "code": "600435",
                "name": "北方导航",
                "value": "+1.52",
                "ratio": "15.9%",
                "isSelected": false
            },
            {
                "code": "600486",
                "name": "扬农化工",
                "value": "+1.96",
                "ratio": "12.0%",
                "isSelected": false
            },
            {
                "code": "600552",
                "name": "凯盛科技",
                "value": "+1.8",
                "ratio": "13.7%",
                "isSelected": true
            },
            {
                "code": "600618",
                "name": "氯碱化工",
                "value": "+1.88",
                "ratio": "12.4%",
                "isSelected": true
            },
            {
                "code": "600746",
                "name": "江苏索普",
                "value": "+1.8",
                "ratio": "12.9%",
                "isSelected": false
            },
            {
                "code": "600844",
                "name": "丹化科技",
                "value": "+1.65",
                "ratio": "15.9%",
                "isSelected": false
            },
            {
                "code": "600888",
                "name": "新疆众和",
                "value": "+1.82",
                "ratio": "12.7%",
                "isSelected": false
            },
            {
                "code": "600990",
                "name": "四创电子",
                "value": "+1.52",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "601065",
                "name": "江盐集团",
                "value": "+1.79",
                "ratio": "15.7%",
                "isSelected": false
            },
            {
                "code": "601678",
                "name": "滨化股份",
                "value": "+1.6",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "601869",
                "name": "长飞光纤",
                "value": "+1.86",
                "ratio": "13.0%",
                "isSelected": false
            },
            {
                "code": "603002",
                "name": "宏昌电子",
                "value": "+1.73",
                "ratio": "14.9%",
                "isSelected": false
            },
            {
                "code": "603004",
                "name": "鼎龙科技",
                "value": "+1.53",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "603023",
                "name": "*ST威帝",
                "value": "+1.6",
                "ratio": "11.0%",
                "isSelected": false
            },
            {
                "code": "603041",
                "name": "美思德",
                "value": "+1.97",
                "ratio": "13.0%",
                "isSelected": false
            },
            {
                "code": "603052",
                "name": "可川科技",
                "value": "+1.58",
                "ratio": "15.0%",
                "isSelected": true
            },
            {
                "code": "603078",
                "name": "江化微",
                "value": "+1.72",
                "ratio": "12.0%",
                "isSelected": true
            },
            {
                "code": "603110",
                "name": "东方材料",
                "value": "+2.07",
                "ratio": "14.5%",
                "isSelected": false
            },
            {
                "code": "603125",
                "name": "常青科技",
                "value": "+1.92",
                "ratio": "11.5%",
                "isSelected": false
            },
            {
                "code": "603172",
                "name": "万丰股份",
                "value": "+1.51",
                "ratio": "13.4%",
                "isSelected": false
            },
            {
                "code": "603192",
                "name": "汇得科技",
                "value": "+1.94",
                "ratio": "13.3%",
                "isSelected": false
            },
            {
                "code": "603217",
                "name": "元利科技",
                "value": "+1.79",
                "ratio": "12.4%",
                "isSelected": false
            },
            {
                "code": "603285",
                "name": "键邦股份",
                "value": "+1.81",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "603310",
                "name": "巍华新材",
                "value": "+2.04",
                "ratio": "15.0%",
                "isSelected": false
            },
            {
                "code": "603375",
                "name": "盛景微",
                "value": "+1.81",
                "ratio": "15.9%",
                "isSelected": false
            },
            {
                "code": "603379",
                "name": "三美股份",
                "value": "+2.04",
                "ratio": "11.2%",
                "isSelected": false
            },
            {
                "code": "603386",
                "name": "骏亚科技",
                "value": "+1.85",
                "ratio": "13.3%",
                "isSelected": false
            },
            {
                "code": "603501",
                "name": "韦尔股份",
                "value": "+1.6",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "603630",
                "name": "拉芳家化",
                "value": "+1.71",
                "ratio": "14.0%",
                "isSelected": false
            },
            {
                "code": "603660",
                "name": "苏州科达",
                "value": "+1.96",
                "ratio": "11.2%",
                "isSelected": false
            },
            {
                "code": "603722",
                "name": "阿科力",
                "value": "+1.92",
                "ratio": "15.2%",
                "isSelected": false
            },
            {
                "code": "603803",
                "name": "瑞斯康达",
                "value": "+2.12",
                "ratio": "13.0%",
                "isSelected": false
            },
            {
                "code": "603938",
                "name": "三孚股份",
                "value": "+2.17",
                "ratio": "15.7%",
                "isSelected": false
            },
            {
                "code": "603948",
                "name": "建业股份",
                "value": "+2.1",
                "ratio": "12.3%",
                "isSelected": false
            },
            {
                "code": "603983",
                "name": "丸美生物",
                "value": "+2.04",
                "ratio": "13.2%",
                "isSelected": false
            },
            {
                "code": "603989",
                "name": "艾华集团",
                "value": "+2.06",
                "ratio": "14.6%",
                "isSelected": false
            },
            {
                "code": "605008",
                "name": "长鸿高科",
                "value": "+1.96",
                "ratio": "12.9%",
                "isSelected": false
            },
            {
                "code": "605033",
                "name": "美邦股份",
                "value": "+2.19",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "605258",
                "name": "协和电子",
                "value": "+1.92",
                "ratio": "13.1%",
                "isSelected": false
            },
            {
                "code": "605366",
                "name": "宏柏新材",
                "value": "+1.96",
                "ratio": "13.2%",
                "isSelected": false
            },
            {
                "code": "605399",
                "name": "晨光新材",
                "value": "+1.57",
                "ratio": "11.1%",
                "isSelected": false
            },
            {
                "code": "605589",
                "name": "圣泉集团",
                "value": "+1.69",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "688025",
                "name": "杰普特",
                "value": "+1.78",
                "ratio": "14.3%",
                "isSelected": false
            },
            {
                "code": "688049",
                "name": "炬芯科技",
                "value": "+1.91",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "688055",
                "name": "龙腾光电",
                "value": "+1.95",
                "ratio": "11.8%",
                "isSelected": false
            },
            {
                "code": "688110",
                "name": "东芯股份",
                "value": "+2.05",
                "ratio": "15.4%",
                "isSelected": false
            },
            {
                "code": "688148",
                "name": "芳源股份",
                "value": "+1.54",
                "ratio": "11.1%",
                "isSelected": false
            },
            {
                "code": "688153",
                "name": "唯捷创芯",
                "value": "+1.56",
                "ratio": "11.4%",
                "isSelected": false
            },
            {
                "code": "688199",
                "name": "久日新材",
                "value": "+1.86",
                "ratio": "16.0%",
                "isSelected": false
            },
            {
                "code": "688216",
                "name": "气派科技",
                "value": "+2.11",
                "ratio": "12.7%",
                "isSelected": false
            },
            {
                "code": "688300",
                "name": "联瑞新材",
                "value": "+1.85",
                "ratio": "15.1%",
                "isSelected": false
            },
            {
                "code": "688326",
                "name": "经纬恒润",
                "value": "+1.9",
                "ratio": "12.1%",
                "isSelected": false
            },
            {
                "code": "688350",
                "name": "富淼科技",
                "value": "+1.67",
                "ratio": "12.5%",
                "isSelected": false
            },
            {
                "code": "688353",
                "name": "华盛锂电",
                "value": "+2.05",
                "ratio": "13.6%",
                "isSelected": false
            },
            {
                "code": "688359",
                "name": "三孚新科",
                "value": "+1.65",
                "ratio": "15.0%",
                "isSelected": false
            },
            {
                "code": "688371",
                "name": "菲沃泰",
                "value": "+1.72",
                "ratio": "14.1%",
                "isSelected": false
            },
            {
                "code": "688387",
                "name": "信科移动",
                "value": "+1.57",
                "ratio": "14.8%",
                "isSelected": false
            },
            {
                "code": "688401",
                "name": "路维光电",
                "value": "+1.62",
                "ratio": "13.5%",
                "isSelected": false
            },
            {
                "code": "688403",
                "name": "汇成股份",
                "value": "+1.57",
                "ratio": "15.7%",
                "isSelected": false
            },
            {
                "code": "688469",
                "name": "芯联集成",
                "value": "+2.02",
                "ratio": "13.0%",
                "isSelected": false
            },
            {
                "code": "688498",
                "name": "源杰科技",
                "value": "+2.07",
                "ratio": "15.4%",
                "isSelected": false
            },
            {
                "code": "688549",
                "name": "中巨芯",
                "value": "+2.1",
                "ratio": "13.3%",
                "isSelected": false
            },
            {
                "code": "688550",
                "name": "瑞联新材",
                "value": "+1.93",
                "ratio": "12.8%",
                "isSelected": false
            },
            {
                "code": "688584",
                "name": "上海合晶",
                "value": "+1.98",
                "ratio": "14.8%",
                "isSelected": true
            },
            {
                "code": "688591",
                "name": "泰凌微",
                "value": "+1.62",
                "ratio": "13.7%",
                "isSelected": true
            },
            {
                "code": "688608",
                "name": "恒玄科技",
                "value": "+1.71",
                "ratio": "12.7%",
                "isSelected": false
            },
            {
                "code": "688620",
                "name": "安凯微",
                "value": "+1.92",
                "ratio": "15.3%",
                "isSelected": false
            },
            {
                "code": "688629",
                "name": "华丰科技",
                "value": "+1.53",
                "ratio": "11.1%",
                "isSelected": false
            },
            {
                "code": "688653",
                "name": "康希通信",
                "value": "+2.17",
                "ratio": "11.6%",
                "isSelected": false
            },
            {
                "code": "688662",
                "name": "富信科技",
                "value": "+1.96",
                "ratio": "14.2%",
                "isSelected": false
            },
            {
                "code": "688737",
                "name": "中自科技",
                "value": "+2.09",
                "ratio": "15.8%",
                "isSelected": false
            },
            {
                "code": "688766",
                "name": "普冉股份",
                "value": "+2.15",
                "ratio": "15.4%",
                "isSelected": false
            },
            {
                "code": "688776",
                "name": "国光电气",
                "value": "+1.66",
                "ratio": "15.2%",
                "isSelected": false
            },
            {
                "code": "688788",
                "name": "科思科技",
                "value": "+2.19",
                "ratio": "12.4%",
                "isSelected": false
            },
            {
                "code": "689009",
                "name": "九号公司",
                "value": "+2.08",
                "ratio": "12.8%",
                "isSelected": false
            }
        ],

        // 展示待查找的股票池
        stockList1:[
        ],

        // 系统模式列表【默认系统提供的有效模式，用于区间查找或选股】
        modeList: [
            {
                index: 'BA',
                name: '多头排列', // 模式名称
                lines: ["MA4", "MA8", "MA12", "MA16", "MA20", "MA47"], // 该模式选用的曲线
                isSelected: false, // 是否是自定义模式
                modeClass:'长期持续形态',
                modeDescription: '多头排列是指短期均线在中期均线之上，且中期均线在长期均线之上，形成多头排列的形态。',
                minDays: 5,
            },
            {
                index: 'BeA',
                name: '空头排列', 
                lines: ["MA4", "MA12", "MA20"], 
                isSelected: false,
                modeClass:'长期持续形态',
                modeDescription: '空头排列是指短期均线在中期均线之下，且中期均线在长期均线之下，形成空头排列的形态。',
                minDays: 5,
            },
            {
                index: 'GC',
                name: '黄金交叉', 
                lines:  ["MA4", "MA12", "MA20"], 
                isSelected: false,
                modeClass:'点状模式',
                modeDescription: '黄金交叉是指短期均线向上穿越中期均线，形成黄金交叉的形态。',
                minDays: 5,
            },
            {
                index: 'DC',
                name: '死亡交叉', 
                lines: ["MA4", "MA12", "MA20"], 
                isSelected: false,
                modeClass:'点状模式',
                modeDescription: '死亡交叉是指短期均线向下穿越中期均线，形成死亡交叉的形态。',
                minDays: 5,
            },
            // {
            //     index: 'SV',
            //     name: '银山谷', 
            //     lines: ["MA4", "MA12", "MA20"], 
            //     isSelected: false,
            //     modeClass:'短期形态',
            //     modeDescription: '银山谷是指短期均线在中期均线之上，且短期均线在长期均线之下，形成银山谷的形态。',
            //     minDays: 3,
            // },
            // {
            //     index: 'GV',
            //     name: '金山谷', 
            //     lines: ["MA4", "MA12", "MA20"], 
            //     isSelected: false,
            //     modeClass:'复杂形态',
            //     modeDescription: '金山谷是指短期均线在中期均线之下，且短期均线在长期均线之上，形成金山谷的形态。',
            //     minDays: 3,
            // },
            // {
            //     index: 'FCUD',
            //     name: '首次粘合后向上发散', 
            //     lines: ["MA4", "MA12", "MA20"], 
            //     isSelected: false,
            //     modeClass:'复杂形态',
            //     modeDescription: '首次粘合后向上发散是指短期均线在中期均线之上，且短期均线在长期均线之下，形成首次粘合后向上发散的形态。',
            //     minDays: 3,
            // },
            // {
            //     index: 'FCD',
            //     name: '首次粘合后向下发散', 
            //     lines: ["MA4", "MA12", "MA20"], 
            //     isSelected: false,
            //     modeClass:'复杂形态',
            //     modeDescription: '首次粘合后向下发散是指短期均线在中期均线之下，且短期均线在长期均线之上，形成首次粘合后向下发散的形态。',
            //     minDays: 3,
            // },
        ],
            
        // 自定义模式列表【用户可以自定义保存的模式，基于newSearchInfo添加几个指标项建立】
        // modeListSelf:[
        //     {
        //         index:'self_mode_1',
        //         name: '自定义模式1',
        //         lines: ["MA4","MA8", "MA12", "MA16", "MA20", "MA47"],
        //         modeFolder:'self_mode_1', // 保存刷选区间的文件夹
        //         selectedFactor : null,
        //         selectedFactor2 : null,
        //         photoOption: [],
        //         savedBrushTimeRanges: [{code: '000021', startDate: '2025-01-17', endDate: '2025-03-05', saveTime: 1754902645071}],
        //         recentNDaysValue: '近20天',
        //     },
        //     {
        //         index:'self_mode_2',
        //         name: '自定义模式2',
        //         lines: ["MA4","MA8", "MA12", "MA16", "MA20", "MA47"],
        //         modeFolder:'self_mode_2', // 保存刷选区间的文件夹
        //         selectedFactor : null,
        //         selectedFactor2 : null,
        //         photoOption: [],
        //         savedBrushTimeRanges: [
        //             {code: '000021', startDate: '2025-01-16', endDate: '2025-03-05', saveTime: 1754902744242},
        //             {code: '000021', startDate: '2025-01-07', endDate: '2025-02-27', saveTime: 1754902756597}
        //         ],
        //         recentNDaysValue: '近30天',
        //     },
        //     {
        //         index:'self_mode_3',
        //         name: '自定义模式3',
        //         lines: ["MA4","MA8", "MA12", "MA16", "MA20", "MA47"],
        //         modeFolder:'self_mode_3', // 保存刷选区间的文件夹
        //         selectedFactor : null,
        //         selectedFactor2 : null,
        //         photoOption: [],
        //         savedBrushTimeRanges: [
        //             {code: '000021', startDate: '2023-05-12', endDate: '2023-05-29', saveTime: 1754962444771},
        //             {code: '000021', startDate: '2022-07-15', endDate: '2022-08-08', saveTime: 1754962469512},
        //             {code: '000021', startDate: '2024-09-23', endDate: '2024-10-22', saveTime: 1754962496756}
        //         ],
        //         recentNDaysValue: '近40天',
        //     }
        // ],
        modeListSelf: [], // 初始化为空数组
    },

    // 用于修改 state 的方法，必须是同步的
    mutations: {
        setSimStockListWeekly(state, data) { state.sim_stock_list_weekly = data; },
        setSimStockListMonthly(state, data) { state.sim_stock_list_monthly = data; },

        setModeListSelf(state, data) {
            state.modeListSelf = data;
        },

        // 设置模式列表
        SET_MODE_LIST_SELF(state, data) {
        state.modeListSelf = data
        },
        // 添加新模式
        ADD_MODE_SELF(state, newMode) {
        state.modeListSelf.push(newMode)
        },

        updateNewSearchInfo(state, newSearchInfo) {
            state.newSearchInfo = {
                ...state.newSearchInfo,
                ...newSearchInfo
            };
        },
        
        // 新增：修改单个属性的方法
        updateNewSearchInfoProperty(state, { key, value }) {
            // 直接修改对象的单个属性
            state.newSearchInfo[key] = value;
        },
        // 更新训练集池
        updateTrainingPool(state, pool) {
            state.trainingPool = { ...state.trainingPool, ...pool };
        },
        updateStockList1(state, newList) {
            state.stockList1 = newList;
        },
        updateStockShowInfo(state, newInfo) {
            state.stockShowInfo = newInfo;
        },
        updateStockInfo(state, newInfo) {
            state.stockInfo = newInfo;
        },
        updateModeInfo(state, payload) {
              state.modeInfo = {
                ...state.modeInfo,        // 保留原有属性
                index: payload.index,
                name: payload.name,
                lines: payload.lines,
                lines1: payload.lines1,
                lines2: payload.lines2,
                isMode: payload.isMode,
                isSelected: payload.isSelected || state.modeInfo.isSelected,
                modeClass: payload.modeClass,
                modeDescription: payload.modeDescription,
                minDays: payload.minDays,
            };
        },
        updateSearchInfo(state, newInfo) {
            state.searchInfo = newInfo;
        },
        updateResultList(state, newList) {
            state.resultList = newList;
        },
        updateBaseInfo(state, newInfo) {
            state.baseInfo = newInfo;
        },
        updateResultStockInfo(state, newInfo){
            state.resultStockInfo = newInfo;
        }
    },

    // 用于处理异步操作，最终会调用 mutations 中的方法
    // 与后端相关的方法未启用
    actions: {
        // 加载modeListSelf数据的action
        async loadModeListSelf({ commit }) {
            try {
                const response = await axios.get('/modeListSelf.json'); // 请求public下的JSON文件
                commit('setModeListSelf', response.data);
            } catch (error) {
                console.error('加载modeListSelf失败:', error);
                commit('setModeListSelf', []); // 失败时设为空数组
            }
        },

        async fetchModeListSelf({ commit }) {
            try {
                const timestamp = new Date().getTime();
                const API_BASE_URL = 'http://127.0.0.1:5000'
                const response = await axios.get(`${API_BASE_URL}/get_modeListSelf_new?timestamp=${timestamp}`)
                if (response.data.success) {
                    commit('SET_MODE_LIST_SELF', response.data.data)
                    return true
                }
                return false
            } catch (error) {
                console.error('获取模式列表失败:', error)
                throw error
            }
        },
        
        // 新增模式到后端
        async addNewModeToSelfList({ commit }, newMode) {
            try {
                // 调用后端新增接口
                const timestamp = new Date().getTime();
                const API_BASE_URL = 'http://127.0.0.1:5000'
                const response = await axios.post(`${API_BASE_URL}/add_modeListSelf_new?timestamp=${timestamp}`, newMode)

                // 后端成功写入后，更新本地状态
                if (response.data.success) {
                commit('ADD_MODE_SELF', newMode)
                return true // 新增成功
                } else {
                throw new Error(response.data.message || '后端处理失败')
                }
            } catch (error) {
                console.error('新增自定义模式失败:', error)
                throw error // 抛出错误供组件捕获处理
            }
        },

        asyncUpdateGraphDataCode({ commit }, newCode) {
            // 模拟异步操作，比如调用 API
            return new Promise((resolve) => {
                setTimeout(() => {
                    commit('updateGraphDataCode', newCode);
                    resolve();
                }, 1000);
            });
        },

          // 获取股票信息
        async fetchStockInfo({ commit }) {
            try {
                const response = await fetch('/api/stocks/all');
                const data = await response.json();
                commit('updateStockInfo', data); // 使用原有的 mutation
                return data;
            } catch (error) {
                console.error('获取股票信息失败:', error);
                throw error;
            }
        },

        async fetchStockByCode({ commit }, stockCode) {
            commit('SET_LOADING', true);
            commit('SET_ERROR', null);
            try {
                // 调用后端接口
                const response = await fetch(`/api/stocks/code/${stockCode}`);
                // 检查HTTP状态码
                if (!response.ok) {
                    throw new Error(`HTTP错误，状态码: ${response.status}`);
                }
                const data = await response.json();
                commit('SET_STOCK', data);
                return data;
            } catch (error) {
                commit('SET_ERROR', error.message);
                console.error('获取股票数据失败:', error);
                throw error;
            } finally {
                commit('SET_LOADING', false);
            }
        },
        
        // 获取模式信息
        async fetchModeInfo({ commit }) {
            try {
                const response = await fetch('/api/modeInfo');
                const data = await response.json();
                commit('updateModeInfo', data); // 使用原有的 mutation
                return data;
            } catch (error) {
                console.error('获取模式信息失败:', error);
                throw error;
            }
        },
    
        // 获取股票列表
        async fetchStockList({ commit }) {
            try {
                const response = await fetch('/api/stockList');
                const data = await response.json();
                commit('updateStockList', data); // 使用原有的 mutation
                return data;
            } catch (error) {
                console.error('获取股票列表失败:', error);
                throw error;
            }
        },
        
        // 获取模式列表
        async fetchModeList({ commit }) {
            try {
                const response = await fetch('/api/modeList');
                const data = await response.json();
                commit('updateModeList', data); // 使用原有的 mutation
                return data;
            } catch (error) {
                console.error('获取模式列表失败:', error);
                throw error;
            }
        }
    },

    // 用于获取 state 中的数据，类似于计算属性
    getters: {
        getModeListSelf: (state) => state.modeListSelf,
        getGraphDataCode: (state) => state.graphDataCode,
        getStockList1: (state) => state.stockList1,
        getStockShowInfo: (state) => state.stockShowInfo,
        getStockInfo: (state) => state.stockInfo,
        getModeInfo: (state) => state.modeInfo,
        getSearchInfo: (state) => state.searchInfo,
        getResultList: (state) => state.resultList,
        getModeList: (state) => state.modeList,
        // 通过索引获取系统默认模式
        getModeListByIndex: (state) => (index) => {
            return state.modeList.find(mode => mode.index === index);
        },
        // 通过索引获取自定义模式
        getModeListSelfByIndex: (state) => (index) => {
            return state.modeListSelf.find(mode => mode.index === index);
        },
        // 通过code获取股票信息
        getStockByCode: (state) => (code) => {
            return state.stockList.find(stock => stock.code === code);
        },
        // 通过name获取股票信息
        getStockByName: (state) => (name) => {
            return state.stockList.find(stock => stock.name === name);
        },
    }
});

export default store;