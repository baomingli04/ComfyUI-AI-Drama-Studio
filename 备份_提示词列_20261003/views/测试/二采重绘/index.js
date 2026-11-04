import { 发, 取 } from '@/接口/请求'
import { 媒体地址, 是视频 } from '@/接口/媒体'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'

export default {
  name: 'T10二采重绘页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗, 'ai-expand': 扩写行 },
  data() {
    return {
      提交中: false,
      扩写模式: 'multi_reference',
      比例选项: ['1:1', '2:3', '3:2', '3:4', '4:3', '9:16', '16:9', '21:9'],
      表单: {
        输入视频1: '',
        输入图1: '',
        正向提示词: '',
        一采MP: '',
        二采MP: '',
        比例: '16:9',
        视频时长: 7
      }
    }
  },
  computed: {
    // 分辨率（只读显示，不提交）：按 docs/13 §0.6 公式，比例 + 一采MP → 32 倍数宽高
    分辨率文本() {
      const 兆像素 = parseFloat(this.表单.一采MP)
      const 比例 = this.表单.比例
      if (!兆像素 || !比例) return ''
      const 兆 = Math.min(16, Math.max(0.1, 兆像素))
      const 分段 = String(比例).split(':')
      const 宽比 = parseFloat(分段[0])
      const 高比 = parseFloat(分段[1])
      if (!宽比 || !高比) return ''
      const 倍数 = 32
      const 缩放 = Math.sqrt((兆 * 1024 * 1024) / (宽比 * 高比))
      const 宽 = Math.round((宽比 * 缩放) / 倍数) * 倍数
      const 高 = Math.round((高比 * 缩放) / 倍数) * 倍数
      return 宽 + ' × ' + 高
    },
    有参考音频() {
      return !!(this.表单.输入音频1 || this.表单.输入音频2 || this.表单.输入音频3)
    }
  },
  methods: {
    // 产物媒体：本页工作流有两个 VHS_VideoCombine —— 168 真输出（二采成品）落 output，
    // 285 预览（一采中间结果）save_output=False 落 ComfyUI temp。
    // 后端「收集输出」已把 temp 的稳定排到后面，所以 产物视频1 = 二采成品、产物视频2 = 一采预览。
    // 覆盖共用混入的同名方法，只为本页加角标（其他页没有 temp 预览，不该跟着标）。
    产物媒体(行) {
      const 列表 = []
      for (const 键 of ['产物视频1', '产物视频2']) {
        if (行[键] && 是视频(行[键])) 列表.push({ 类型: 'video', 名称: 键, 地址: 媒体地址(行[键]) })
      }
      if (列表.length === 2) {
        列表[0].角标 = 列表[0].名称 = '二采成品'
        列表[1].角标 = 列表[1].名称 = '一采预览'
      }
      return 列表
    },
    // 源视频：只占 输入视频1（工作流 144 一个源视频槽）
    视频成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      this.$set(this.表单, '输入视频1', 响应.路径)
    },
    清空源视频() {
      this.$set(this.表单, '输入视频1', '')
    },
    // 参考图：最多 8 张（工作流 137/139/146-151 共 8 个槽，比平台上限 9 更严）
    图成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      for (let i = 1; i <= 8; i++) {
        if (!this.表单['输入图' + i]) {
          this.$set(this.表单, '输入图' + i, 响应.路径)
          return
        }
      }
      this.$message.warning('参考图最多 8 张')
    },
    清空参考图() {
      for (let i = 1; i <= 8; i++) this.$set(this.表单, '输入图' + i, '')
    },
    // 参考音频：最多 3 个（工作流 155/163/164 共 3 个槽）
    音频成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      for (let i = 1; i <= 3; i++) {
        if (!this.表单['输入音频' + i]) {
          this.$set(this.表单, '输入音频' + i, 响应.路径)
          return
        }
      }
      this.$message.warning('参考音频最多 3 个')
    },
    清空参考音频() {
      for (let i = 1; i <= 3; i++) this.$set(this.表单, '输入音频' + i, '')
    },
    async 提交任务() {
      this.提交中 = true
      try {
        const 参数 = Object.assign({ 类型: '二采重绘' }, this.表单)
        for (let i = 1; i <= 8; i++) {
          if (!参数['输入图' + i]) delete 参数['输入图' + i]
        }
        for (let i = 1; i <= 3; i++) {
          if (!参数['输入音频' + i]) delete 参数['输入音频' + i]
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('二采重绘'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
