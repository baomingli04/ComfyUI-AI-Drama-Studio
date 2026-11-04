const 应用配置 = window.__APP_CONFIG__ || {}

export default {
  name: '确认分类弹窗',
  props: {
    显示: { type: Boolean, default: false },
    分类列表: { type: Array, default: function () { return [] } }
  },
  data() {
    return {
      分类id: null
    }
  },
  computed: {
    上传地址() {
      return window.location.protocol + '//' + (应用配置.后端 || '127.0.0.1:8001') + '/api/技能/上传?分类id=' + (this.分类id || '')
    },
    上传头() {
      return { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') }
    }
  },
  methods: {
    上传成功(响应) {
      if (响应.ok) {
        this.$message.success('技能已上传：' + 响应.目录名)
        this.$emit('已上传')
      } else {
        this.$message.error(响应.error || '上传失败')
      }
    },
    上传失败() {
      this.$message.error('上传请求失败，请检查后端服务')
    }
  }
}
