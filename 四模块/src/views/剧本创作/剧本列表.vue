<template>
  <div>
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">剧本创作</h1>
        <div class="副题">剧本超长续航不断连，支持 100 万字超长制作</div>
      </div>
      <div class="右">
        <el-button @click="提示('已打开导入面板，支持粘贴或上传分集剧本')">导入剧本</el-button>
        <el-button @click="提示('已导出当前剧本为 TXT 分集格式')">导出剧本</el-button>
        <el-button type="primary" @click="$router.push('/script/new')">新建剧本</el-button>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="卡片" style="margin-bottom:16px">
      <div class="行间">
        <el-input
          v-model="关键词"
          placeholder="搜索剧名或题材"
          prefix-icon="el-icon-search"
          style="width:260px">
        </el-input>
        <div class="行间" style="flex-wrap:wrap">
          <div
            v-for="项 in 状态选项"
            :key="项"
            class="chip"
            :class="{ 选中: 当前状态 === 项 }"
            @click="当前状态 = 项">{{ 项 }}</div>
        </div>
        <div style="flex:1"></div>
        <el-select v-model="排序" style="width:150px">
          <el-option label="最近更新" value="最近更新"></el-option>
          <el-option label="进度优先" value="进度优先"></el-option>
          <el-option label="集数最多" value="集数最多"></el-option>
        </el-select>
      </div>
    </div>

    <!-- 剧本卡片网格 -->
    <div class="网格 三">
      <div
        v-for="剧 in 展示列表"
        :key="剧.id"
        class="卡片 剧卡"
        @click="打开剧本(剧)">
        <div class="占位图" :style="{ height:'130px', background: 剧.封面色 }">原图：{{ 剧.名 }} 封面</div>
        <div class="行间" style="margin-top:12px">
          <div style="font-size:16px;font-weight:600">{{ 剧.名 }}</div>
          <div style="flex:1"></div>
          <span class="小标签" :class="状态类(剧.状态)">{{ 剧.状态 }}</span>
        </div>
        <div style="margin-top:8px;font-size:12px;color:var(--字弱)">
          <el-tag size="mini">{{ 剧.题材 }}</el-tag>
          <span style="margin-left:8px">{{ 剧.集数 }} 集</span>
        </div>
        <div style="margin-top:12px">
          <el-progress :percentage="剧.进度" :stroke-width="6" :show-text="false"></el-progress>
        </div>
        <div class="行间" style="margin-top:8px;font-size:12px;color:var(--字弱)">
          <span>完成度 {{ 剧.进度 }}%</span>
          <div style="flex:1"></div>
          <span>更新 {{ 剧.更新 }}</span>
        </div>
        <div class="行间" style="margin-top:12px">
          <el-button type="primary" size="mini" @click.stop="打开剧本(剧)">继续创作</el-button>
          <el-button size="mini" @click.stop="提示('已同步至梦想剧场')">同步</el-button>
        </div>
      </div>
    </div>

    <div v-if="展示列表.length === 0" class="空态">
      <div class="大">没有符合条件的剧本</div>
      <div>换个关键词，或点右上角「新建剧本」重新开始</div>
    </div>

    <div style="margin-top:16px;font-size:12px;color:var(--字弱)">
      共 {{ 展示列表.length }} 部剧本 · 内容由 AI 生成，请仔细核对剧情信息
    </div>
  </div>
</template>

<script>
import { 剧本列表 } from '../../假数据'

export default {
  name: 'ScriptList',
  data() {
    return {
      全部: 剧本列表,
      关键词: '',
      当前状态: '全部',
      状态选项: ['全部', '创作中', '已完成', '草稿'],
      排序: '最近更新'
    }
  },
  computed: {
    展示列表() {
      const 词 = this.关键词.trim()
      let 结果 = this.全部.filter(function (剧) {
        const 匹配状态 = this.当前状态 === '全部' || 剧.状态 === this.当前状态
        const 匹配词 = !词 || 剧.名.indexOf(词) >= 0 || 剧.题材.indexOf(词) >= 0
        return 匹配状态 && 匹配词
      }, this)
      if (this.排序 === '进度优先') {
        结果 = 结果.slice().sort(function (a, b) { return b.进度 - a.进度 })
      } else if (this.排序 === '集数最多') {
        结果 = 结果.slice().sort(function (a, b) { return b.集数 - a.集数 })
      } else {
        结果 = 结果.slice().sort(function (a, b) { return a.更新 < b.更新 ? 1 : -1 })
      }
      return 结果
    }
  },
  methods: {
    状态类(状态) {
      if (状态 === '已完成') return '灰'
      if (状态 === '草稿') return '灰'
      return ''
    },
    打开剧本(剧) {
      this.$router.push({ path: '/script/plan', query: { 剧名: 剧.名, 集数: 剧.集数, 题材: 剧.题材 } })
    },
    提示(文本) {
      this.$message({ message: 文本, type: 'success', duration: 1500 })
    }
  }
}
</script>

<style scoped>
.剧卡 { cursor: pointer; transition: border-color .15s, transform .15s; }
.剧卡:hover { border-color: var(--主); transform: translateY(-2px); }
</style>
