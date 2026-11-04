export default {
  name: '登录',
  data() {
    return {
      表单: {
        用户名: '',
        密码: ''
      },
      记住账号密码: false,
      提交中: false,
      错误文字: ''
    }
  },
  created() {
    // 回填记住的账号密码
    try {
      const 已存 = JSON.parse(localStorage.getItem('记住登录') || 'null')
      if (已存 && 已存.用户名) {
        this.表单.用户名 = 已存.用户名 || ''
        this.表单.密码 = 已存.密码 || ''
        this.记住账号密码 = true
      }
    } catch (e) {
      /* 存档损坏按无记住处理 */
    }
  },
  methods: {
    async 提交() {
      if (!this.表单.用户名 || !this.表单.密码) {
        this.错误文字 = '请输入用户名和密码。'
        return
      }
      this.提交中 = true
      this.错误文字 = ''
      try {
        const 响应 = await fetch(
          window.location.protocol + '//' + ((window.__APP_CONFIG__ || {}).后端 || '127.0.0.1:8001') + '/api/登录',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.表单)
          }
        )
        const 数据 = await 响应.json()
        if (数据 && 数据.ok) {
          // 记住账号密码：勾选存、不勾清
          if (this.记住账号密码) {
            localStorage.setItem('记住登录', JSON.stringify({ 用户名: this.表单.用户名, 密码: this.表单.密码 }))
          } else {
            localStorage.removeItem('记住登录')
          }
          localStorage.setItem('token', 数据.token)
          localStorage.setItem('用户名', 数据.用户名 || '')
          localStorage.setItem('昵称', 数据.昵称 || '')
          this.$router.push('/user')
        } else {
          this.错误文字 = (数据 && 数据.error) || '登录失败。'
        }
      } catch (e) {
        this.错误文字 = '后端连不上，请检查服务是否启动。'
      } finally {
        this.提交中 = false
      }
    }
  }
}
