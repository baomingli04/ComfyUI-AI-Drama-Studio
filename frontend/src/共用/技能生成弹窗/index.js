import { 读引导, 存配置, 读技能id, 适配技能id } from '@/共用/技能生成配置'

// 技能生成弹窗：三段式（技能 / 技能引导提示词 / 保存）。
// 弹窗自己负责「读本页已存配置 + 保存」，页面只关心 显示 / 技能id / 引导 三个值。
export default {
  name: '技能生成弹窗',
  props: {
    显示: { type: Boolean, default: false },
    技能列表: { type: Array, default: () => [] },
    技能id: { type: [Number, String], default: '' },
    引导: { type: String, default: '' },
    // 本页默认引导（库里没存过时用它兜底），由页面传
    默认引导: { type: String, default: '' },
    // 后端存本页配置的 key，形如 生成:/script/new
    配置类型: { type: String, default: '' },
    // 生成的东西叫什么，只用于文案（梗概 / 人物设定 / 分集大纲…）
    目标名: { type: String, default: '本页内容' },
    // 引入数据：这次生成要带上的上下文，形如 [{键, 名, 值, 勾选, 可编辑, 提示}]
    // 传空数组就不显示第 3 段（新建剧本 / 创作方案页没有这一步，行为不变）
    引入数据: { type: Array, default: () => [] }
  },
  data() {
    return {
      本地技能id: '',
      本地引导: '',
      本地引入: [],
      载入中: false,
      保存中: false
    }
  },
  computed: {
    当前技能() {
      const id = String(this.本地技能id)
      for (let i = 0; i < this.技能列表.length; i++) {
        if (String(this.技能列表[i].id) === id) return this.技能列表[i]
      }
      return null
    }
  },
  watch: {
    // 打开时重新载入一次：用户可能在别的地方改过配置
    显示(新值) {
      if (新值) this.载入()
    },
    // 技能列表晚于弹窗打开才拉回来时，补一个默认选中（选最适配本页的）
    技能列表() {
      if (!this.本地技能id && this.技能列表.length) {
        this.本地技能id = 适配技能id(this.技能列表, this.配置类型)
      }
    }
  },
  methods: {
    async 载入() {
      this.载入中 = true
      // 先用页面给的默认值兜底，再让库里存的覆盖
      this.本地引导 = this.引导 || this.默认引导 || ''
      this.本地技能id = this.技能id || 读技能id(this.配置类型) ||
        适配技能id(this.技能列表, this.配置类型)
      // 引入数据：拷一份，勾选/编辑都不影响页面上的原值，点保存才回写
      this.本地引入 = (this.引入数据 || []).map(function (项) {
        return Object.assign({}, 项, { 勾选: 项.勾选 !== false })
      })
      // 引导提示词按「页面:技能id」各存一份，按当前选中技能读
      const 已存 = await 读引导(this.配置类型, this.本地技能id)
      if (已存) this.本地引导 = 已存
      this.载入中 = false
    },
    // 切换技能：引导提示词跟着换技能——读过存的就用存的，没存过回到本页默认
    async 技能变化() {
      const 已存 = await 读引导(this.配置类型, this.本地技能id)
      this.本地引导 = 已存 || this.默认引导 || ''
    },
    全选引入(值) {
      for (let i = 0; i < this.本地引入.length; i++) {
        this.本地引入[i].勾选 = !!值
      }
    },
    恢复默认() {
      this.本地引导 = this.默认引导 || ''
      this.$message({ message: '已恢复本页默认规则，记得点保存', type: 'info' })
    },
    async 保存() {
      if (!this.本地技能id) {
        this.$message.warning('请先选择技能')
        return
      }
      this.保存中 = true
      try {
        await 存配置(this.配置类型, this.本地技能id, this.本地引导)
        this.$emit('update:技能id', this.本地技能id)
        this.$emit('update:引导', this.本地引导)
        this.$emit('update:引入数据', this.本地引入)
        this.$emit('保存', {
          技能id: this.本地技能id,
          引导: this.本地引导,
          引入: this.本地引入
        })
        this.$message.success('已保存技能与技能引导提示词')
        this.关闭()
      } catch (e) {
        this.$message.error((e && e.message) || '保存失败')
      } finally {
        this.保存中 = false
      }
    },
    关闭() {
      this.$emit('update:显示', false)
    },
    // el-dialog 自己关（ESC 等）时也要把父级状态同步回去，不然再点「技能」打不开
    可见变化(新值) {
      if (!新值) this.关闭()
    }
  }
}
