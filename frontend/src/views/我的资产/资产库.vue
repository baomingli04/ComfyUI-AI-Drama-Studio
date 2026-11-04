<template>
  <div class="创作模块">
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">资产库</h1>
        <div class="副题">全部剧集的人物、场景、道具、服装资产汇总（跨剧）</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-refresh" :loading="载入中" @click="载入()">刷新</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="卡片" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div class="行间" style="flex-wrap:wrap">
          <span style="font-size:13px;color:var(--字弱);margin-right:4px">类型</span>
          <span v-for="类 in 类型组" :key="'类型-' + 类" class="chip" :class="{ 选中: 类型 === 类 }" @click="类型 = 类">{{ 类 }}</span>
          <span style="width:16px"></span>
          <span style="font-size:13px;color:var(--字弱);margin-right:4px">剧集</span>
          <span v-for="剧 in 剧组" :key="'剧-' + 剧" class="chip" :class="{ 选中: 剧名 === 剧 }" @click="剧名 = 剧">{{ 剧 }}</span>
        </div>
        <div class="行间">
          <el-input v-model="关键词" placeholder="搜索资产名 / 资产id" prefix-icon="el-icon-search" size="small" style="width:220px" clearable />
          <span style="font-size:13px;color:var(--字弱)">共 {{ 过滤后.length }} 项</span>
        </div>
      </div>
    </div>

    <!-- 网格 -->
    <div v-if="过滤后.length" class="网格 四">
      <div v-for="资 in 过滤后" :key="资.id" class="卡片" style="padding:12px">
        <div style="position:relative">
          <img
            v-if="首图(资)"
            :src="媒体地址(首图(资).url)"
            :alt="首图(资).标注 || 资.名称"
            style="width:100%;height:150px;object-fit:cover;border-radius:8px;display:block;background:#0f172a;cursor:zoom-in"
            @click="预览图 = 资" />
          <div v-else class="占位图" :style="{ height:'150px' }">
            <span>{{ 资.类型 }} · 未出图</span>
          </div>
          <span style="position:absolute;top:8px;left:8px" class="小标签 灰">{{ 资.类型 }}</span>
          <el-tag
            size="mini"
            :type="资.生图状态 === '已生成' ? 'success' : 'info'"
            effect="plain"
            style="position:absolute;top:8px;right:8px">{{ 资.生图状态 }}</el-tag>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px">
          <span style="font-size:14px;color:var(--字);font-weight:500">{{ 资.名称 }}</span>
          <code style="font-size:11px;color:var(--字弱)">{{ 资.资产id }}</code>
        </div>
        <div style="font-size:12px;color:var(--字弱);margin-top:4px">
          {{ 资.剧名 }} · {{ 资.集号 > 0 ? '第 ' + 资.集号 + ' 集' : '全剧通用' }}<span v-if="资.级别"> · {{ 资.级别 }}</span>
          <span v-if="资.图们.length"> · {{ 资.图们.length }} 图</span>
        </div>
        <div v-if="资.摘要" style="font-size:12px;color:var(--字弱);margin-top:2px;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical">{{ 资.摘要 }}</div>
        <div class="行间" style="margin-top:10px">
          <el-button size="mini" plain style="flex:1" @click="去美术(资)">美术设定</el-button>
        </div>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else class="卡片">
      <div class="空态">
        <div class="大">还没有任何资产</div>
        <div>资产从各集剧本里提取。先去 剧集详情-资产清单 页生成本集资产，再回到这里查看全部。</div>
        <el-button type="primary" style="margin-top:16px" @click="$router.push('/video')">前往项目</el-button>
      </div>
    </div>

    <!-- 大图预览 -->
    <el-dialog :visible.sync="预览开" title="资产参考图" width="560px" append-to-body>
      <template v-if="预览图">
        <div style="font-size:14px;color:var(--字);margin-bottom:8px">{{ 预览图.名称 }} <code style="font-size:11px;color:var(--字弱)">{{ 预览图.资产id }}</code></div>
        <div style="display:flex;flex-direction:column;gap:10px;max-height:60vh;overflow:auto">
          <div v-for="(图, 序) in 预览图.图们" :key="序">
            <img :src="媒体地址(图.url)" style="width:100%;border-radius:8px;display:block;background:#0f172a" />
            <div v-if="图.标注" style="font-size:12px;color:var(--字弱);margin-top:2px">{{ 图.标注 }}</div>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { 取 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'

export default {
  name: 'AssetLib',
  data() {
    return {
      载入中: false,
      报错: '',
      全部: [],
      类型: '全部',
      剧名: '全部',
      关键词: '',
      预览图: null,
      预览开: false
    }
  },
  computed: {
    类型组() {
      return ['全部', '人物', '场景', '道具', '服装']
    },
    剧组() {
      const 名们 = Array.from(new Set(this.全部.map(x => x.剧名).filter(Boolean)))
      return ['全部'].concat(名们)
    },
    过滤后() {
      const 词 = this.关键词.trim()
      return this.全部.filter(x =>
        (this.类型 === '全部' || x.类型 === this.类型) &&
        (this.剧名 === '全部' || x.剧名 === this.剧名) &&
        (!词 || x.名称.indexOf(词) >= 0 || x.资产id.indexOf(词) >= 0)
      )
    }
  },
  mounted() {
    this.载入()
  },
  methods: {
    媒体地址,
    首图(资) {
      return (资.图们 && 资.图们.length) ? 资.图们[0] : null
    },
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.报错 = ''
      try {
        const 数据 = await 取('/api/资产/全部')
        页.全部 = (数据 && 数据.资产们) || []
      } catch (e) {
        页.报错 = '资产读取失败：' + ((e && e.message) || e)
        页.$message.error(页.报错)
      }
      页.载入中 = false
    },
    去美术(资) {
      this.$router.push({
        path: '/video/art',
        query: { ep: 资.剧id, name: 资.剧名, 集: 资.集号 }
      })
    }
  }
}
</script>
