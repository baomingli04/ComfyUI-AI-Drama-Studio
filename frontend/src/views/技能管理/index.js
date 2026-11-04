import { 取, 发 } from '@/接口/请求'
import 新增分类弹窗 from './新增分类弹窗/index.vue'
import 确认分类弹窗 from './确认分类弹窗/index.vue'
import 编辑技能弹窗 from './编辑技能弹窗/index.vue'

export default {
  name: '技能管理页',
  components: {
    'add-category-dialog': 新增分类弹窗,
    'upload-skill-dialog': 确认分类弹窗,
    'edit-skill-dialog': 编辑技能弹窗
  },
  data() {
    return {
      分类列表: [],
      技能列表: [],
      当前分类id: null,
      新增弹窗显示: false,
      上传弹窗显示: false,
      编辑弹窗显示: false,
      当前技能: null
    }
  },
  created() {
    this.拉分类()
    this.拉技能()
  },
  methods: {
    async 拉分类() {
      try {
        const 数据 = await 取('/api/技能分类')
        this.分类列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    },
    async 拉技能() {
      try {
        let 地址 = '/api/技能'
        if (this.当前分类id) {
          地址 += '?分类id=' + this.当前分类id
        }
        const 数据 = await 取(地址)
        this.技能列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    },
    选分类(分类) {
      this.当前分类id = 分类.id
      this.拉技能()
    },
    async 删分类(分类) {
      try {
        await this.$confirm('删除分类「' + 分类.名称 + '」？', '提示', { type: 'warning' })
      } catch (e) {
        return
      }
      try {
        await 发('/api/技能分类/删除', { id: 分类.id })
        this.$message.success('已删除')
        if (this.当前分类id === 分类.id) {
          this.当前分类id = null
        }
        this.拉分类()
      } catch (e) {
        this.报错(e)
      }
    },
    打开新增分类() {
      this.新增弹窗显示 = true
    },
    已新增分类() {
      this.新增弹窗显示 = false
      this.拉分类()
    },
    打开编辑技能(行) {
      this.当前技能 = 行
      this.编辑弹窗显示 = true
    },
    已保存技能() {
      this.编辑弹窗显示 = false
      this.当前技能 = null
      this.拉技能()
    },
    打开上传弹窗() {
      this.上传弹窗显示 = true
    },
    已上传技能() {
      this.上传弹窗显示 = false
      this.拉技能()
    },
    async 删技能(行) {
      try {
        await this.$confirm('删除技能「' + 行.名称 + '」会连目录一起删除，确定？', '提示', { type: 'warning' })
      } catch (e) {
        return
      }
      try {
        await 发('/api/技能/删除', { id: 行.id })
        this.$message.success('已删除')
        this.拉技能()
      } catch (e) {
        this.报错(e)
      }
    },
    报错(e) {
      this.$message.error(e.message)
      if (e.状态码 === 401) {
        this.$router.push('/login')
      }
    }
  }
}
