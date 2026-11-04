import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import { 媒体地址, 是图片, 是视频, 是音频 } from '@/接口/媒体'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'
import 提示词单元格 from '@/共用/提示词单元格/index.vue'
import { 默认规则集, 扩写模式集, 模式说明集 } from './扩写规则'

// 随机种子：进页面时换一个新种子用（用户 2026-10-23 要求）。
// 区间与后端 能力/工作流工具.py 的 随机种子() 对齐：0 ~ 2^48，
// 保证前端生成的种子落在 ComfyUI 种子节点接受的整数范围内，后端不会二次改写。
function 新种子() {
  return Math.floor(Math.random() * 2 ** 48)
}

// 模式 → 底膜族（与后端 模式配置 的第二个元素一致，官方配对 README.md:42）
//   t2v / i2v / fl2v → fl2va    r2v / v2v / rv2v → ref2va
// 具体文件名由下面的 底膜文件 按「族 × 精度」给出，不要在两处各写一份。
const 底膜族表 = {
  t2v: 'fl2va', i2v: 'fl2va', fl2v: 'fl2va',
  r2v: 'ref2va', v2v: 'ref2va', rv2v: 'ref2va'
}

// 族 × 精度 → 具体文件。**以 能力/导演台全能.py 的 基座模型文件 为准**，
// 这里只为在页面上显示"这次到底会加载哪个文件"，改了后端记得同步（两边都核对过
// 4 个文件都在 /object_info 的 UNETLoader 下拉里）。
const 底膜文件 = {
  ref2va: {
    auto: 'minimax_h3_ref2va_pruned_bf16.safetensors',
    bf16: 'minimax_h3_ref2va_pruned_bf16.safetensors',
    int8: 'minimax_h3_ref2va_pruned_int8_convrot.safetensors'
  },
  fl2va: {
    auto: 'minimax_h3_fl2va_pruned_int8_convrot.safetensors',
    bf16: 'minimax_h3_fl2va_pruned_bf16.safetensors',
    int8: 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'
  }
}

// 精度档位 → (简称, 说明, 单文件体积)。默认 auto = 本项目原有行为，不动任何实测配置。
const 底膜精度档 = {
  auto: { 简称: '工作流默认', 说明: 'ref2va 用 bf16（工作流原值）、fl2va 用 int8，与现在完全一致', 体积: '' },
  bf16: { 简称: 'bf16', 说明: '两个族都用 bf16：画质上限最高，但显存最紧、首次加载约 5 分钟', 体积: '约 38 GB' },
  int8: { 简称: 'int8 convrot', 说明: '两个族都用 int8：官方推荐，显存约省一半、加载快很多，画质略降', 体积: '约 20 GB' }
}

// 这 3 个模式在插件里都是「单段」跑（见后端 导演台全能.py 的 _单段 注释）：
// i2v 每段都要一份源图，多段等于每段都从图重开；v2v/rv2v 的段区间由源片长度切。
const 单段模式 = ['i2v', 'v2v', 'rv2v']

const 模式中文表 = {
  t2v: '文生视频', i2v: '图生视频', fl2v: '首尾帧', r2v: '参考主体',
  v2v: '视频转视频', rv2v: '参考改视频'
}

export default {
  name: '导演台全能页',
  mixins: [混入],
  components: {
    'run-log-dialog': 运行日志弹窗,
    'media-thumbs': 媒体缩略图,
    'media-preview': 媒体预览弹窗,
    'ai-expand': 扩写行,
    'prompt-cell': 提示词单元格
  },
  data() {
    return {
      提交中: false,
      比例选项: ['16:9', '9:16', '3:4', '4:3', '1:1', '2:3', '3:2', '21:9'],
      采样器选项: ['res_multistep', 'euler', 'euler_ancestral', 'dpmpp_2m',
        'dpmpp_2m_sde', 'dpmpp_3m_sde', 'uni_pc', 'ddim'],
      // 扩写模式由 表单.模式 决定（见 watch），这里给默认模式 r2v 对应的值。
      // 不能写成同名 computed：混入里 扩写模式 是 data，Vue2 会告警且 computed 不生效。
      扩写模式: 'multi_reference',
      // 默认值全部对齐「MiniMax H3 导演台全能工作流.json」里已跑通的配置，不要随手改：
      //   模式 r2v（task_type=r2v）· 864×480（16:9 + 0.4MP）· 24fps · 15s（两段 10s+5s=367帧）
      //   cfg=1 · seed=666 · steps=8（turbo 8step LoRA）· res_multistep · 有声 · bad video
      //   seed 例外：进页面时每次换一个新的随机数（用户 2026-10-23 要求），
      //   区间和后端 随机种子() 一致（0 ~ 2^48），不写死 666 免得每次进页面都同一个种子。
      表单: {
        模式: 'r2v',
        输入图1: '', 输入图2: '', 输入图3: '', 输入图4: '', 输入图5: '',
        输入图6: '', 输入图7: '', 输入图8: '', 输入图9: '',
        输入视频1: '', 输入视频2: '', 输入视频3: '',
        输入音频1: '', 输入音频2: '', 输入音频3: '',
        正向提示词: '',
        反向提示词: 'bad video',
        seed: 新种子(),
        cfg: 1,
        比例: '16:9',
        一采MP: 0.4,
        视频时长: 15,
        生成声音: true,
        步数: 8,
        采样器: 'res_multistep',
        // 底膜精度：默认 int8（用户 2026-10-23 明确要求前端默认 int8）。
        // int8 = 两个族都用 int8 convrot：官方推荐、显存约省一半、加载约 40 秒；
        // 想按工作流原值跑就手动切「工作流默认」（ref2va bf16 / fl2va int8）。
        底膜精度: 'int8',
        视频宽: 0,
        视频高: 0
      }
    }
  },
  computed: {
    当前底膜提示() {
      const 档 = this.当前底膜精度档
      const 体积 = 档.体积 ? '（' + 档.体积 + '）' : ''
      return this.当前底膜族 + ' · ' + this.当前底膜文件 + 体积
    },
    当前底膜族() {
      return 底膜族表[this.表单.模式] || 'ref2va'
    },
    // 这次真正会加载的文件（族 × 精度）。int8 档下 ref2va 也会变成 int8，
    // 这一点必须让用户在提交前看见 —— 换文件 = 重新加载模型，5 分钟那种。
    当前底膜文件() {
      const 族 = this.当前底膜族
      const 档 = (底膜文件[族] || {})[this.表单.底膜精度] || (底膜文件[族] || {}).auto
      return 档 || ''
    },
    当前底膜精度档() {
      return 底膜精度档[this.表单.底膜精度] || 底膜精度档.auto
    },
    底膜精度选项() {
      return Object.keys(底膜精度档)
    },
    // 模板里要遍历三档拿简称，Vue2 的模板摸不到模块级常量，这里转一手
    底膜精度档表() {
      return 底膜精度档
    },
    画布宽高() {
      return this.算画布(this.表单 && this.表单.比例, this.表单 && this.表单.一采MP)
    },
    // 总帧数：两段模式（t2v/r2v）不在这里算，工作流是「10s + 5s」两段结构，后端按各段
    // 原时长比例分配后再各自补到 17k+5（15s → 243+124=367 帧）；单段模式
    // （i2v/v2v/rv2v）就是 最小帧数 = round(秒×24) 再补到 17k+5。
    帧数说明() {
      const 秒 = Number(this.表单.视频时长) || 0
      if (单段模式.indexOf(this.表单.模式) >= 0) {
        return '单段 → ' + this.单段帧数(秒) + ' 帧'
      }
      if (秒 === 15) return '工作流分段 10s+5s → 243+124 = 367 帧（与工作流默认一致）'
      return '后端按工作流分段比例分配时长，每段补到 17k+5（改时长会等比缩放分段）'
    },
    有参考视频() {
      return this.参考视频数 > 0
    },
    有参考音频() {
      return !!(this.表单.输入音频1 || this.表单.输入音频2 || this.表单.输入音频3)
    },
    已传图数() {
      let 数 = 0
      for (let i = 1; i <= 9; i++) if (this.表单['输入图' + i]) 数++
      return 数
    },
    首帧媒体() {
      return (this.表单.输入图1 && 是图片(this.表单.输入图1))
        ? [{ 类型: 'image', 名称: '首帧', 地址: 媒体地址(this.表单.输入图1) }] : []
    },
    尾帧媒体() {
      return (this.表单.输入图2 && 是图片(this.表单.输入图2))
        ? [{ 类型: 'image', 名称: '尾帧', 地址: 媒体地址(this.表单.输入图2) }] : []
    },
    源视频媒体() {
      return (this.表单.输入视频1 && 是视频(this.表单.输入视频1))
        ? [{ 类型: 'video', 名称: '源视频', 地址: 媒体地址(this.表单.输入视频1) }] : []
    },
    参考视频媒体() {
      const 列表 = []
      for (let i = 1; i <= 3; i++) {
        const 路径 = this.表单['输入视频' + i]
        if (路径 && 是视频(路径)) {
          列表.push({ 类型: 'video', 名称: '参考视频' + i, 地址: 媒体地址(路径) })
        }
      }
      return 列表
    },
    参考视频数() {
      return this.参考视频媒体.length
    },
    // 「参考图」行只显示图。混入里的 表单媒体列表() 把图/视频/音频混在一个列表里，
    // 放在参考图行会把视频音频的缩略图也列出来，串行。
    参考图媒体() {
      const 列表 = []
      for (let i = 1; i <= 9; i++) {
        const 路径 = this.表单['输入图' + i]
        if (路径 && 是图片(路径)) {
          列表.push({ 类型: 'image', 名称: '参考图' + i, 地址: 媒体地址(路径) })
        }
      }
      return 列表
    },
    // 「参考音频」行（之前只有文字提示，传完看不到传了什么）
    参考音频媒体() {
      const 列表 = []
      for (let i = 1; i <= 3; i++) {
        const 路径 = this.表单['输入音频' + i]
        if (路径 && 是音频(路径)) {
          列表.push({ 类型: 'audio', 名称: '参考音频' + i, 地址: 媒体地址(路径) })
        }
      }
      return 列表
    },
    // ---- 扩写：一页六模式 → 六条规则 ----
    // 库里的键形如 扩写:/test/d-all:r2v，与已有页面 扩写:<路由> 的约定同源，只是多一段模式后缀
    扩写配置类型() {
      const 路径 = (this.$route && this.$route.path) || '/test/d-all'
      return '扩写:' + 路径 + ':' + (this.表单.模式 || 'r2v')
    },
    当前扩写规则() {
      return 默认规则集[this.表单.模式] || 默认规则集.t2v
    },
    模式说明() {
      return 模式说明集[this.表单.模式] || ''
    },
    模式中文() {
      return 模式中文表[this.表单.模式] || ''
    },
    是单段模式() {
      return 单段模式.indexOf(this.表单.模式) >= 0
    },
    需要源视频() {
      return this.表单.模式 === 'v2v' || this.表单.模式 === 'rv2v'
    },
    // 把模式名带到扩写行文案上，用户一眼知道现在改的是哪个模式的规则
    扩写文案() {
      return {
        配置文字: '扩写提示词配置（' + this.模式中文 + '）',
        配置说明: '这里是「' + this.模式中文 + '」模式专用的扩写规则，会原样附加到本模式扩写的系统提示词里，'
          + '优先级最高。切模式会自动换成对应那一套，互不影响。可自由增删改。'
      }
    },
    // 扩写的声音字段跟随「生成声音」开关：关 → 完全无声，两段都写 N/A；
    // 开 → 按需求写（未提配乐时 non_diegetic_music 仍写 N/A）
    扩写声音模式() {
      return this.表单.生成声音 ? 'custom' : 'silent'
    },
    // 导演台组件的「声音」下拉只在 v2v / rv2v / r2v 出现
    // （minimax_timeline.js:5054-5055），t2v / i2v / fl2v 下整个是隐藏的，
    // 那几个模式沿用工作流里存的声音设置，页面也就不显示这个开关。
    声音可用() {
      return ['r2v', 'v2v', 'rv2v'].indexOf(this.表单.模式) >= 0
    }
  },
  watch: {
    画布宽高: {
      immediate: true,
      handler(v) {
        if (v && this.表单) {
          this.$set(this.表单, '视频宽', v.宽)
          this.$set(this.表单, '视频高', v.高)
        }
      }
    },
    // 切模式要同步三件事，缺一个都会串模式：
    //   1) 清素材：r2v 的参考图占 输入图1~9，fl2v 的首帧/尾帧也是 输入图1/2，
    //      v2v/rv2v 的源片占 输入视频1；不清会把上一模式的素材当成新模式的输入提交上去；
    //   2) 换扩写模式：t2v/i2v/fl2v/v2v 走 single_frame（后端再按图数分 T2VA / I2VA / FL2VA），
    //      r2v/rv2v 走 multi_reference（六段式）；写死一个值必然有一边写错格式；
    //   3) 扩写规则与配置键由 computed 跟着 表单.模式 走，扩写行会自动重新载入。
    '表单.模式': {
      immediate: true,
      handler(新值, 旧值) {
        this.扩写模式 = 扩写模式集[新值] || 'single_frame'
        if (新值 === 旧值) return
        this.清空全部素材()
        // 提示词不清（可能手改过），但必须提醒：上一个模式的提示词格式放到新模式就是错的
        if ((this.表单.正向提示词 || '').trim()) {
          this.$message.warning('已切到「' + this.模式中文 + '」，正向提示词还是上一个模式的内容，建议按新模式重新扩写')
        }
      }
    }
  },
  methods: {
    // 与后端 导演台工具.最小帧数 同一套公式：max(5, round(秒×帧率)) 再补到 17k+5
    单段帧数(秒) {
      const 帧 = Math.max(5, Math.round((Number(秒) || 0) * 24))
      return 帧 + (5 - (帧 % 17)) % 17
    },
    模式短名(键) {
      if (!键) return '-'
      return 模式中文表[键] ? 模式中文表[键] + '(' + 键 + ')' : 键
    },
    底膜精度短名(键) {
      const 档 = 底膜精度档[键]
      return 档 ? 档.简称 : 底膜精度档.auto.简称
    },
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
    // ---- 任务列表里输入媒体的展示（按模式改名，别让用户看一堆「输入图1」） ----
    输入媒体(行) {
      const 模式 = 行.模式 || 'r2v'
      const 图改名 = {}
      const 视频改名 = {}
      if (模式 === 'fl2v') {
        图改名['输入图1'] = '首帧'
        图改名['输入图2'] = '尾帧'
      } else if (模式 === 'i2v') {
        图改名['输入图1'] = '首帧图'
      }
      if (模式 === 'v2v' || 模式 === 'rv2v') {
        视频改名['输入视频1'] = '源视频'
      }
      const 列表 = []
      for (let i = 1; i <= 9; i++) {
        const 路径 = 行['输入图' + i]
        if (路径 && 是图片(路径)) {
          列表.push({ 类型: 'image', 名称: 图改名['输入图' + i] || '输入图' + i, 地址: 媒体地址(路径) })
        }
      }
      for (let i = 1; i <= 3; i++) {
        const 路径 = 行['输入视频' + i]
        if (路径 && 是视频(路径)) {
          列表.push({ 类型: 'video', 名称: 视频改名['输入视频' + i] || '输入视频' + i, 地址: 媒体地址(路径) })
        }
      }
      for (let i = 1; i <= 3; i++) {
        const 路径 = 行['输入音频' + i]
        if (路径 && 是音频(路径)) 列表.push({ 类型: 'audio', 名称: '输入音频' + i, 地址: 媒体地址(路径) })
      }
      return 列表
    },
    // ---- r2v 参考素材 ----
    图成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      for (let i = 1; i <= 9; i++) {
        if (!this.表单['输入图' + i]) {
          this.$set(this.表单, '输入图' + i, 响应.路径)
          return
        }
      }
      this.$message.warning('参考图最多 9 张')
    },
    清空参考() {
      for (let i = 1; i <= 9; i++) this.$set(this.表单, '输入图' + i, '')
    },
    // ---- 参考视频（只有 r2v 用；v2v/rv2v 官方没有参考视频槽） ----
    视频成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      for (let i = 1; i <= 3; i++) {
        if (!this.表单['输入视频' + i]) {
          this.$set(this.表单, '输入视频' + i, 响应.路径)
          return
        }
      }
      this.$message.warning('参考视频最多 3 个')
    },
    清空参考视频() {
      for (let i = 1; i <= 3; i++) this.$set(this.表单, '输入视频' + i, '')
    },
    // ---- 源视频（v2v / rv2v 的 输入视频1） ----
    源视频成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      this.$set(this.表单, '输入视频1', 响应.路径)
    },
    清空源视频() {
      this.$set(this.表单, '输入视频1', '')
    },
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
    // ---- 逐条删除 ----
    // 缩略图组件 emit('删除', 下标)，下标是**显示列表**里的位置（从 0 开始）。
    // 删中间一条后，后面的素材要依次前移，保持 输入XX1..N 连续 ——
    // 提示词里的 <Picture N>/<Video N>/<Audio N> 就是按这个槽位顺序引用的，
    // 中间留空槽会让编号和实际素材对不上。
    删图(下标) {
      const 值 = []
      for (let i = 1; i <= 9; i++) if (this.表单['输入图' + i]) 值.push(this.表单['输入图' + i])
      if (下标 < 0 || 下标 >= 值.length) return
      值.splice(下标, 1)
      for (let i = 1; i <= 9; i++) this.$set(this.表单, '输入图' + i, 值[i - 1] || '')
    },
    删视频(下标) {
      const 值 = []
      for (let i = 1; i <= 3; i++) if (this.表单['输入视频' + i]) 值.push(this.表单['输入视频' + i])
      if (下标 < 0 || 下标 >= 值.length) return
      值.splice(下标, 1)
      for (let i = 1; i <= 3; i++) this.$set(this.表单, '输入视频' + i, 值[i - 1] || '')
    },
    删音频(下标) {
      const 值 = []
      for (let i = 1; i <= 3; i++) if (this.表单['输入音频' + i]) 值.push(this.表单['输入音频' + i])
      if (下标 < 0 || 下标 >= 值.length) return
      值.splice(下标, 1)
      for (let i = 1; i <= 3; i++) this.$set(this.表单, '输入音频' + i, 值[i - 1] || '')
    },
    // fl2v 删首帧要特殊处理：尾帧还在时，删首帧会让尾帧顶到首帧位（模式按 I2VA 生成），
    // 图还是那张图但含义变了，必须让用户确认，不能悄悄换。
    async 删首帧() {
      if (this.表单.输入图2) {
        try {
          await this.$confirm('删掉首帧后，尾帧会变成首帧（按 I2VA 生成），确定吗？', '提示', { type: 'warning' })
        } catch (e) {
          return // 用户取消
        }
      }
      this.删图(0)
    },
    删尾帧() {
      // 尾帧永远是最后一张图，删显示列表里的最后一条即可
      const 总数 = this.参考图媒体.length
      if (总数) this.删图(总数 - 1)
    },
    删源视频() {
      this.$set(this.表单, '输入视频1', '')
    },
    // ---- fl2v 首帧 / 尾帧 ----
    清空全部素材() {
      for (let i = 1; i <= 9; i++) this.$set(this.表单, '输入图' + i, '')
      for (let i = 1; i <= 3; i++) {
        this.$set(this.表单, '输入视频' + i, '')
        this.$set(this.表单, '输入音频' + i, '')
      }
    },
    首帧成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      this.$set(this.表单, '输入图1', 响应.路径)
    },
    尾帧成功(响应) {
      if (!响应.ok) {
        this.$message.error(响应.error || '上传失败')
        return
      }
      // 只有尾帧、没有首帧是没意义的状态：扩写会把它当成「唯一一张图」按 I2VA 写首帧锚点，
      // 提交时又会被「请先上传首帧」拦住。所以这里先卡一道。
      if (!this.表单.输入图1) {
        this.$message.warning('请先上传首帧，再传尾帧')
        return
      }
      this.$set(this.表单, '输入图2', 响应.路径)
    },
    清空首帧() {
      this.$set(this.表单, '输入图1', '')
    },
    清空尾帧() {
      this.$set(this.表单, '输入图2', '')
    },
    // 参数一键回到「MiniMax H3 导演台全能工作流.json」里已跑通的那组值。
    // 只动参数，不动 模式 / 素材 / 提示词（那些是用户当次填的内容）。
    // 底膜精度默认档按用户要求定为 int8（2026-10-23），不再回到 auto。
    恢复工作流默认() {
      const 默认 = {
        反向提示词: 'bad video', seed: 666, cfg: 1, 比例: '16:9', 一采MP: 0.4,
        视频时长: 15, 生成声音: true, 步数: 8, 采样器: 'res_multistep',
        底膜精度: 'int8'
      }
      Object.keys(默认).forEach(键 => this.$set(this.表单, 键, 默认[键]))
      this.$message.success('已恢复工作流默认参数')
    },
    // fl2v 有「只首帧（I2VA）」和「首尾帧（FL2VA）」两种写法，靠模型自己数素材会猜错
    // （实测：只传首帧时它仍按 FL2VA 写了对齐行 + Picture 2）。
    // 所以这里按实际上传情况，把当前子模式写死追加到规则末尾（后端会当成最高优先级的用户附加规则）。
    带子模式规则(规则) {
      const 原文 = 规则 || ''
      const 秒 = (Number(this.表单.视频时长) || 15).toFixed(2)

      if (this.表单.模式 === 'i2v') {
        return 原文 + '\n\n==== 本页当前状态（最高优先级）====\n'
          + '本页是「图生视频」：只上传了 1 张图，它就是整条视频的第 0 帧（共 1 张图），必须用 I2VA 写法。'
          + '第一行必须是：For the target video, at 0.00 seconds into the target video, '
          + '<Picture 1> (from [Shot 1]) is fully referenced. '
          + '禁止出现 Picture 2、禁止写对齐行（How the reference pictures align…）、禁止写结束时刻；'
          + '整片时长 ' + 秒 + ' 秒，所有时间点都必须小于它。'
      }

      if (this.表单.模式 === 'fl2v') {
        if (this.表单.输入图2) {
          return 原文 + '\n\n==== 本页当前状态（最高优先级）====\n'
            + '本次首帧、尾帧都已上传（共 2 张图），必须用 FL2VA 写法：'
            + '第一行是对齐行 How the reference pictures align with the target video — '
            + 'Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; '
            + 'Picture 2 (from Shot N) aligns with the ' + 秒 + '-second mark of the target video.'
        }
        return 原文 + '\n\n==== 本页当前状态（最高优先级）====\n'
          + '本次只上传了首帧，没有尾帧（共 1 张图），必须用 I2VA 写法：'
          + '第一行是 For the target video, at 0.00 seconds into the target video, '
          + '<Picture 1> (from [Shot 1]) is fully referenced. '
          + '禁止出现 Picture 2、禁止写对齐行（How the reference pictures align…）、禁止写结束时刻。'
      }

      if (this.表单.模式 === 'v2v') {
        return 原文 + '\n\n==== 本页当前状态（最高优先级）====\n'
          + '本页是「视频转视频」：没有上传任何参考图，唯一的素材是源视频，它在提示词里只能叫 <Video 1>。'
          + '禁止出现 <Picture N> / <Subject N> / <Audio N>；禁止写对齐行；禁止用 Ref2VA 六段式。'
          + '整片时长 ' + 秒 + ' 秒，内容必须按源片时间轴铺满全程。'
      }

      if (this.表单.模式 === 'rv2v') {
        return 原文 + '\n\n==== 本页当前状态（最高优先级）====\n'
          + '本页是「参考素材改视频」：源视频是 <Video 1>（必须保留它的运镜、剪辑节奏与场景结构），'
          + '参考图依次是 <Picture 1>' + (this.已传图数 > 1 ? ' … <Picture ' + this.已传图数 + '>' : '')
          + (this.有参考音频 ? '，参考音频依次是 <Audio 1>' + (this.表单.输入音频2 ? ' …' : '') : '')
          + '。整片时长 ' + 秒 + ' 秒。'
          + (this.已传图数 === 0
            ? '注意：本次没有上传任何参考图，所以不得凭空写 <Subject N> 或 <Picture N>，只引用 <Video 1>。'
            : '')
      }

      return 原文
    },
    async 提交任务() {
      const 模式 = this.表单.模式
      const 有提示词 = !!(this.表单.正向提示词 || '').trim()
      // 校验顺序跟后端一致：先看素材，再看提示词。后端也会再拦一遍（防绕过页面）。
      if (模式 === 'r2v' && !this.表单.输入图1) {
        this.$message.warning('参考主体生视频请先上传至少 1 张参考图')
        return
      }
      if (模式 === 'i2v' && !this.表单.输入图1) {
        this.$message.warning('图生视频请先上传 1 张首帧图')
        return
      }
      if (模式 === 'fl2v' && !this.表单.输入图1) {
        this.$message.warning('首尾帧生视频请先上传首帧')
        return
      }
      if (this.需要源视频 && !this.表单.输入视频1) {
        this.$message.warning(this.模式中文 + '请先上传源视频（输入视频1）')
        return
      }
      if (模式 === 't2v' && !有提示词) {
        this.$message.warning('文生视频请输入正向提示词')
        return
      }
      if (this.需要源视频 && !有提示词) {
        this.$message.warning(this.模式中文 + '要写清「改成什么样」，请输入正向提示词')
        return
      }
      this.提交中 = true
      try {
        const 参数 = Object.assign({ 类型: '导演台全能' }, this.表单)
        for (let i = 1; i <= 9; i++) {
          if (!参数['输入图' + i]) delete 参数['输入图' + i]
        }
        for (let i = 1; i <= 3; i++) {
          if (!参数['输入视频' + i]) delete 参数['输入视频' + i]
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
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('导演台全能'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
