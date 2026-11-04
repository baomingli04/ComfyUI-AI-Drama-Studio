import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'
import 提示词单元格 from '@/共用/提示词单元格/index.vue'

export default {
  name: 'T7首尾帧页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗, 'ai-expand': 扩写行, 'prompt-cell': 提示词单元格 },
  data() {
    return {
      提交中: false,
      比例选项: ['16:9', '9:16', '3:4', '4:3', '1:1', '2:3', '3:2', '21:9'],
      扩写模式: 'single_frame',
      // H3-首尾帧8步加速.json 不认 MP：比例 + 一采MP 只在前端当「算宽高的输入」，
      // 算出来直接填进 视频宽/视频高 框；提交给后端的只有 宽 + 高 + 时长。
      表单: {
        输入图1: '',
        输入图2: '',
        正向提示词: '',
        比例: '16:9',
        一采MP: 0.4,
        视频宽: 864,
        视频高: 480,
        视频时长: 5
      }
    }
  },
  computed: {
    画布宽高() {
      return this.算画布(this.表单 && this.表单.比例, this.表单 && this.表单.一采MP)
    },
    总帧数() {
      // MiniMax H3 只认 17k+5 的帧数：max(5, round(秒×24)) 再向上补足
      const 帧 = Math.max(5, Math.round((this.表单.视频时长 || 0) * 24))
      return 帧 + ((5 - (帧 % 17)) % 17)
    }
  },
  watch: {
    // 比例 / 一采MP 一变就重算，结果直接写进宽高框。
    // 宽高框是唯一真源：手动改宽高后不会再被覆盖（除非又动了比例或一采MP）。
    画布宽高: {
      immediate: true,
      handler(v) {
        if (v && this.表单) {
          this.$set(this.表单, '视频宽', v.宽)
          this.$set(this.表单, '视频高', v.高)
        }
      }
    }
  },
  methods: {
    算画布(比例, mp) {
      const 比例表 = {
        '1:1': [1, 1], '2:3': [2, 3], '3:2': [3, 2], '3:4': [3, 4],
        '4:3': [4, 3], '9:16': [9, 16], '16:9': [16, 9], '21:9': [21, 9]
      }
      const 比 = 比例表[String(比例 || '').trim().split(' ')[0]]
      const m = Number(mp)
      if (!比 || !m) return null
      const v = Math.min(16, Math.max(0.1, m))
      const scale = Math.sqrt((v * 1024 * 1024) / (比[0] * 比[1]))
      const snap = n => Math.max(32, Math.round(n / 32) * 32)
      return { 宽: snap(比[0] * scale), 高: snap(比[1] * scale) }
    },
    // 手填宽高后吸附到 32 的倍数：MiniMax 画布 stride=32，非 32 倍数会被工作流直接判非法
    吸附32() {
      const 吸 = n => Math.max(32, Math.round(Number(n || 0) / 32) * 32)
      this.$set(this.表单, '视频宽', 吸(this.表单.视频宽))
      this.$set(this.表单, '视频高', 吸(this.表单.视频高))
    },
    图成功(序号, 响应) {
      if (响应.ok) {
        this.$set(this.表单, '输入图' + 序号, 响应.路径)
      } else {
        this.$message.error(响应.error || '上传失败')
      }
    },
    async 提交任务() {
      if (!this.表单.输入图1 || !this.表单.输入图2) {
        this.$message.warning('首帧和尾帧图都要上传')
        return
      }
      this.提交中 = true
      try {
        // 比例 / 一采MP 只是前端的「算宽高输入」，最终给后端的只有 宽 + 高 + 时长
        const 参数 = Object.assign({ 类型: '首尾帧' }, this.表单)
        delete 参数.比例
        delete 参数['一采MP']
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('首尾帧'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
