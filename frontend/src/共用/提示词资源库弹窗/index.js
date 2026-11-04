// 提示词资源库弹窗：浏览 comfyit.cn 提示词广场，选中一条后把正/反向提示词回传给页面。
// 用法：<提示词资源库弹窗 :显示="xx" @关闭="xx=false" @采用="采用提示词($event)"></...>
import { 取 } from '@/接口/请求'

export default {
  name: '提示词资源库弹窗',
  props: {
    显示: { type: Boolean, default: false }
  },
  data() {
    return {
      载入中: false,
      详情载入中: false,
      列表: [],
      当前: null,
      页: 1,
      每页: 20,
      总数: 0
    }
  },
  watch: {
    显示(值) {
      if (值 && !this.列表.length) this.拉列表(1)
    }
  },
  methods: {
    async 拉列表(页码) {
      this.载入中 = true
      try {
        const 数据 = await 取('/api/提示词资源库/列表?page=' + 页码)
        this.列表 = 数据.列表 || []
        this.总数 = 数据.总数 || 0
        this.每页 = 数据.每页 || 20
        this.页 = 数据.页 || 页码
        this.当前 = null
      } catch (e) {
        this.$message.error(e.message)
      } finally {
        this.载入中 = false
      }
    },
    翻页(页码) {
      this.拉列表(页码)
    },
    async 选条目(项) {
      // 先把封面/标题显示出来，提示词等详情回来再补（列表接口不给提示词）
      this.当前 = Object.assign({}, 项, { 正向提示词: '', 反向提示词: '' })
      this.详情载入中 = true
      try {
        const 数据 = await 取('/api/提示词资源库/详情?id=' + 项.id)
        this.$set(this.当前, '正向提示词', 数据.正向提示词 || '')
        this.$set(this.当前, '反向提示词', 数据.反向提示词 || '')
      } catch (e) {
        this.$message.error(e.message)
      } finally {
        this.详情载入中 = false
      }
    },
    采用() {
      if (!this.当前) return
      const 正向 = this.当前.正向提示词 || ''
      const 反向 = this.当前.反向提示词 || ''
      if (!正向 && !反向) {
        this.$message.warning('该条没有提示词')
        return
      }
      this.$emit('采用', { 正向提示词: 正向, 反向提示词: 反向 })
      this.$emit('关闭')
    }
  }
}
