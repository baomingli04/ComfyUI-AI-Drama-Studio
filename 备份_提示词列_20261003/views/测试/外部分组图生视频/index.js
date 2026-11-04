import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'

// 工作流只有 4 个 LoadImage 图位。Combine 的顺序是 group_0=23 / group_1=24 /
// group_2=35 / group_3=31，所以出片段序是：组1(首尾) → 组2(首) → 组3(尾) → 组4(纯提示词)。
// 图位依次落在：组1首(18) / 组1尾(19) / 组2首(20) / 组3尾(30)
const 图位 = [
  { 键: '输入图1', 名: '组1 首帧' },
  { 键: '输入图2', 名: '组1 尾帧' },
  { 键: '输入图3', 名: '组2 首帧' },
  { 键: '输入图4', 名: '组3 尾帧' }
]

export default {
  name: 'D8外部分组图生视频页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗, 'ai-expand': 扩写行 },
  data() {
    return {
      提交中: false,
      比例选项: ['16:9', '9:16', '3:4', '4:3', '1:1', '2:3', '3:2', '21:9'],
      扩写模式: 'single_frame',
      图位,
      当前位: 0,
      组数: [1, 2, 3, 4],
      展开组: [1],
      表单: {
        输入图1: '',
        输入图2: '',
        输入图3: '',
        输入图4: '',
        正向提示词: '',
        反向提示词: '',
        seed: '',
        cfg: 1,
        视频宽: 576,
        视频高: 736,
        比例: '3:4',
        一采MP: 0.4,
        视频时长: 1,
        组1提示词: '', 组2提示词: '', 组3提示词: '', 组4提示词: '',
        组1时长: '', 组2时长: '', 组3时长: '', 组4时长: ''
      }
    }
  },
  computed: {
    画布宽高() {
      return this.算画布(this.表单 && this.表单.比例, this.表单 && this.表单.一采MP)
    },
    总帧数() {
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
    选位(i) {
      this.当前位 = i
    },
    图成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      this.$set(this.表单, 图位[this.当前位].键, 响应.路径)
      for (let i = 0; i < 图位.length; i++) {
        if (!this.表单[图位[i].键]) {
          this.当前位 = i
          return
        }
      }
    },
    清空图(i) {
      this.$set(this.表单, 图位[i].键, '')
      this.当前位 = i
    },
    async 提交任务() {
      for (let i = 0; i < 图位.length; i++) {
        if (!this.表单[图位[i].键]) {
          this.$message.warning('请先上传「' + 图位[i].名 + '」')
          return
        }
      }
      const 参数 = Object.assign({ 类型: '外部分组图生视频' }, this.表单)
      this.组数.forEach(i => {
        if (!参数['组' + i + '提示词']) delete 参数['组' + i + '提示词']
        if (参数['组' + i + '时长'] === '' || 参数['组' + i + '时长'] === null) delete 参数['组' + i + '时长']
      })
      this.提交中 = true
      try {
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('外部分组图生视频'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
