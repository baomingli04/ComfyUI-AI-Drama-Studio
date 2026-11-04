import { 菜单 } from './indexdata'
import { 取 } from '@/接口/请求'

export default {
  name: '壳',
  data() {
    return {
      菜单: 菜单,
      当前用户名: localStorage.getItem('用户名') || '',
      当前昵称: localStorage.getItem('昵称') || '',
      侧栏收起: false,
      平板: false
    }
  },
  computed: {
    当前路径() {
      // 子路由（如 /script/new、/video/director）要回落到菜单里的父项，才能高亮
      // 菜单项分两种：有子项的分组（取子项路径）和扁平一级项（取自身路径）
      const 全路径 = this.$route.path
      let 命中 = ''
      for (const 组 of this.菜单) {
        const 路径组 = 组.扁平 ? [组.路径] : (组.子项 || []).map(项 => 项.路径)
        for (const p of 路径组) {
          if (!p) continue
          if (全路径 === p) return p
          if (全路径.indexOf(p + '/') === 0 && p.length > 命中.length) 命中 = p
        }
      }
      return 命中 || 全路径
    },
    侧栏布局宽() {
      if (this.平板) return '0px'
      return this.侧栏收起 ? '64px' : '220px'
    }
  },
  created() {
    this.拉用户()
  },
  mounted() {
    this.检测宽度()
    window.addEventListener('resize', this.检测宽度)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.检测宽度)
  },
  methods: {
    检测宽度() {
      const 是平板 = window.innerWidth <= 1024
      if (是平板 !== this.平板) {
        this.平板 = 是平板
        this.侧栏收起 = 是平板
      }
    },
    切换侧栏() {
      this.侧栏收起 = !this.侧栏收起
    },
    async 拉用户() {
      try {
        const 数据 = await 取('/api/当前用户')
        this.当前用户名 = 数据.用户名
        this.当前昵称 = 数据.昵称
        localStorage.setItem('用户名', 数据.用户名)
        localStorage.setItem('昵称', 数据.昵称)
      } catch (e) {
        if (e.状态码 === 401) {
          this.$router.push('/登录')
        }
      }
    },
    跳转(路径) {
      if (this.$route.path !== 路径) {
        this.$router.push(路径)
      }
      if (this.平板) {
        this.侧栏收起 = true
      }
    },
    退出登录() {
      localStorage.removeItem('token')
      localStorage.removeItem('用户名')
      localStorage.removeItem('昵称')
      this.$router.push('/登录')
    }
  }
}
