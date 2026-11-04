<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        :剧名="剧名" :剧id="剧id" :集="集" :标题="标题" />

      <div class="剧集主体">
        <!-- 面包屑 -->
        <div class="面包屑条">
          <span class="可点" @click="回列表()">视频生成</span>
          <span> / </span>
          <span class="可点" @click="回剧集()">{{ 剧名 }}</span>
          <span> / </span>
          <span style="color:var(--字次)">第 {{ 集 }} 集{{ 标题 ? ' · ' + 标题 : '' }}</span>
        </div>

        <!-- 载入 / 报错门控 -->
        <div v-if="载入中" class="卡片 空态">
          <i class="el-icon-loading" style="font-size:40px;color:var(--字弱)"></i>
          <div style="margin-top:8px">正在读取本集数据…</div>
        </div>
        <div v-else-if="载入报错" class="卡片 空态">
          <i class="el-icon-warning-outline" style="font-size:40px;color:var(--警,#e6a23c)"></i>
          <div style="margin-top:8px">{{ 载入报错 }}</div>
          <el-button size="small" style="margin-top:10px" @click="载入()">重试</el-button>
        </div>

        <template v-else>
        <!-- 页头 -->
        <div class="页头" style="margin-bottom:0">
          <div class="左">
            <h1 class="标题">第 {{ 集 }} 集{{ 标题 ? ' · ' + 标题 : '' }}</h1>
            <div class="副题">{{ 剧名 }} · {{ 当前状态 }} · {{ 字数 }} 字 · {{ 分镜数 }} 分镜 · {{ 本集资产数 }} 资产</div>
          </div>
          <div class="右">
            <el-button size="small" @click="进剧本创作()">进入剧本创作</el-button>
            <el-button size="small" type="primary" @click="下一集()">
              下一集<i class="el-icon-arrow-right"></i>
            </el-button>
          </div>
        </div>

        <!-- 概览：进度环 + 四个数字 -->
        <div class="卡片 概览卡">
          <div class="概览环">
            <el-progress
              type="circle"
              :percentage="当前进度"
              :width="104"
              :stroke-width="7"
              color="#22c55e" />
            <div class="概览环字">本集进度</div>
          </div>
          <div class="概览数们">
            <div class="概览数">
              <div class="数名">剧本</div>
              <div class="数值">{{ 字数 }}<span>字</span></div>
              <div class="数注">{{ 场次们.length }} 场次{{ 剧本行 ? ' · ' + (剧本行.状态 || '') : '' }}</div>
            </div>
            <div class="概览数">
              <div class="数名">资产</div>
              <div class="数值">{{ 本集资产数 }}<span>项</span></div>
              <div class="数注">角色 / 场景 / 道具 / 服装</div>
            </div>
            <div class="概览数">
              <div class="数名">美术图</div>
              <div class="数值">{{ 本集美术数 }}<span>张</span></div>
              <div class="数注">已出图 {{ 本集美术已生成 }} / {{ 本集美术数 }}</div>
            </div>
            <div class="概览数">
              <div class="数名">分镜</div>
              <div class="数值">{{ 分镜数 }}<span>镜</span></div>
              <div class="数注">已生成视频 {{ 分镜已生成 }}</div>
            </div>
          </div>
          <div class="概览继续">
            <div class="继续名">继续上次</div>
            <div class="继续步">{{ 下一步.名 }}</div>
            <el-button size="small" type="primary" @click="进(下一步)">进入<i class="el-icon-arrow-right"></i></el-button>
          </div>
        </div>

        <!-- 本集场次 + 出场角色 -->
        <div class="两列">
          <div class="卡片">
            <div class="行间" style="justify-content:space-between;margin-bottom:12px">
              <span class="区标题" style="margin:0">本集场次</span>
              <el-button type="text" size="mini" @click="进(步表[0])">去剧本编辑</el-button>
            </div>
            <div v-if="!场次们.length" class="空注">本集还没有剧本，去剧本编辑生成</div>
            <div class="场次列">
              <div v-for="(场, 序) in 场次们" :key="序" class="场次行">
                <span class="场次号">{{ 场.场 }}</span>
                <span class="场次地">{{ 场.地点 }}</span>
                <span class="场次文">{{ (场.正文 || []).join(' ') }}</span>
              </div>
            </div>
          </div>

          <div class="卡片">
            <div class="行间" style="justify-content:space-between;margin-bottom:12px">
              <span class="区标题" style="margin:0">出场角色</span>
              <el-button type="text" size="mini" @click="进(步表[1])">去资产清单</el-button>
            </div>
            <div v-if="!角色们.length" class="空注">暂无角色资产，去资产清单提取</div>
            <div class="角色列">
              <div v-for="人 in 角色们" :key="人.资产id || 人.人物id" class="角色行">
                <div class="角色头">{{ 人.名 }} <span v-if="人.级别" class="角色级">{{ 人.级别 }}</span></div>
                <div class="角色文">{{ 人.描述 }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 本剧集切换（真库分集 + 各集真实进度） -->
        <div class="卡片">
          <div class="行间" style="justify-content:space-between;margin-bottom:12px">
            <span class="区标题" style="margin:0">本剧集</span>
            <span style="font-size:12px;color:var(--字弱)">共 {{ 本剧集.length }} 集 · 点一集切过去</span>
          </div>
          <div v-if="!本剧集.length" class="空注">这部剧还没有分集目录，去 分集目录 页生成</div>
          <div class="集网格">
            <div
              v-for="项 in 本剧集"
              :key="项.集"
              class="集格"
              :class="{ 当前: 项.集 === 集, 完: 项.进度 >= 100 }"
              @click="切到(项)">
              <div class="集格号">{{ 项.进度 >= 100 ? '✓' : 项.集 }}</div>
              <div class="集格文">
                <div class="集格名">{{ 项.标题 || ('第 ' + 项.集 + ' 集') }}</div>
                <div class="集格注">{{ 项.状态 }} · {{ 项.进度 }}%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 提示 -->
        <div class="提示条" style="margin-bottom:0">
          <span>4 项工序就是这一集的完整流程，点哪项进哪页；资产与分镜首次进入对应页面时会自动生成并落库。</span>
          <el-button type="text" size="mini" @click="回剧集()">返回剧集列表</el-button>
        </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import 剧集侧栏 from '@/共用/剧集侧栏/index.vue'
import { 取 } from '@/接口/请求'
import { 算每集进度 } from '@/共用/集进度'

/* 本集 4 道工序（与假数据口径一致，但这里静态定义，不依赖假数据模块） */
const 步表 = [
  { 键: '剧本编辑', 名: '剧本编辑', 说明: '本集正文、场次与对白', 图标: 'el-icon-document', 路由: '/video/script' },
  { 键: '资产清单', 名: '资产清单', 说明: '角色 · 场景 · 道具 · 服装', 图标: 'el-icon-folder-opened', 路由: '/video/assets' },
  { 键: '美术资产', 名: '美术资产', 说明: '逐项出参考图并审核', 图标: 'el-icon-picture-outline', 路由: '/video/art' },
  { 键: '拆分分镜', 名: '拆分分镜', 说明: '按场次拆成可生成的镜头', 图标: 'el-icon-film', 路由: '/video/shot' }
]

export default {
  name: 'DramaEpisode',
  components: { 'ep-rail': 剧集侧栏 },
  data() {
    return {
      载入中: true,
      载入报错: '',
      步表: 步表,
      /* 真库数据 */
      分集们: [],
      剧本们: [],
      资产全集: [],
      分镜全集: [],
      人物们: [],
      美术全集: []
    }
  },
  computed: {
    剧名() { return this.$route.query.name || '' },
    剧id() { return parseInt(this.$route.query.ep) || 0 },
    集() { return parseInt(this.$route.query.集) || 1 },
    标题() { return this.$route.query.标题 || '' },
    /* 真库分集行（含标题/状态） */
    本集分集() {
      const 号 = this.集
      return this.分集们.filter(function (x) { return x.集号 === 号 })[0] || null
    },
    剧本行() {
      const 号 = this.集
      return this.剧本们.filter(function (x) { return x.集号 === 号 })[0] || null
    },
    本集资产() { return this.资产全集.filter(function (x) { return x.集号 === this.集 }, this) },
    本集分镜() { return this.分镜全集.filter(function (x) { return x.集号 === this.集 }, this) },
    场次们() { return (this.剧本行 && this.剧本行.场次们) || [] },
    字数() { return (this.剧本行 && this.剧本行.总字数) || 0 },
    分镜数() { return this.本集分镜.length },
    分镜已生成() { return this.本集分镜.filter(function (x) { return x.视频状态 === '已生成' }).length },
    本集资产数() { return this.本集资产.length },
    本集美术() { return this.美术全集.filter(function (x) { return x.集号 === this.集 }, this) },
    本集美术数() { return this.本集美术.length },
    本集美术已生成() { return this.本集美术.filter(function (x) { return x.生图状态 === '已生成' }).length },
    /* 出场角色：优先本集人物资产，否则回退剧的人物设定 */
    角色们() {
      const 人物资产 = this.本集资产.filter(function (x) { return x.类型 === '人物' })
        .map(function (x) { return { 资产id: x.资产id, 名: x.名称, 级别: x.级别, 描述: x.摘要 } })
      if (人物资产.length) return 人物资产
      return this.人物们.map(function (人) {
        return { 人物id: 人.人物id, 名: 人.名, 级别: 人.身份 || '', 描述: 人.简介 || '' }
      })
    },
    /* 每集状态与进度：剧本 40% + 资产 20% + 分镜 40%（共用 集进度.js，与剧集详情/侧栏同口径） */
    每集进度表() {
      return 算每集进度(this.分集们, this.剧本们, this.资产全集, this.分镜全集)
    },
    本剧集() {
      const 页 = this
      const 表 = 页.每集进度表
      return 页.分集们.map(function (行) {
        const 项 = 表[行.集号] || { 进度: 0, 状态: '未开始' }
        return { 集: 行.集号, 标题: 行.标题 || '', 状态: 项.状态, 进度: 项.进度 }
      }).sort(function (a, b) { return a.集 - b.集 })
    },
    当前状态() { return this.本集分集 ? (this.本集分集.状态 || '未开始') : '未开始' },
    当前进度() {
      const 项 = this.每集进度表[this.集]
      return (项 && 项.进度) || 0
    },
    /* 下一步：无剧本→剧本编辑；无资产→资产清单；无美术图→美术资产；都有→回分镜继续 */
    下一步() {
      if (!this.剧本行) return this.步表[0]
      if (!this.本集资产数) return this.步表[1]
      if (!this.本集美术数) return this.步表[2]
      return this.步表[3]
    }
  },
  created() {
    this.载入()
  },
  methods: {
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.载入报错 = ''
      /* 四类数据独立拉取：单个接口失败只缺那一块统计，不拖死整页 */
      const 兜底 = function () { return null }
      const 结果 = await Promise.all([
        取('/api/分集/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/剧本/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/资产/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/分镜/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/人物/列表?剧id=' + 页.剧id).catch(兜底),
        取('/api/美术/列表?剧id=' + 页.剧id + '&集号=' + 页.集).catch(兜底)
      ])
      页.分集们 = (结果[0] && 结果[0].分集们) || []
      页.剧本们 = (结果[1] && 结果[1].剧本们) || []
      页.资产全集 = (结果[2] && 结果[2].资产们) || []
      页.分镜全集 = (结果[3] && 结果[3].分镜们) || []
      页.人物们 = (结果[4] && 结果[4].人物们) || []
      页.美术全集 = (结果[5] && 结果[5].行们) || []
      if (!结果[0] && !结果[1]) {
        页.载入报错 = '本集数据读取失败，请点重试'
      }
      页.载入中 = false
    },
    进(步) {
      if (!步) return
      this.$router.push({ path: 步.路由, query: this.$route.query })
    },
    切到(项) {
      if (项.集 === this.集) return
      this.$router.push({
        path: '/video/episode',
        query: Object.assign({}, this.$route.query, { 集: 项.集, 标题: 项.标题 || '' })
      })
      /* 切集后重取统计（进度与场次随集变化） */
      this.载入()
    },
    下一集() {
      const 号 = this.集 + 1
      const 目标 = this.本剧集.filter(function (x) { return x.集 === 号 })[0]
      if (!目标) {
        this.$message.info('已是最后一集')
        return
      }
      this.切到(目标)
    },
    回列表() { this.$router.push('/video') },
    回剧集() { this.$router.push({ path: '/video/drama', query: { id: this.剧id, name: this.剧名 } }) },
    进剧本创作() { this.$router.push({ path: '/script/episode', query: { id: this.剧id, 剧名: this.剧名 } }) }
  }
}
</script>

<style scoped>
/* 概览：进度环 + 4 个数字 + 继续按钮 */
.概览卡 {
  display: flex;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
}
.概览环 {
  flex: 0 0 auto;
  text-align: center;
}
.概览环字 {
  margin-top: 8px;
  font-size: 12px;
  color: var(--字弱);
}
.概览数们 {
  flex: 1;
  min-width: 320px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.概览数 {
  padding: 10px 14px;
  border-left: 2px solid var(--描边);
}
.概览数 .数名 {
  font-size: 12px;
  color: var(--字弱);
}
.概览数 .数值 {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 700;
  color: var(--字);
  line-height: 1.2;
}
.概览数 .数值 span {
  margin-left: 2px;
  font-size: 12px;
  font-weight: 400;
  color: var(--字弱);
}
.概览数 .数注 {
  margin-top: 2px;
  font-size: 11px;
  color: var(--字弱);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.概览继续 {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 20px;
  border-left: 1px solid var(--描边);
}
.概览继续 .继续名 {
  font-size: 11px;
  color: var(--字弱);
}
.概览继续 .继续步 {
  font-size: 14px;
  font-weight: 600;
  color: var(--主);
}

/* 两列摘要 */
.两列 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.场次列,
.角色列 {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.空注 {
  font-size: 12px;
  color: var(--字弱);
  padding: 12px 0;
}
.场次行 {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 12px;
  line-height: 1.7;
}
.场次号 {
  flex: 0 0 auto;
  color: var(--主);
  font-weight: 600;
}
.场次地 {
  flex: 0 0 auto;
  color: var(--字次);
}
.场次文 {
  flex: 1;
  min-width: 0;
  color: var(--字弱);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.角色行 {
  padding: 8px 10px;
  border: 1px solid var(--描边);
  border-radius: 8px;
  background: var(--卡片二);
}
.角色头 {
  font-size: 13px;
  color: var(--字);
}
.角色级 {
  font-size: 11px;
  color: var(--字弱);
  font-weight: 400;
  margin-left: 6px;
}
.角色文 {
  margin-top: 2px;
  font-size: 12px;
  color: var(--字弱);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 集切换网格 */
.集网格 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}
.集格 {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--描边);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.集格:hover { border-color: var(--描边亮); }
.集格.当前 { border-color: var(--主); background: var(--主浅); }
.集格号 {
  flex: 0 0 26px;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: var(--描边);
  color: var(--字次);
}
.集格.当前 .集格号 { background: var(--主); color: #06210f; font-weight: 700; }
.集格.完 .集格号 { background: var(--主浅); color: var(--主); }
.集格文 { min-width: 0; }
.集格名 {
  font-size: 13px;
  color: var(--字);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.集格注 {
  margin-top: 2px;
  font-size: 11px;
  color: var(--字弱);
}

@media (max-width: 1280px) {
  .概览数们 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 900px) {
  .两列 { grid-template-columns: 1fr; }
  .概览继续 { padding-left: 0; border-left: none; }
}
</style>
