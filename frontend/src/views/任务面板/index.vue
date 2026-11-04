<template>
  <div class="创作模块">
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">任务面板</h1>
        <div class="副题">全部生成任务一处查看：失败/中断可一键重试，生成中的任务实时看到已生成内容</div>
      </div>
      <div class="右">
        <span style="font-size:12px;color:var(--字弱)">进行中 {{ 进行中数 }} 个</span>
        <el-button size="small" icon="el-icon-refresh" @click="载入()">刷新</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="卡片" style="margin-bottom:16px">
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
        <el-select v-model="筛选类型" size="small" style="width:180px" clearable placeholder="全部类型">
          <el-option v-for="t in 类型们" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="筛选状态" size="small" style="width:140px" clearable placeholder="全部状态">
          <el-option v-for="s in 状态们" :key="s" :label="s" :value="s" />
        </el-select>
        <el-input v-model="关键词" size="small" style="width:280px" clearable
                  prefix-icon="el-icon-search" placeholder="搜提示词 / 错误信息" />
        <span style="font-size:12px;color:var(--字弱)">共 {{ 过滤后.length }} 条</span>
        <el-button v-if="可重试数" size="small" type="warning" plain
                   @click="重试全部失败()">一键重试全部失败（{{ 可重试数 }}）</el-button>
      </div>
    </div>

    <!-- 任务表 -->
    <div class="卡片">
      <el-table :data="过滤后" size="small" border @row-click="打开详情">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="类型" label="类型" width="130" show-overflow-tooltip />
        <el-table-column label="状态" width="92">
          <template slot-scope="s"><span class="状态标" :class="'状' + s.row.状态">{{ s.row.状态 }}</span></template>
        </el-table-column>
        <el-table-column label="内容" min-width="240">
          <template slot-scope="s">{{ (s.row.正向提示词 || '').slice(0, 120) || '—' }}</template>
        </el-table-column>
        <el-table-column label="进度" width="110">
          <template slot-scope="s">
            <span v-if="s.row.状态 === '生成中' && s.row.回复">已生成 {{ s.row.回复.length }} 字</span>
            <span v-else-if="s.row.生成时长" style="color:var(--字弱)">{{ s.row.生成时长 }}s</span>
            <span v-else style="color:var(--字弱)">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="创建时间" label="创建时间" width="150" />
        <el-table-column label="错误信息" min-width="160">
          <template slot-scope="s"><span style="color:var(--危,#c0392b)">{{ (s.row.错误信息 || '').slice(0, 100) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template slot-scope="s">
            <el-button v-if="可重试(s.row)" size="mini" type="warning" @click.stop="重试(s.row)">重试</el-button>
            <el-button v-if="可取消(s.row)" size="mini" type="danger" plain @click.stop="取消(s.row)">取消</el-button>
            <el-button size="mini" @click.stop="打开详情(s.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog :visible.sync="详情显示" title="任务详情" width="720px" append-to-body>
      <template v-if="详情行">
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;font-size:13px">
          <span>#{{ 详情行.id }}</span>
          <span class="状态标" :class="'状' + 详情行.状态">{{ 详情行.状态 }}</span>
          <span style="color:var(--字弱)">{{ 详情行.类型 }}</span>
          <span style="color:var(--字弱)">{{ 详情行.创建时间 }}</span>
          <span v-if="详情行.生成时长" style="color:var(--字弱)">耗时 {{ 详情行.生成时长 }}s</span>
        </div>
        <div v-if="详情行.错误信息" class="详情块" style="border-color:var(--危,#c0392b)">
          <div class="块标">错误信息</div>
          <pre class="块文">{{ 详情行.错误信息 }}</pre>
        </div>
        <div class="详情块">
          <div class="块标">正向提示词</div>
          <pre class="块文">{{ 详情行.正向提示词 || '—' }}</pre>
        </div>
        <div v-if="详情行.系统提示词" class="详情块">
          <div class="块标">系统提示词</div>
          <pre class="块文">{{ 详情行.系统提示词 }}</pre>
        </div>
        <div v-if="详情行.回复" class="详情块">
          <div class="块标">回复{{ 详情行.状态 === '生成中' ? '（生成中，实时增长）' : '' }}</div>
          <pre class="块文">{{ 详情行.回复 }}</pre>
        </div>
        <div v-if="详情行.产物图片 || 详情行.产物图片2 || 详情行.产物视频1 || 详情行.产物视频2" class="详情块">
          <div class="块标">产物</div>
          <pre class="块文">{{ [详情行.产物图片, 详情行.产物图片2, 详情行.产物视频1, 详情行.产物视频2].filter(Boolean).join('\n') }}</pre>
        </div>
        <div v-if="输入图们.length" class="详情块">
          <div class="块标">输入图</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <img v-for="(u, i) in 输入图们" :key="i" :src="媒体地址(u)" style="width:96px;height:96px;object-fit:cover;border-radius:6px;border:1px solid var(--描边)" />
          </div>
        </div>
      </template>
      <div slot="footer">
        <el-button v-if="详情行 && 可重试(详情行)" type="warning" @click="重试(详情行); 详情显示 = false">重试此任务</el-button>
        <el-button @click="详情显示 = false">关闭</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { 取, 发 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'

const 终态们 = ['成功', '失败', '中断', '已取消']
const 可重试态 = ['失败', '中断', '已取消']
const 状态们 = ['已创建', '已提交', '排队中', '生成中', '成功', '失败', '中断', '已取消']

export default {
  name: 'TaskPanel',
  data() {
    return {
      行们: [],
      载入中: false,
      筛选类型: '',
      筛选状态: '',
      关键词: '',
      类型们: [],
      状态们: 状态们,
      定时器: null,
      详情显示: false,
      详情行: null
    }
  },
  computed: {
    过滤后() {
      const 词 = (this.关键词 || '').trim().toLowerCase()
      return this.行们.filter(r => {
        if (this.筛选类型 && r.类型 !== this.筛选类型) return false
        if (this.筛选状态 && r.状态 !== this.筛选状态) return false
        if (词) {
          const 文 = ((r.正向提示词 || '') + (r.错误信息 || '') + (r.回复 || '')).toLowerCase()
          if (文.indexOf(词) < 0) return false
        }
        return true
      })
    },
    进行中数() {
      return this.行们.filter(r => 终态们.indexOf(r.状态) < 0).length
    },
    可重试数() {
      return this.行们.filter(r => r.状态 === '失败' || r.状态 === '中断').length
    },
    输入图们() {
      if (!this.详情行) return []
      const 们 = []
      for (let i = 1; i <= 9; i++) {
        const u = this.详情行['输入图' + i]
        if (u) 们.push(u)
      }
      return 们
    }
  },
  created() {
    this.载入()
  },
  beforeDestroy() {
    this.停轮询()
  },
  methods: {
    async 载入() {
      this.载入中 = true
      try {
        const 数据 = await 取('/api/任务列表?条数=200')
        this.行们 = (数据 && 数据.列表) || []
        const 见 = {}
        this.行们.forEach(r => { 见[r.类型] = true })
        this.类型们 = Object.keys(见).sort()
        this.安排轮询()
      } catch (e) {
        this.$message.error('任务列表加载失败：' + ((e && e.message) || e))
      }
      this.载入中 = false
    },
    /* 有进行中的任务才开轮询；页面销毁必清定时器 */
    安排轮询() {
      this.停轮询()
      if (this.进行中数 > 0) {
        this.定时器 = setTimeout(() => this.载入(), 4000)
      }
    },
    停轮询() {
      if (this.定时器) {
        clearTimeout(this.定时器)
        this.定时器 = null
      }
    },
    可重试(行) {
      return 可重试态.indexOf(行.状态) >= 0
    },
    可取消(行) {
      return ['已创建', '已提交', '排队中', '生成中'].indexOf(行.状态) >= 0
    },
    async 重试(行) {
      try {
        const 数据 = await 发('/api/任务/重试', { id: 行.id })
        this.$message.success('已重新提交为任务 #' + ((数据 && 数据.新任务id) || '?') + '，参数与原任务一致')
        this.载入()
      } catch (e) {
        this.$message.error('重试失败：' + ((e && e.message) || e))
      }
    },
    重试全部失败() {
      const 们 = this.行们.filter(r => r.状态 === '失败' || r.状态 === '中断')
      const 页 = this
      this.$confirm('把 ' + 们.length + ' 个失败/中断任务全部按原参数重新提交？', '一键重试', {
        confirmButtonText: '全部重试', cancelButtonText: '取消', type: 'warning'
      }).then(async function () {
        let 好 = 0
        for (let i = 0; i < 们.length; i++) {
          try {
            await 发('/api/任务/重试', { id: 们[i].id })
            好++
          } catch (e) { /* 单个失败不中断整批 */ }
        }
        页.$message.success('已重新提交 ' + 好 + ' 个任务')
        页.载入()
      }).catch(function () {})
    },
    async 取消(行) {
      try {
        await 发('/api/任务/取消', { id: 行.id })
        this.$message.success('任务 #' + 行.id + ' 已取消')
        this.载入()
      } catch (e) {
        this.$message.error('取消失败：' + ((e && e.message) || e))
      }
    },
    打开详情(行) {
      this.详情行 = 行
      this.详情显示 = true
    }
  }
}
</script>

<style scoped>
.状态标 {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 18px;
}
.状成功 { background: rgba(46, 204, 113, .15); color: #27ae60; }
.状失败, .状中断 { background: rgba(231, 76, 60, .15); color: #c0392b; }
.状已取消 { background: rgba(127, 140, 141, .18); color: #7f8c8d; }
.状生成中, .状已提交, .状排队中, .状已创建 { background: rgba(52, 152, 219, .15); color: #2980b9; }

.详情块 {
  border: 1px solid var(--描边);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
}
.块标 { font-size: 12px; color: var(--字弱); margin-bottom: 6px; }
.块文 {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.7;
  max-height: 260px;
  overflow: auto;
}
</style>
