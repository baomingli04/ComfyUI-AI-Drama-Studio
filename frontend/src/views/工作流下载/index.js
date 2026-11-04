import { 取 } from '@/接口/请求'

const 应用配置 = window.__APP_CONFIG__ || {}

export default {
  name: '工作流下载页',
  data() {
    return {
      文件列表: []
    }
  },
  computed: {
    上传地址() {
      return window.location.protocol + '//' + (应用配置.后端 || '127.0.0.1:8001') + '/api/工作流/上传'
    },
    上传头() {
      return { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') }
    }
  },
  created() {
    this.拉列表()
  },
  methods: {
    async 拉列表() {
      try {
        const 数据 = await 取('/api/工作流列表')
        this.文件列表 = 数据.列表
      } catch (e) {
        this.$message.error(e.message)
        if (e.状态码 === 401) {
          this.$router.push('/login')
        }
      }
    },
    大小文本(字节) {
      if (字节 > 1048576) {
        return (字节 / 1048576).toFixed(1) + ' MB'
      }
      if (字节 > 1024) {
        return (字节 / 1024).toFixed(1) + ' KB'
      }
      return 字节 + ' B'
    },
    下载(行) {
      // 与现有项目一致：直接拼后端地址用 a 标签下载
      const 地址 = window.location.protocol + '//' + (应用配置.后端 || '127.0.0.1:8001') + '/api/工作流/下载?名=' + encodeURIComponent(行.名) + '&token=' + (localStorage.getItem('token') || '')
      const 链接 = document.createElement('a')
      链接.href = 地址
      链接.click()
    },
    上传成功(响应) {
      if (响应.ok) {
        this.$message.success('已上传：' + 响应.名)
        this.拉列表()
      } else {
        this.$message.error(响应.error || '上传失败')
      }
    },
    上传失败() {
      this.$message.error('上传请求失败，请检查后端服务')
    }
  }
}
