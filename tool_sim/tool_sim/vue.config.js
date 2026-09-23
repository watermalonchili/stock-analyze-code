const { defineConfig } = require('@vue/cli-service')

// 根据环境变量设置不同的配置
const isProduction = process.env.NODE_ENV === 'production'

module.exports = defineConfig({
  // 生产环境使用相对路径，开发环境使用绝对路径
  publicPath: isProduction ? './' : '/',

  devServer: {
    proxy: {
      '/api': {
        target: isProduction ? 'http://backend:5000' : 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: { '^/api': '' },
        hot: false,
        liveReload: false,
      }
    }
  },

  transpileDependencies: true,

  chainWebpack: (config) => {
    config.module.rule('eslint').exclude.add(/node_modules/)
  },

  lintOnSave: false,

  css: {
    loaderOptions: {
      scss: {
        additionalData: `@import "@/styles/variables.scss";`
      }
    }
  },

  // 生产环境配置
  configureWebpack: config => {
    if (isProduction) {
      // 生产环境优化配置
      config.optimization = {
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
            }
          }
        }
      }
    }
  }
})
