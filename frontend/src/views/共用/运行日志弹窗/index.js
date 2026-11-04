export default {
  name: '运行日志弹窗',
  props: {
    显示: { type: Boolean, default: false },
    日志: { type: String, default: '' },
    任务id: { type: [Number, String], default: '' },
    标题: { type: String, default: '' }
  }
}
