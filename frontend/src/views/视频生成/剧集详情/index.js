// 剧集详情：进入某个项目（短剧）后才显示它的分集列表（真库）。
// 首页 /video 只列项目卡片，点进来带 query { id, name }。
// 数据：/api/分集/列表（目录）+ /api/剧本/列表（字数）+ /api/资产/列表 + /api/分镜/列表（各集统计）。
import { 取 } from '@/接口/请求'
import { 算每集进度 } from '@/共用/集进度'

export default {
  name: 'DramaDetail',
  data() {
    return {
      载入中: true,
      载入报错: '',
      当前页: 1,
      每页: 10,
      /* 真库数据 */
      分集们: [],
      剧本们: [],
      资产全集: [],
      分镜全集: []
    }
  },
  computed: {
    剧id() {
      return parseInt(this.$route.query.id) || 0
    },
    剧名() {
      return this.$route.query.name || '短剧'
    },
    副题() {
      const 集数 = this.集列表.length
      const 分镜总数 = this.分镜全集.length
      if (!集数) return '还没有分集，先去剧本创作生成分集目录'
      return [集数 + ' 集', '分镜 ' + 分镜总数, '资产 ' + this.资产全集.length + ' 项'].join(' · ')
    },
    /* 每集状态与进度：剧本 40% + 资产 20% + 分镜 40%（共用 集进度.js，与关卡详情/侧栏同口径） */
    每集进度表() {
      return 算每集进度(this.分集们, this.剧本们, this.资产全集, this.分镜全集)
    },
    /* 分集列表：优先分集目录；没有目录但有剧本时用剧本的集号兜底 */
    集列表() {
      const 页 = this
      const 表 = 页.每集进度表
      let 号们 = 页.分集们.map(function (x) { return x.集号 })
      if (!号们.length) {
        号们 = 页.剧本们.map(function (x) { return x.集号 })
      }
      const 出 = 号们.map(function (号) {
        const 项 = 表[号] || { 状态: '未开始', 分镜: 0, 字数: 0, 进度: 0 }
        return {
          集: 号,
          标题: 项.标题 || ('第 ' + 号 + ' 集'),
          状态: 项.状态,
          分镜: 项.分镜,
          字数: 项.字数,
          进度: 项.进度
        }
      })
      return 出.sort(function (a, b) { return a.集 - b.集 })
    },
    /* 分页切片：换剧或总数变少时把页码拉回有效范围 */
    分页集列表() {
      const 最大页 = Math.max(1, Math.ceil(this.集列表.length / this.每页))
      if (this.当前页 > 最大页) this.当前页 = 最大页
      const 起 = (this.当前页 - 1) * this.每页
      return this.集列表.slice(起, 起 + this.每页)
    }
  },
  watch: {
    /* 换剧回到第 1 页并重拉 */
    剧id() {
      this.当前页 = 1
      this.载入()
    }
  },
  created() {
    this.载入()
  },
  methods: {
    async 载入() {
      const 页 = this
      if (!页.剧id) {
        页.载入报错 = '缺少剧 id'
        页.载入中 = false
        return
      }
      页.载入中 = true
      页.载入报错 = ''
      /* 四类数据独立拉取：单个接口失败只缺那一块统计，不拖死分集列表 */
      const 兜底 = function () { return null }
      const 结果 = await Promise.all([
        取('/api/分集/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/剧本/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/资产/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/分镜/列表?剧id=' + 页.剧id).catch(兜底)
      ])
      页.分集们 = (结果[0] && 结果[0].分集们) || []
      页.剧本们 = (结果[1] && 结果[1].剧本们) || []
      页.资产全集 = (结果[2] && 结果[2].资产们) || []
      页.分镜全集 = (结果[3] && 结果[3].分镜们) || []
      if (!结果[0] && !结果[1]) {
        页.载入报错 = '剧集数据读取失败，请重试'
      }
      页.载入中 = false
    },
    进关卡(关) {
      this.$router.push({
        path: '/video/episode',
        query: { ep: this.剧id, name: this.剧名, 集: 关.集, 标题: 关.标题 }
      })
    },
    回列表() {
      this.$router.push('/video')
    }
  }
}
