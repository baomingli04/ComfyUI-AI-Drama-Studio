import { 取, 发 } from '@/接口/请求'

// 库里没存本页规则时用的默认规则（用户可在「扩写提示词配置」里改，改完按页面路由存库）
export const 默认扩写规则 = [
  '1. 禁止描写人物形象、服装、发型、配色、年龄等外观特征；人物外观一律以用户上传的参考图（<Picture N>）为准。',
  '2. 角色只允许描述表情、动作、姿势、位置关系、运动轨迹。',
  '3. 场景、环境、光影、镜头运动可正常描述。',
  '4. 不得添加用户未要求的角色、情节或元素。',
  '5. 只输出提示词正文，不要解释、前缀或后缀。'
].join('\n')

export default {
  name: '扩写行',
  props: {
    技能列表: { type: Array, default: () => [] },
    技能id: { type: [Number, String], default: '' },
    需求: { type: String, default: '' },
    载入中: { type: Boolean, default: false },
    // 页面可传自己的默认规则（剧本创作页按页面类型传）；不传时沿用全局默认规则，行为不变
    默认规则: { type: String, default: '' },
    // 文案整体替换：剧本创作页把这套“扩写/提示词”话术换成“生成本页内容”；
    // 不传时每一项都回退到原话术，9 个测试页观感零变化
    文案: { type: Object, default: () => ({}) },
    // 配置类型（= 后端按页存规则的那一行 key）。默认 '扩写:'+当前路由，保持原样；
    // 剧本创作页传 '生成:'+路由，跟“生成本页内容”的话术对齐（库里本就无这些行，无冲突）
    配置类型: { type: String, default: '' },
    // 引入数据清单（字符串数组，如 '图1 = 人物图 · 李宝明【便装】'）：
    // 传了就在配置弹窗里展示只读「引入数据」区块（与其他页技能生成弹窗的做法一致）；
    // 不传（测试页等）则不显示，观感零变化
    引入数据们: { type: Array, default: () => [] }
  },
  data() {
    return {
      配置展开: false,
      保存中: false,
      配置文本: '',
      配置键: '',
      扩写规则: ''
    }
  },
  computed: {
    本地技能id: {
      get() { return this.技能id },
      set(v) { this.$emit('update:技能id', v) }
    },
    本地需求: {
      get() { return this.需求 },
      set(v) { this.$emit('update:需求', v) }
    },
    // 类型 = 扩写:<当前页面路由>，一页一行，见 docs/02 第 8 节；页面可用 配置类型 prop 覆盖
    本地配置类型() {
      if (this.配置类型) return this.配置类型
      const 路径 = (this.$route && this.$route.path) || ''
      return '扩写:' + 路径
    },
    // ---- 文案（不传就用原话术）----
    标题() { return this.文案.标题 || 'AI扩写' },
    技能提示() { return this.文案.技能提示 || '提示词技能' },
    需求提示() { return this.文案.需求提示 || '写需求：想要什么画面/效果，简短描述即可' },
    按钮文字() { return this.文案.按钮文字 || '生成提示词' },
    配置文字() { return this.文案.配置文字 || '扩写提示词配置' },
    配置说明() {
      return this.文案.配置说明 || '这些规则会原样附加到本页扩写的系统提示词里，优先级最高。可自由增删改。'
    },
    保存配置提示() { return this.文案.保存配置提示 || '已保存本页扩写规则' }
  },
  created() {
    this.重新载入配置()
  },
  watch: {
    // 同一页可能按状态切不同的规则行（导演台全能按 t2v/fl2v/r2v 切三套），
    // 配置类型或默认规则一变就重新载入；否则会一直用进页面时那一套，扩写出错模式。
    本地配置类型() {
      this.重新载入配置()
    },
    默认规则() {
      this.重新载入配置()
    }
  },
  methods: {
    生成() {
      this.$emit('生成', this.扩写规则)
    },
    // 先用默认规则兜底，再拉库里的配置覆盖（拉不到就保留默认，不阻塞）
    重新载入配置() {
      this.配置展开 = false
      this.配置文本 = ''
      this.配置键 = ''
      this.扩写规则 = this.默认规则 || 默认扩写规则
      this.拉配置()
    },
    async 拉配置() {
      const 类型 = this.本地配置类型
      try {
        const 数据 = await 取('/api/提示词/配置?类型=' + encodeURIComponent(类型))
        // 请求期间又切了模式：丢弃过期结果，别把上一模式的规则写到当前模式上
        if (this.本地配置类型 !== 类型) return
        if (数据 && 数据.内容) this.扩写规则 = 数据.内容
      } catch (e) {
        /* 拉不到就用默认规则，不阻塞页面 */
      }
    },
    // 打开配置弹窗：记下打开时的键——万一保存前切了模式，也不会写错行
    打开配置() {
      this.配置键 = this.本地配置类型
      this.配置文本 = this.扩写规则
      this.配置展开 = true
    },
    async 保存配置() {
      const 键 = this.配置键 || this.本地配置类型
      this.保存中 = true
      try {
        await 发('/api/提示词/配置/保存', { 类型: 键, 内容: this.配置文本 })
        if (键 === this.本地配置类型) this.扩写规则 = this.配置文本
        this.配置展开 = false
        this.$message.success(this.保存配置提示)
      } catch (e) {
        this.$message.error(e.message)
      } finally {
        this.保存中 = false
      }
    }
  }
}
