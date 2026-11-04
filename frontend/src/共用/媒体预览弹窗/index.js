export default {
  name: '媒体预览弹窗',
  props: {
    显示: { type: Boolean, default: false },
    列表: { type: Array, default: () => [] },
    索引: { type: Number, default: 0 }
  },
  computed: {
    当前() {
      return this.列表[this.索引] || null
    }
  }
}
