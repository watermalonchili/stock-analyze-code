import { createApp } from 'vue'

import * as echarts from 'echarts'

import ElementPlus from 'element-plus'

import 'element-plus/dist/index.css'
import './styles/basic.css'
import App from './App.vue'
import store from './store'

const app=createApp(App);
app.config.globalProperties.$echarts = echarts;
app.use(store)
app.use(ElementPlus)
app.mount('#app');