<template>
  <div class="创作模块">
    <div class="页头">
      <div class="左">
        <h1 class="标题">音色库</h1>
        <div class="副题">试听参考站提供的 15 个官方音色，选择适合您角色的声音</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-upload2" @click="上传()">上传我的音色</el-button>
      </div>
    </div>

    <div class="卡片" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div class="行间" style="flex-wrap:wrap">
          <span v-for="类 in 分类组" :key="类" class="chip" :class="{ 选中: 分类 === 类 }" @click="分类 = 类">{{ 类 }}</span>
          <span style="width:12px"></span>
          <el-input v-model="关键词" placeholder="搜索音色..." prefix-icon="el-icon-search" size="small" style="width:200px" clearable />
        </div>
        <div class="行间">
          <span style="font-size:13px;color:var(--字弱)">数量</span>
          <span class="小标签">{{ 过滤后.length }}</span>
        </div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 3fr;gap:24px">
      <div class="卡片" style="padding:8px;align-self:start">
        <div style="display:flex;flex-direction:column;gap:2px">
          <div
            v-for="音 in 过滤后"
            :key="音.id"
            style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:13px"
            :style="{ background: 当前.id === 音.id ? 'var(--描边)' : 'transparent' }"
            @click="切到(音)"
          >
            <div class="行间" style="min-width:0">
              <span :style="{ color: 当前.id === 音.id && 正在播 ? 'var(--主)' : (当前.id === 音.id ? 'var(--字次)' : '#475569') }">●</span>
              <span :style="{ color: 当前.id === 音.id ? 'var(--字)' : 'var(--字次)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }">{{ 音.名 }}</span>
            </div>
            <span style="font-size:11px;background:var(--描边);padding:2px 6px;border-radius:4px;color:var(--字次);margin-left:8px">{{ 音.性别 }}</span>
          </div>
        </div>
        <div v-if="!过滤后.length" class="空态" style="padding:32px 0">
          <div>没有匹配的音色</div>
        </div>
      </div>

      <div class="卡片" style="min-height:320px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px">
        <div style="text-align:center;margin-bottom:24px;width:100%">
          <h2 style="font-size:18px;font-weight:700;color:var(--字);margin:0 0 4px">{{ 当前.名 }}</h2>
          <div style="font-size:12px;color:var(--字弱)">{{ 当前.说明 }}</div>
          <div style="margin-top:8px">
            <span class="小标签" style="margin-right:4px">{{ 当前.年龄段 }}</span>
            <span class="小标签 灰">{{ 当前.风格 }}</span>
          </div>
        </div>

        <audio
          ref="音频"
          :src="当前.文件"
          preload="metadata"
          @timeupdate="同步进度()"
          @ended="播完()"
          @loadedmetadata="元数据就绪()"
          style="display:none"
        ></audio>

        <div style="display:flex;align-items:center;gap:16px;background:var(--描边);border-radius:999px;padding:12px 24px;width:100%;max-width:480px">
          <i
            :class="正在播 ? 'el-icon-video-pause' : 'el-icon-video-play'"
            style="font-size:20px;color:var(--字);cursor:pointer"
            @click="播或停()"
          ></i>
          <span style="font-size:12px;color:var(--字次);font-family:monospace;min-width:80px;text-align:center">{{ 当前时间 }} / {{ 总时长 }}</span>
          <div style="flex:1;height:4px;background:var(--描边亮);border-radius:999px;overflow:hidden;cursor:pointer" @click="跳转($event)">
            <div :style="{ width: 进度 + '%', height: '100%', background: 'var(--主)', transition: 'width .1s' }"></div>
          </div>
          <i class="el-icon-headset" style="font-size:16px;color:var(--字次)"></i>
        </div>

        <div class="行间" style="margin-top:24px">
          <el-button size="small" plain @click="播或停()">{{ 正在播 ? '停止' : '试听示例' }}</el-button>
          <el-button size="small" type="primary" @click="使用()">使用该音色</el-button>
        </div>

        <div style="margin-top:20px;font-size:12px;color:var(--字弱);text-align:center;line-height:1.8">
          <div>语速：中 · 情绪：默认 · 适用语言：中文普通话</div>
          <div>可用于角色配音、旁白与画外音</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 音色列表 } from '../共用/假数据'

export default {
  name: 'VoiceLib',
  data() {
    return {
      列表: 音色列表,
      分类: '全部',
      关键词: '',
      当前: 音色列表[0],
      正在播: false,
      当前时间: '0:00',
      总时长: '0:15',
      进度: 0
    }
  },
  computed: {
    分类组() {
      return ['全部', '男声', '女声']
    },
    过滤后() {
      const 词 = this.关键词.trim()
      return this.列表.filter(x => {
        const 性别匹配 = this.分类 === '全部'
          || (this.分类 === '男声' && x.性别 === '男')
          || (this.分类 === '女声' && x.性别 === '女')
        const 词匹配 = !词 || x.名.indexOf(词) >= 0
        return 性别匹配 && 词匹配
      })
    }
  },
  methods: {
    切到(音) {
      this.当前 = 音
      this.停()
      this.$nextTick(() => {
        if (this.$refs.音频) this.$refs.音频.load()
      })
    },
    播或停() {
      if (!this.$refs.音频) return
      if (this.正在播) {
        this.停()
      } else {
        const p = this.$refs.音频.play()
        if (p && p.catch) p.catch(() => {
          this.$message.warning('浏览器拦截了自动播放，请点页面任意位置后再试')
        })
        this.正在播 = true
      }
    },
    停() {
      if (this.$refs.音频) this.$refs.音频.pause()
      this.正在播 = false
    },
    同步进度() {
      const a = this.$refs.音频
      if (!a || !a.duration) return
      this.当前时间 = this.分秒(a.currentTime)
      this.总时长 = this.分秒(a.duration)
      this.进度 = (a.currentTime / a.duration) * 100
    },
    元数据就绪() {
      const a = this.$refs.音频
      if (a && a.duration) this.总时长 = this.分秒(a.duration)
    },
    播完() {
      this.正在播 = false
      this.进度 = 0
      this.当前时间 = '0:00'
    },
    跳转(e) {
      const a = this.$refs.音频
      if (!a || !a.duration) return
      const r = e.currentTarget.getBoundingClientRect()
      a.currentTime = ((e.clientX - r.left) / r.width) * a.duration
      this.同步进度()
    },
    分秒(s) {
      if (!s || isNaN(s)) return '0:00'
      const m = Math.floor(s / 60)
      const ss = Math.floor(s % 60)
      return m + ':' + (ss < 10 ? '0' : '') + ss
    },
    使用() {
      this.$message.success('已把「' + this.当前.名 + '」设为当前角色音色')
    },
    上传() {
      this.$message.success('纯前端演示：上传音色未接入后端')
    }
  },
  beforeDestroy() {
    this.停()
  }
}
</script>
