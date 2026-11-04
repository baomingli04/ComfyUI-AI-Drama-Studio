import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'

export default {
  name: 'D1文生视频页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗, 'ai-expand': 扩写行 },
  data() {
    return {
      提交中: false,
      比例选项: ['16:9', '9:16', '3:4', '4:3', '1:1', '2:3', '3:2', '21:9'],
      扩写模式: 'image',
      表单: {
        正向提示词: '',
        反向提示词: '',
        seed: '',
        cfg: 1,
        视频宽: 864,
        视频高: 480,
        比例: '16:9',
        一采MP: 0.4,
        视频时长: 5
      }
    }
  },
  computed: {
    画布宽高() {
      return this.算画布(this.表单 && this.表单.比例, this.表单 && this.表单.一采MP)
    },
    总帧数() {
      // MiniMax H3 只认 17k+5 的帧数：max(5, round(秒×帧率)) 再向上补足
      const 帧 = Math.max(5, Math.round((this.表单.视频时长 || 0) * 24))
      return 帧 + ((5 - (帧 % 17)) % 17)
    }
  },
  watch: {
    // 画布是「比例 + 一采MP」的派生值，同步回表单，提交时才有像素宽高落库
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
    async 提交任务() {
      if (!this.表单.正向提示词 || !this.表单.正向提示词.trim()) {
        this.$message.warning('请先填写正向提示词')
        return
      }
      this.提交中 = true
      try {
        const 数据 = await 发('/api/任务/提交', Object.assign({ 类型: '文生视频' }, this.表单))
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('文生视频'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
