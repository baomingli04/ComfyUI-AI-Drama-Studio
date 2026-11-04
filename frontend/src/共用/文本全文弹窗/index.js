import { 复制到剪贴板 } from '@/共用/复制文本'

export default {
  name: '文本全文弹窗',
  props: {
    显示: { type: Boolean, default: false },
    标题: { type: String, default: '全文' },
    内容: { type: String, default: '' }
  },
  methods: {
    async 复制() {
      const 成功 = await 复制到剪贴板(this.内容)
      if (成功) this.$message.success('已复制全文')
      else this.$message.warning('复制失败，请在弹窗里手动框选复制')
    }
  }
}
