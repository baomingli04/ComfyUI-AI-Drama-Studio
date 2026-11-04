<template>
  <!-- 剧集工作台的二级侧栏：竖排 6 项，和主侧栏（壳）是两回事，只出现在 /video/* 的集内页面 -->
  <aside class="剧集侧栏">
    <div class="侧栏头">
      <div class="侧栏剧名" :title="剧名">{{ 剧名 }}</div>
      <div class="侧栏集号">第 {{ 集 }} 集</div>
      <div class="侧栏集名" :title="标题">{{ 标题 || '未命名' }}</div>
      <div class="侧栏进度">
        <div class="侧栏进度轨"><i :style="{ width: 总进度 + '%' }"></i></div>
        <span class="侧栏进度字">{{ 总进度 }}%</span>
      </div>
    </div>

    <nav class="侧栏列">
      <button
        v-for="(项, 序) in 项们"
        :key="项.键"
        type="button"
        class="侧栏项"
        :class="{ 当前: 项.键 === 当前, 完成: 序 < 当前序 }"
        @click="去(项)">
        <span class="项号">
          <i v-if="序 < 当前序" class="el-icon-check"></i>
          <template v-else>{{ 序 + 1 }}</template>
        </span>
        <span class="项文">
          <span class="项名">{{ 项.名 }}</span>
          <span class="项标">{{ 指标(项.键) }}</span>
        </span>
        <i class="项箭 el-icon-arrow-right"></i>
      </button>
    </nav>

    <div class="侧栏尾">
      <div class="侧栏切">
        <el-button size="mini" icon="el-icon-arrow-left" :disabled="集 <= 最小集" @click="切集(-1)">上一集</el-button>
        <el-button size="mini" :disabled="集 >= 最大集" @click="切集(1)">下一集<i class="el-icon-arrow-right"></i></el-button>
      </div>
      <el-button type="text" class="侧栏回" @click="回剧集()">返回剧集列表</el-button>
    </div>
  </aside>
</template>

<script>
import { 取 } from '@/接口/请求'
import { 算每集进度 } from '@/共用/集进度'

/* 六道工序：前四步与 关卡详情/剧集详情 的进度口径一致，后两步是 2026-11 新增的单镜生成与成片合成 */
const 工序们 = [
  { 键: '剧本编辑', 名: '剧本编辑', 路由: '/video/script' },
  { 键: '资产清单', 名: '资产清单', 路由: '/video/assets' },
  { 键: '美术资产', 名: '美术资产', 路由: '/video/art' },
  { 键: '拆分分镜', 名: '拆分分镜', 路由: '/video/shot' },
  { 键: '单镜生成', 名: '单镜生成', 路由: '/video/director' },
  { 键: '成片合成', 名: '成片合成', 路由: '/video/film' }
]

export default {
  name: 'EpisodeRail',
  props: {
    剧名: { type: String, default: '' },
    剧id: { type: [Number, String], default: 0 },
    集: { type: [Number, String], default: 1 },
    标题: { type: String, default: '' },
    /* 当前阶段键：剧本编辑 / 资产清单 / 美术资产 / 拆分分镜 / 单镜生成 / 成片合成；总览页留空即全不选中 */
    当前: { type: String, default: '' }
  },
  data() {
    return {
      项们: 工序们,
      /* 真库指标（当前集）：载入失败时指标显示占位，不阻塞导航 */
      字数: 0,
      资产数: 0,
      美术已通过: 0,
      美术总数: 0,
      分镜数: 0,
      分镜已生成: 0,
      分集们: [],
      本集进度: 0
    }
  },
  computed: {
    当前序() {
      return this.项们.findIndex(function (项) { return 项.键 === this.当前 }, this)
    },
    集号数() {
      return Number(this.集) || 1
    },
    最小集() {
      return this.分集们.length ? this.分集们[0].集号 : 1
    },
    最大集() {
      return this.分集们.length ? this.分集们[this.分集们.length - 1].集号 : 1
    },
    总进度() {
      return this.本集进度 || 0
    }
  },
  watch: {
    /* 切集是同路由改 query，组件不重建，跟着重拉指标 */
    集() {
      this.载入()
    },
    剧id() {
      this.载入()
    }
  },
  created() {
    this.载入()
  },
  methods: {
    async 载入() {
      const 页 = this
      const 剧id = Number(页.剧id) || 0
      if (!剧id) return
      const 集号 = 页.集号数
      const 兜底 = function () { return null }
      /* 六道工序的指标全部来自真库；单个接口失败只缺那一块小字 */
      const 结果 = await Promise.all([
        取('/api/剧本/列表?剧id=' + 剧id).catch(兜底),
        取('/api/资产/列表?剧id=' + 剧id + '&集号=' + 集号).catch(兜底),
        取('/api/美术/列表?剧id=' + 剧id + '&集号=' + 集号).catch(兜底),
        取('/api/分镜/列表?剧id=' + 剧id + '&集号=' + 集号).catch(兜底),
        取('/api/分集/列表?剧id=' + 剧id).catch(兜底)
      ])
      const 剧本数据 = 结果[0]
      const 资产数据 = 结果[1]
      const 美术数据 = 结果[2]
      const 分镜数据 = 结果[3]
      const 分集数据 = 结果[4]

      页.分集们 = ((分集数据 && 分集数据.分集们) || [])
        .map(function (行) { return { 集号: 行.集号, 标题: 行.标题 || '' } })
        .sort(function (a, b) { return a.集号 - b.集号 })

      const 剧本行 = ((剧本数据 && 剧本数据.剧本们) || []).filter(function (行) { return 行.集号 === 集号 })[0] || null
      页.字数 = 剧本行 ? (剧本行.总字数 || 0) : 0

      const 资产行们 = (资产数据 && 资产数据.资产们) || []
      页.资产数 = 资产行们.length

      const 美术行们 = (美术数据 && 美术数据.行们) || []
      页.美术总数 = 美术行们.length
      页.美术已通过 = 美术行们.filter(function (行) { return 行.生图状态 === '已生成' || 行.状态 === '已通过' }).length

      const 分镜行们 = (分镜数据 && 分镜数据.分镜们) || []
      页.分镜数 = 分镜行们.length
      页.分镜已生成 = 分镜行们.filter(function (行) { return 行.视频状态 === '已生成' }).length

      /* 总进度用全站统一口径（与 剧集详情/关卡详情 同一份 算每集进度） */
      const 表 = 算每集进度(
        null,
        剧本行 ? [剧本行] : [],
        资产行们,
        分镜行们
      )
      const 行 = 表[集号]
      页.本集进度 = 行 ? 行.进度 : 0
    },
    /* 每项下面那行小字：让侧栏本身就能看出做到哪一步了，不用点进去 */
    指标(键) {
      if (键 === '剧本编辑') {
        return this.字数 ? this.字数 + ' 字' : '待写'
      }
      if (键 === '资产清单') {
        return this.资产数 ? this.资产数 + ' 项' : '待提取'
      }
      if (键 === '美术资产') {
        return this.美术总数 ? this.美术已通过 + '/' + this.美术总数 + ' 已出图' : '待生成'
      }
      if (键 === '拆分分镜') {
        return this.分镜数 ? this.分镜数 + ' 镜头' : '未拆分'
      }
      if (键 === '单镜生成') {
        return this.分镜已生成 ? this.分镜已生成 + '/' + this.分镜数 + ' 已出片' : '待生成'
      }
      if (键 === '成片合成') {
        return this.分镜已生成 ? '可合成' : '待成片'
      }
      return ''
    },
    去(项) {
      if (!项 || 项.键 === this.当前) return
      this.$router.push({ path: 项.路由, query: this.$route.query })
    },
    切集(差) {
      const 页 = this
      const 目标号 = 页.集号数 + 差
      if (目标号 < 页.最小集) {
        页.$message.info('已是第 1 集')
        return
      }
      if (目标号 > 页.最大集) {
        页.$message.info('已是最后一集')
        return
      }
      const 目标 = 页.分集们.filter(function (行) { return 行.集号 === 目标号 })[0]
      页.$router.push({
        path: 页.$route.path,
        query: Object.assign({}, 页.$route.query, { 集: 目标号, 标题: 目标 ? 目标.标题 : '' })
      })
    },
    回剧集() {
      this.$router.push({ path: '/video/drama', query: { id: this.剧id, name: this.剧名 } })
    }
  }
}
</script>

<style src="./index.css"></style>
