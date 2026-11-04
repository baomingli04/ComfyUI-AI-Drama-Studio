<template>
  <div class="创作模块">
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">视频生成</h1>
        <div class="副题">剧本创作里已生成分集剧本的项目，在这里接着做出片</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-view" title="打开列表第一个短剧的成片页" @click="展示视频()">展示视频</el-button>
        <el-button size="small" type="primary" icon="el-icon-plus" @click="新建()">新建短剧</el-button>
      </div>
    </div>

    <!-- 搜索与筛选 -->
    <div class="卡片" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <el-input
          v-model="关键词"
          placeholder="搜索短剧"
          prefix-icon="el-icon-search"
          style="width:320px"
          clearable
        />
        <div class="行间">
          <span style="font-size:13px;color:var(--字弱)">共 {{ 过滤后.length }} 部短剧</span>
          <el-select v-model="排序" style="width:130px" size="small">
            <el-option label="最新更新" value="最新更新" />
            <el-option label="剧本进度优先" value="剧本进度优先" />
            <el-option label="复核最多" value="复核最多" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 首页只列项目卡片；第几集在点进项目之后才出现 -->
    <div v-if="过滤后.length" style="display:flex;flex-direction:column;gap:20px">
      <div v-for="剧 in 过滤后" :key="剧.id">
        <!-- 剧卡 -->
        <div
          class="卡片 剧卡"
          @click="进剧集(剧)"
          :style="{ borderColor: 悬停 === 剧.id ? 'var(--描边亮)' : 'var(--描边)' }"
          @mouseenter="悬停 = 剧.id"
          @mouseleave="悬停 = 0"
        >
          <div style="display:flex;gap:16px;align-items:center">
            <div style="position:relative;width:160px;height:90px;flex:0 0 160px">
              <div class="占位图" :style="{ width:'160px', height:'90px', background:'linear-gradient(135deg,' + 剧.封面 + ',#0f172a)' }">
                <span>原图：短剧封面</span>
              </div>
              <div style="position:absolute;right:8px;bottom:8px;background:rgba(0,0,0,.6);padding:2px 8px;border-radius:4px;font-size:12px;color:#fff">
                {{ 剧.集数 }} 集
              </div>
            </div>
            <div style="flex:1;min-width:0">
              <div style="font-size:18px;font-weight:700;margin-bottom:6px">{{ 剧.名 }}</div>
              <div class="行间" style="font-size:12px;color:var(--字弱)">
                <span>剧本 {{ 剧.已生成 }}/{{ 剧.集数 }} 集</span>
                <span class="小标签 灰">{{ 剧.阶段 }}</span>
                <span>已复核 {{ 剧.已复核 }} 集</span>
                <span>{{ 剧.题材 }}</span>
                <span>{{ 剧.日期 }}</span>
              </div>
            </div>
            <div class="行间" style="margin-right:4px">
              <span style="font-size:12px;color:var(--字弱)">视频进度</span>
              <div style="width:120px;height:4px;background:var(--描边);border-radius:999px;overflow:hidden">
                <div :style="{ width: 剧.进度 + '%', height:'100%', background:'var(--主)', borderRadius:'999px' }"></div>
              </div>
              <span style="font-size:12px;color:var(--字弱)">{{ 剧.进度 }}%</span>
            </div>
            <div class="行间" style="gap:8px" @click.stop>
              <el-button size="small" type="primary" @click.stop="进剧集(剧)">进入<i class="el-icon-arrow-right"></i></el-button>
              <el-button size="small" icon="el-icon-delete" @click.stop="删除剧(剧)">删除</el-button>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 空态 -->
    <div v-else class="卡片">
      <div class="空态">
        <div class="大">{{ 载入中 ? '正在读取项目…' : '还没有可出片的短剧' }}</div>
        <div>只有剧本创作里生成过分集剧本的项目才会出现在这里；先去 /script/episode 生成剧本。</div>
      </div>
    </div>
  </div>
</template>

<script>
import { 取, 发 } from '@/接口/请求'

// 封面占位渐变色：按剧 id 轮换，视觉上区分项目
const 封面色板 = ['#7c3aed', '#0ea5e9', '#f59e0b', '#10b981', '#ef4444', '#6366f1']

export default {
  name: 'DramaList',
  data() {
    return {
      /* 真库数据：/api/视频/剧列表 = 剧本创作里已生成分集剧本的剧 */
      列表: [],
      载入中: true,
      关键词: '',
      排序: '最新更新',
      悬停: 0
    }
  },
  computed: {
    /* 首页只列项目；分集在点进项目之后才出现 */
    过滤后() {
      const 词 = (this.关键词 || '').trim()
      let 结果 = this.列表.filter(x => !词 || x.名.indexOf(词) >= 0 || x.题材.indexOf(词) >= 0)
      if (this.排序 === '剧本进度优先') {
        结果 = 结果.slice().sort((a, b) => b.已生成 / b.集数 - a.已生成 / a.集数)
      }
      if (this.排序 === '复核最多') 结果 = 结果.slice().sort((a, b) => b.已复核 - a.已复核)
      return 结果
    }
  },
  created() {
    this.载入()
  },
  methods: {
    async 载入() {
      this.载入中 = true
      try {
        const 数据 = await 取('/api/视频/剧列表')
        const 列表 = (数据 && 数据.列表) || []
        this.列表 = 列表.map((行, 序) => ({
          id: 行.id,
          名: 行.剧名,
          集数: 行.集数,
          题材: 行.题材 || '',
          已生成: 行.已生成集数 || 0,
          已复核: 行.已复核集数 || 0,
          阶段: (行.已生成集数 || 0) >= 行.集数 ? '剧本齐全' : '剧本创作中',
          进度: 行.视频进度 || 0,
          日期: (行.更新时间 || 行.创建时间 || '').replace(' ', ' · '),
          封面: 封面色板[行.id % 封面色板.length]
        }))
      } catch (e) {
        this.$message.error('拉取短剧列表失败：' + ((e && e.message) || e))
      } finally {
        this.载入中 = false
      }
    },
    /* 点项目 → 项目内页，那里才显示第 1 集、第 2 集… */
    进剧集(剧) {
      this.$router.push({ path: '/video/drama', query: { id: 剧.id, name: 剧.名 } })
    },
    删除剧(剧) {
      const 页 = this
      页.$confirm(
        '确定删除短剧「' + 剧.名 + '」？将连同它的方案、分集剧本等全部数据级联删除，不可恢复。',
        '删除短剧', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async function () {
        try {
          await 发('/api/剧/删除', { id: 剧.id })
          const 序 = 页.列表.indexOf(剧)
          if (序 >= 0) 页.列表.splice(序, 1)
          页.$message.success('已删除：' + 剧.名)
        } catch (e) {
          页.$message.error('删除失败：' + ((e && e.message) || e))
        }
      }).catch(function () {})
    },
    /* 立项在剧本创作线：新建短剧去 /script/new 填剧名/集数/创意 */
    新建() {
      this.$router.push({ path: '/script/new' })
    },
    /* 打开列表第一个短剧的成片页 */
    展示视频() {
      const 行 = this.列表[0]
      if (!行) {
        this.$message.warning('还没有短剧，先新建或去剧本创作立项')
        return
      }
      this.$router.push({ path: '/video/film', query: { ep: 行.id, name: 行.名, 集: 1 } })
    }
  }
}
</script>

<style scoped>
.剧卡 {
  padding: 18px;
  cursor: pointer;
  transition: border-color .15s;
}
</style>
