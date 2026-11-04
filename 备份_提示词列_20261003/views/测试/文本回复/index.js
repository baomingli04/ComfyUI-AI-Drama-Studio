import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'

export default {
  name: 'T1文本回复页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗 },
  data() {
    return {
      提交中: false,
      表单: { 正向提示词: '', 系统提示词: '' }
    }
  },
  methods: {
    async 提交任务() {
      this.提交中 = true
      try {
        const 数据 = await 发('/api/任务/提交', Object.assign({ 类型: '文本回复' }, this.表单))
        this.$message.success('任务已提交，id=' + 数据.id)
        this.拉任务列表()
      } catch (e) {
        this.报错(e)
      } finally {
        this.提交中 = false
      }
    },
    async 拉任务列表() {
      try {
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('文本回复'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    },
    结果文本(行) {
      return 行.回复 || (行.错误信息 ? '错误：' + 行.错误信息 : '')
    }
  }
}
