import { 复制到剪贴板 } from '@/共用/复制文本'
import 文本全文弹窗 from '@/共用/文本全文弹窗/index.vue'

export default {
  name: '提示词单元格',
  components: { 'text-dialog': 文本全文弹窗 },
  props: {
    文本: { type: String, default: '' },
    标题: { type: String, default: '提示词全文' },
    行数: { type: Number, default: 2 }
  },
  data() {
    return {
      弹窗显示: false
    }
  },
  methods: {
    打开全文() {
      if (!this.文本) return
      this.弹窗显示 = true
    },
    async 复制() {
      const 成功 = await 复制到剪贴板(this.文本)
      if (成功) this.$message.success('已复制提示词')
      else this.$message.warning('复制失败，点单元格打开全文后手动框选')
    }
  }
}
