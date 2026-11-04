import { 发 } from '@/接口/请求'

export default {
  name: '新增分类弹窗',
  props: {
    显示: { type: Boolean, default: false }
  },
  data() {
    return {
      名称: '',
      提交中: false
    }
  },
  methods: {
    async 提交() {
      if (!this.名称.trim()) {
        this.$message.warning('请输入分类名称')
        return
      }
      this.提交中 = true
      try {
        await 发('/api/技能分类/新增', { 名称: this.名称.trim() })
        this.$message.success('分类已新增')
        this.名称 = ''
        this.$emit('已新增')
      } catch (e) {
        this.$message.error(e.message)
      } finally {
        this.提交中 = false
      }
    }
  }
}
