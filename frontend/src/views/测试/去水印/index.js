import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'

export default {
  name: 'T9去水印页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗 },
  data() {
    return {
      提交中: false,
      表单: { 输入图1: '' }
    }
  },
  methods: {
    图1成功(响应) {
      if (响应.ok) {
        this.表单.输入图1 = 响应.路径
      } else {
        this.$message.error(响应.error || '上传失败')
      }
    },
    async 提交任务() {
      if (!this.表单.输入图1) {
        this.$message.warning('请先上传要去水印的图片')
        return
      }
      this.提交中 = true
      try {
        const 数据 = await 发('/api/任务/提交', Object.assign({ 类型: '去水印' }, this.表单))
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('去水印'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
