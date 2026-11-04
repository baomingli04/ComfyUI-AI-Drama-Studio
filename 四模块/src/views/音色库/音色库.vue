<template>
  <div>
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">音色库</h1>
        <div class="副题">浏览平台官方音色，试听效果，选择适合您角色的声音</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-upload2" @click="上传()">上传我的音色</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="卡片" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div class="行间" style="flex-wrap:wrap">
          <span v-for="类 in 分类组" :key="类" class="chip" :class="{ 选中: 分类 === 类 }" @click="分类 = 类">{{ 类 }}</span>
          <span style="width:12px"></span>
          <el-input v-model="关键词" placeholder="搜索音色..." prefix-icon="el-icon-search" size="small" style="width:200px" clearable />
        </div>
        <div class="行间">
          <span style="font-size:13px;color:var(--字弱)">排序</span>
          <el-select v-model="排序" size="small" style="width:110px">
            <el-option label="全部" value="全部" />
            <el-option label="最新" value="最新" />
            <el-option label="最热" value="最热" />
          </el-select>
        </div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 3fr;gap:24px">
      <!-- 左：音色列表 -->
      <div class="卡片" style="padding:8px;align-self:start">
        <div style="display:flex;flex-direction:column;gap:2px">
          <div
            v-for="音 in 过滤后"
            :key="音.id"
            style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:13px"
            :style="{ background: 当前.id === 音.id ? 'var(--描边)' : 'transparent' }"
            @click="当前 = 音"
          >
            <div class="行间" style="min-width:0">
              <span :style="{ color: 当前.id === 音.id ? 'var(--主)' : '#475569' }">●</span>
              <span :style="{ color: 当前.id === 音.id ? 'var(--字)' : 'var(--字次)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }">{{ 音.名 }}</span>
            </div>
            <span style="font-size:11px;background:var(--描边);padding:2px 6px;border-radius:4px;color:var(--字次);margin-left:8px">{{ 音.性别 }}</span>
          </div>
        </div>
        <div v-if="!过滤后.length" class="空态" style="padding:32px 0">
          <div>没有匹配的音色</div>
        </div>
      </div>

      <!-- 右：播放器 -->
      <div class="卡片" style="min-height:320px;display:flex;flex-direction:column;align-items:center;justify-content:center">
        <div style="text-align:center;margin-bottom:32px">
          <h2 style="font-size:18px;font-weight:700;color:var(--字);margin:0 0 4px">{{ 当前.名 }}</h2>
          <div style="font-size:12px;color:var(--字弱)">{{ 当前.说明 }}</div>
        </div>

        <div style="display:flex;align-items:center;gap:16px;background:var(--描边);border-radius:999px;padding:12px 24px">
          <i class="el-icon-caret-right" style="font-size:20px;color:var(--字);cursor:pointer"></i>
          <span style="font-size:12px;color:var(--字次);font-family:monospace">0:00 / {{ 当前.时长 }}</span>
          <div style="width:128px;height:4px;background:var(--描边亮);border-radius:999px;overflow:hidden">
            <div style="width:0;height:100%;background:var(--主)"></div>
          </div>
          <i class="el-icon-headset" style="font-size:16px;color:var(--字次);cursor:pointer"></i>
        </div>

        <div class="行间" style="margin-top:32px">
          <el-button size="small" plain @click="试听()">试听示例</el-button>
          <el-button size="small" type="primary" @click="使用()">使用该音色</el-button>
        </div>

        <div style="margin-top:24px;font-size:12px;color:var(--字弱);text-align:center;line-height:1.8">
          <div>语速：中 · 情绪：默认 · 适用语言：中文普通话</div>
          <div>可用于角色配音、旁白与画外音</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 音色列表 } from '../../假数据'

export default {
  name: 'VoiceLib',
  data() {
    return {
      列表: 音色列表,
      分类: '全部',
      关键词: '',
      排序: '全部',
      当前: 音色列表[0]
    }
  },
  computed: {
    分类组() {
      return ['全部', '男声', '女声']
    },
    过滤后() {
      const 词 = this.关键词.trim()
      let 结果 = this.列表.filter(x =>
        (this.分类 === '全部' || x.名.indexOf(this.分类) === 0) &&
        (!词 || x.名.indexOf(词) >= 0)
      )
      if (this.排序 === '最新') 结果 = 结果.slice().reverse()
      return 结果
    }
  },
  methods: {
    试听() {
      this.$message.success('纯前端演示：播放「' + this.当前.名 + '」示例音频')
    },
    使用() {
      this.$message.success('已把「' + this.当前.名 + '」设为当前角色音色')
    },
    上传() {
      this.$message.success('纯前端演示：上传音色未接入后端')
    }
  }
}
</script>
