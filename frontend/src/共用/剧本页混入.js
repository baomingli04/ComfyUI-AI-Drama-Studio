// 剧本创作页（创作方案 / 方案详情 / 分集大纲）共用混入。
// 干三件事：①四步进度条的数据与跨页跳转；②技能下拉 + AI扩写（复用现成 /api/提示词/扩写）；
//          ③生成结果暂存 + 复制 + 保存提示。
// 注意：这三个页目前展示的是假数据，保存只给前端成功提示，不写任何后端数据。
import { 取, 发 } from '@/接口/请求'
import { 复制到剪贴板 } from '@/共用/复制文本'

export default {
  data() {
    return {
      // 四步流程：创作方案 → 人物设定 → 分集目录 → 分集剧本
      // （原第 5 步「合规审查」已按需求下线，页面与路由一并删除）
      步骤: ['创作方案', '人物设定', '分集目录', '分集剧本'],
      // 四步各是一个独立页
      步骤落地: [
        { 路径: '/script/plan' },
        { 路径: '/script/character' },
        { 路径: '/script/outline' },
        { 路径: '/script/episode' }
      ],
      // 当前页属于第几步（0 起）。分集大纲页按 tab 覆盖为 computed
      当前序号: 0,
      // 技能 / 扩写（与测试页同一套接口，前端零后端改动）
      // 手册 6.1 分类隔离：剧本创作 6 页只认「剧本创作」分类，与测试台 minimax 互不可见
      扩写模式: 'image',
      扩写技能分类: '剧本创作',
      技能列表: [],
      扩写技能id: '',
      扩写需求: '',
      扩写中: false,
      生成结果: '',
      // 本组页面统一话术：这是“用技能生成本页内容”，不是“生成提示词”。
      // 由 技能区 透传给 扩写行，覆盖它的默认文案（测试页不传，仍是原话术）
      页文案: {
        标题: '技能生成本页内容',
        技能提示: '选择技能',
        需求提示: '写需求：想要什么内容，简短描述即可，回车即生成',
        按钮文字: '生成本页内容',
        配置文字: '本页生成规则',
        配置说明: '本页生成内容时这些规则优先级最高（与技能规范冲突时以它为准），可自由增删改。',
        保存配置提示: '已保存本页生成规则'
      }
    }
  },
  computed: {
    当前技能() {
      const id = String(this.扩写技能id)
      for (let i = 0; i < this.技能列表.length; i++) {
        if (String(this.技能列表[i].id) === id) return this.技能列表[i]
      }
      return null
    },
    // 本页生成规则在后端存的 key：和测试页的 扩写:<路由> 区分开，免得两边串味
    页配置类型() {
      return '生成:' + ((this.$route && this.$route.path) || '')
    }
  },
  created() {
    this.拉技能列表()
  },
  methods: {
    async 拉技能列表() {
      try {
        const 数据 = await 取('/api/提示词/技能列表?分类=' + encodeURIComponent(this.扩写技能分类))
        this.技能列表 = (数据 && 数据.列表) || []
        // 默认选「最适配」本页的技能（按页面关键词打分）；已选过就不覆盖
        if (!this.扩写技能id && this.技能列表.length) {
          this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
        }
      } catch (e) {
        /* 技能列表拉不到不阻塞页面 */
      }
    },
    // 点四步进度条跳转。同一页内的步骤切换由页面自己实现（分集大纲页是切 tab）。
    跳到步骤页(序) {
      if (序 < 0 || 序 >= this.步骤.length) return
      if (序 === this.当前序号) {
        this.$message({ message: '当前已在「' + this.步骤[序] + '」', type: 'info' })
        return
      }
      const 落 = this.步骤落地[序]
      if (!落) return
      this.$router.push({
        path: 落.路径,
        query: Object.assign({}, this.$route.query, 落.查询 || {})
      })
    },
    // 生成：调现成的提示词扩写接口，结果落到本页「生成结果」框里。
    // 剧本页没有上传参考图，所以 引用 传空数组；要什么内容由本页的 默认规则/配置 决定。
    async 扩写(附加规则) {
      if (!this.扩写技能id) {
        this.$message.warning('请先选择提示词技能')
        return
      }
      if (!this.扩写需求 || !this.扩写需求.trim()) {
        this.$message.warning('请先填写需求')
        return
      }
      this.扩写中 = true
      try {
        const 数据 = await 发('/api/提示词/扩写', {
          技能id: this.扩写技能id,
          模式: this.扩写模式,
          需求: this.扩写需求.trim(),
          引用: [],
          附加规则: 附加规则 || ''
        })
        this.生成结果 = (数据 && 数据.提示词) || ''
        this.$message.success('已生成本页内容，见下方「生成内容」')
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.扩写中 = false
      }
    },
    扩写报错(e) {
      this.$message.error((e && e.message) || '生成失败')
      if (e && e.状态码 === 401) this.$router.push('/login')
    },
    async 复制生成结果() {
      const 成功 = await 复制到剪贴板(this.生成结果)
      this.$message[成功 ? 'success' : 'error'](成功 ? '已复制到剪贴板' : '复制失败，请手动选择复制')
    },
    // 保存：这些页目前是假数据展示，保存只给提示，不动后端、不动页面数据
    保存() {
      this.$message({ message: '已保存「' + this.步骤[this.当前序号] + '」当前内容', type: 'success' })
    }
  }
}
