import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'
import 提示词资源库弹窗 from '@/共用/提示词资源库弹窗/index.vue'
import 提示词单元格 from '@/共用/提示词单元格/index.vue'

export default {
  name: 'T3B生成图片8K页',
  mixins: [混入],
  components: {
    'run-log-dialog': 运行日志弹窗,
    'media-thumbs': 媒体缩略图,
    'media-preview': 媒体预览弹窗,
    'ai-expand': 扩写行,
    'prompt-library-dialog': 提示词资源库弹窗,
    'prompt-cell': 提示词单元格,
  },
  data() {
    return {
      提交中: false,
      资源库显示: false,
      // 本页扩写下拉取「图片提示词扩写」分类下的技能
      扩写技能分类: '图片提示词扩写',
      比例示例: [
        { 比例: '1:1', 宽: 1024, 高: 1024 },
        { 比例: '16:9', 宽: 1280, 高: 720 },
        { 比例: '9:16', 宽: 720, 高: 1280 },
        { 比例: '4:3', 宽: 1024, 高: 768 },
        { 比例: '3:4', 宽: 768, 高: 1024 },
        { 比例: '3:2', 宽: 1152, 高: 768 },
        { 比例: '2:3', 宽: 768, 高: 1152 },
        { 比例: '21:9', 宽: 1344, 高: 576 }
      ],
      表单: { 正向提示词: '', 反向提示词: '', 图片宽: 1024, 图片高: 1024, seed: '', 水印: false }
    }
  },
  methods: {
    打开提示词资源库() {
      this.资源库显示 = true
    },
    采用提示词(数据) {
      this.表单.正向提示词 = 数据.正向提示词 || ''
      this.表单.反向提示词 = 数据.反向提示词 || ''
      this.$message.success('提示词已添加')
    },
    填宽高(项) {
      this.表单.图片宽 = 项.宽
      this.表单.图片高 = 项.高
    },
    async 提交任务() {
      if (!this.表单.正向提示词) {
        this.$message.warning('请输入正向提示词')
        return
      }
      this.提交中 = true
      try {
        const 数据 = await 发('/api/任务/提交', Object.assign({ 类型: '文生图8K' }, this.表单))
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('文生图8K'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
