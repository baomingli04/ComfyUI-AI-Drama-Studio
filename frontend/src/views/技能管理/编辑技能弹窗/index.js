import { 发 } from '@/接口/请求'

export default {
  name: '编辑技能弹窗',
  props: {
    显示: { type: Boolean, default: false },
    技能: { type: Object, default: null },
    分类列表: { type: Array, default: () => [] }
  },
  data() {
    return {
      分类id: null,
      提交中: false
    }
  },
  watch: {
    显示(值) {
      if (值 && this.技能) {
        this.分类id = this.技能.分类id
      }
    }
  },
  methods: {
    async 提交() {
      if (!this.技能) {
        return
      }
      if (!this.分类id) {
        this.$message.warning('请选择分类')
        return
      }
      if (this.分类id === this.技能.分类id) {
        this.$emit('关闭')
        return
      }
      this.提交中 = true
      try {
        await 发('/api/技能/修改', { id: this.技能.id, 分类id: this.分类id })
        this.$message.success('分类已修改')
        this.$emit('已保存')
      } catch (e) {
        this.$message.error(e.message)
      } finally {
        this.提交中 = false
      }
    }
  }
}
