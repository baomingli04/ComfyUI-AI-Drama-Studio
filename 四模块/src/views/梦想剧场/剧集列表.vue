<template>
  <div>
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">梦想剧场</h1>
        <div class="副题">智能资产生成，把技能变为流程</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-delete">回收站</el-button>
        <el-button size="small" icon="el-icon-view">展示视频</el-button>
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
            <el-option label="最新创建" value="最新创建" />
            <el-option label="进度优先" value="进度优先" />
            <el-option label="观看最多" value="观看最多" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 剧集卡片列表 -->
    <div v-if="过滤后.length" style="display:flex;flex-direction:column;gap:16px">
      <div
        v-for="剧 in 过滤后"
        :key="剧.id"
        class="卡片"
        style="padding:16px;cursor:pointer;transition:border-color .15s"
        @mouseenter="悬停 = 剧.id"
        @mouseleave="悬停 = 0"
        :style="{ borderColor: 悬停 === 剧.id ? 'var(--描边亮)' : 'var(--描边)' }"
      >
        <div style="display:flex;gap:16px">
          <!-- 封面 -->
          <div style="position:relative;width:192px;height:112px;flex:0 0 192px">
            <div class="占位图" :style="{ width:'192px', height:'112px', background:'linear-gradient(135deg,' + 剧.封面 + ',#0f172a)' }">
              <span>原图：短剧封面</span>
            </div>
            <div style="position:absolute;right:8px;bottom:8px;background:rgba(0,0,0,.6);padding:2px 8px;border-radius:4px;font-size:12px;color:#fff">
              {{ 剧.集数 }}集
            </div>
          </div>

          <!-- 信息 -->
          <div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:4px 0">
            <div>
              <div style="font-size:18px;font-weight:700;margin-bottom:8px">{{ 剧.名 }}</div>
              <div class="行间" style="margin-bottom:10px">
                <span class="行间" style="font-size:13px;color:var(--字次)">
                  <i class="el-icon-view" style="margin-right:4px"></i>{{ 剧.观看 }}
                </span>
                <span class="小标签" v-if="剧.已解锁">
                  <i class="el-icon-check" style="margin-right:4px"></i>已拥有每日设计费
                </span>
                <span class="小标签 灰" v-else>未解锁</span>
              </div>
              <div style="font-size:12px;color:var(--字弱);margin-bottom:4px">分镜数 {{ 剧.分镜 }}</div>
              <div style="font-size:12px;color:var(--字弱)">{{ 剧.日期 }}</div>
            </div>

            <div style="display:flex;align-items:center;justify-content:space-between">
              <div class="行间">
                <span style="font-size:12px;color:var(--字弱)">新集进度</span>
                <div style="width:128px;height:4px;background:var(--描边);border-radius:999px;overflow:hidden">
                  <div :style="{ width: 剧.进度 + '%', height:'100%', background:'var(--主)', borderRadius:'999px' }"></div>
                </div>
                <span style="font-size:12px;color:var(--字弱)">{{ 剧.进度 }}%</span>
              </div>
              <div class="行间">
                <span class="小标签 灰">{{ 剧.阶段 }}</span>
                <el-button type="primary" size="small" @click.stop="进入(剧)">
                  进入项目 <i class="el-icon-arrow-right"></i>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else class="卡片">
      <div class="空态">
        <div class="大">没有匹配的短剧</div>
        <div>换个关键词，或点右上角「新建短剧」从零开始。</div>
      </div>
    </div>
  </div>
</template>

<script>
import { 剧集列表 } from '../../假数据'

export default {
  name: 'DramaList',
  data() {
    return {
      列表: 剧集列表,
      关键词: '',
      排序: '最新创建',
      悬停: 0
    }
  },
  computed: {
    过滤后() {
      const 词 = this.关键词.trim()
      let 结果 = this.列表.filter(x => !词 || x.名.indexOf(词) >= 0)
      if (this.排序 === '进度优先') 结果 = 结果.slice().sort((a, b) => b.进度 - a.进度)
      if (this.排序 === '观看最多') 结果 = 结果.slice().sort((a, b) => b.观看 - a.观看)
      return 结果
    }
  },
  methods: {
    进入(剧) {
      this.$router.push({ path: '/theater/script', query: { ep: 剧.id, name: 剧.名 } })
    },
    新建() {
      this.$message.success('纯前端演示：新建短剧流程未接入后端')
    }
  }
}
</script>
