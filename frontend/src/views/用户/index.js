import { 取 } from '@/接口/请求'

export default {
  name: '用户页',
  data() {
    return {
      加载中: false,
      用户信息: null,
      错误文字: ''
    }
  },
  created() {
    this.拉用户()
  },
  methods: {
    async 拉用户() {
      this.加载中 = true
      this.错误文字 = ''
      try {
        this.用户信息 = await 取('/api/当前用户')
      } catch (e) {
        this.错误文字 = e.message
        if (e.状态码 === 401) {
          this.$router.push('/登录')
        }
      } finally {
        this.加载中 = false
      }
    }
  }
}
