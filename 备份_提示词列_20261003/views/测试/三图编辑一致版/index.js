import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'

export default {
  name: '三图编辑一致版页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗, 'ai-expand': 扩写行 },
  data() {
    return {
      提交中: false,
      // 本页扩写下拉取「图片提示词扩写」分类下的技能
      扩写技能分类: '图片提示词扩写',
      表单: { 输入图1: '', 输入图2: '', 输入图3: '', 正向提示词: '' }
    }
  },
  methods: {
    图成功(序号, 响应) {
      if (响应.ok) {
        this.$set(this.表单, '输入图' + 序号, 响应.路径)
      } else {
        this.$message.error(响应.error || '上传失败')
      }
    },
    async 提交任务() {
      // 1~3 张柔性：图1（主图）必填，图2/图3 可选（后端按张数摘掉多余图位）
      if (!this.表单.输入图1) {
        this.$message.warning('请先上传图1（主图）；图2、图3 可选')
        return
      }
      this.提交中 = true
      try {
        const 参数 = Object.assign({ 类型: '三图编辑一致版' }, this.表单)
        for (let i = 1; i <= 3; i++) {
          if (!参数['输入图' + i]) delete 参数['输入图' + i]
        }
        const 数据 = await 发('/api/任务/提交', 参数)
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('三图编辑一致版'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
