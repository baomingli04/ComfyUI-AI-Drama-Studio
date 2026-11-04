<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        当前="成片合成"
        :剧名="剧名" :剧id="剧id" :集="集号" :标题="集标题" />

      <div class="剧集主体">
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/video')">视频生成</span>
      <span> / </span>
      <span class="可点" @click="$router.push({ path:'/video/episode', query:$route.query })">{{ 剧名 }} 第 {{ 集号 }} 集</span>
      <span> / </span>
      <span style="color:var(--字次)">合成</span>
    </div>

    <!-- 载入 / 报错门控 -->
    <div v-if="载入中" class="卡片 空场">
      <i class="el-icon-loading" style="font-size:40px;color:var(--字弱)"></i>
      <div class="空注">正在读取本集分镜与正式使用版视频…</div>
    </div>
    <div v-else-if="载入报错" class="卡片 空场">
      <div style="color:var(--警,#e6a23c)">{{ 载入报错 }}</div>
      <el-button size="small" style="margin-top:10px" @click="载入()">重试</el-button>
    </div>

    <div v-else style="display:flex;gap:16px;align-items:flex-start">
      <!-- 左：预览 -->
      <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:16px">
        <div class="卡片 无内距">
          <div style="padding:16px;border-bottom:1px solid var(--描边);display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-size:12px;color:var(--字弱)">当前片段</div>
              <div style="font-size:14px;color:var(--字);font-weight:600">{{ 当前片段 ? 当前片段.镜号 + ' · ' + 当前片段.画面截断 : '还没有可播放的片段' }}</div>
            </div>
            <span v-if="当前片段" class="小标签 灰">{{ 当前片段.方式名 }} · {{ 当前片段.时长文本 }}</span>
          </div>

          <!-- 真视频预览 -->
          <video
            v-if="当前片段 && 当前片段.url"
            :key="当前片段.镜号"
            :src="媒体地址(当前片段.url)"
            controls
            preload="metadata"
            style="width:100%;height:320px;display:block;background:#000"></video>
          <div v-else class="占位图" style="height:320px;border-radius:0;background:linear-gradient(135deg,#2f3a4a,#0f172a)">
            <div style="text-align:center">
              <i class="el-icon-video-play" style="font-size:48px;display:block;margin-bottom:8px"></i>
              <span v-if="片段.length">{{ 片段.length }} 个镜头都还没有「正式使用」的视频，去 单镜生成 页出片并设为正式使用</span>
              <span v-else>本集还没有分镜，先去 拆分分镜 页拆分</span>
            </div>
          </div>

          <!-- 片段信息条 -->
          <div v-if="当前片段" style="padding:12px 16px;border-top:1px solid var(--描边);display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <span style="font-size:12px;color:var(--字次);font-family:monospace">{{ 当前片段.镜号 }}</span>
            <span style="font-size:12px;color:var(--字弱)">{{ 当前片段.画面 }}</span>
          </div>
        </div>

        <!-- 时间线 -->
        <div class="卡片">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:12px;color:var(--字弱)">时间线 · 共 {{ 片段.length }} 个镜头 · 正式使用 {{ 已生成数 }} 个</span>
            <span style="font-size:12px;color:var(--字弱)">总时长 {{ 总时长文本 }}</span>
          </div>
          <div v-if="片段.length" style="display:flex;gap:4px">
            <div
              v-for="片 in 片段"
              :key="片.镜号"
              :style="{ flex: 片.权重, height:'56px', cursor:'pointer', border: 当前镜号 === 片.镜号 ? '2px solid var(--主)' : '1px solid var(--描边)', borderRadius:'6px', background: 片.url ? 'linear-gradient(135deg,#1f7a4d,#0f172a)' : 'linear-gradient(135deg,#3a3f4a,#0f172a)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'11px', color: 片.url ? '#d1fae5' : '#64748b', overflow:'hidden', padding:'0 6px', whiteSpace:'nowrap' }"
              :title="片.镜号 + (片.url ? ' · 正式使用' : ' · 未生成')"
              @click="选片段(片)"
            >
              {{ 片.镜号 }}{{ 片.url ? ' ✓' : '' }}
            </div>
          </div>
          <div v-else style="font-size:12px;color:var(--字弱)">没有分镜</div>
        </div>
      </div>

      <!-- 右：片段列表 -->
      <div style="width:400px;flex:0 0 400px;display:flex;flex-direction:column;gap:16px">
        <div class="卡片">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
            <h2 class="区标题" style="margin:0">片段列表</h2>
            <el-button size="mini" @click="载入()">
              <i class="el-icon-refresh"></i> 刷新
            </el-button>
          </div>

          <div v-if="片段.length" style="display:flex;flex-direction:column;gap:8px">
            <div
              v-for="片 in 片段"
              :key="片.镜号"
              style="display:flex;align-items:center;gap:12px;padding:10px;border:1px solid var(--描边);border-radius:8px;cursor:pointer"
              :style="{ borderColor: 当前镜号 === 片.镜号 ? 'var(--主)' : 'var(--描边)' }"
              @click="选片段(片)"
            >
              <video
                v-if="片.url"
                :src="媒体地址(片.url)"
                preload="metadata"
                :style="{ width:'64px', height:'40px', flex:'0 0 64px', objectFit:'cover', borderRadius:'6px', background:'#000' }"></video>
              <div v-else class="占位图" :style="{ width:'64px', height:'40px', flex:'0 0 64px', borderRadius:'6px', background:'#2a3040' }">
                <i class="el-icon-video-camera" style="font-size:16px;color:var(--字弱)"></i>
              </div>
              <div style="flex:1;min-width:0">
                <div style="font-size:13px;color:var(--字)">{{ 片.镜号 }} · {{ 片.画面截断 }}</div>
                <div style="font-size:12px;color:var(--字弱);margin-top:2px">{{ 片.方式名 }} · {{ 片.时长文本 }}</div>
              </div>
              <el-tag size="mini" :type="片.url ? 'success' : 'info'">
                {{ 片.url ? '正式使用' : '未生成' }}
              </el-tag>
            </div>
          </div>
          <div v-else style="font-size:12px;color:var(--字弱);padding:20px 0;text-align:center">
            本集还没有分镜，先去 拆分分镜 页拆分
          </div>
        </div>

        <!-- 导出设置 -->
        <div class="卡片">
          <h2 class="区标题">导出设置</h2>
          <div style="display:flex;flex-direction:column;gap:12px;font-size:13px">
            <div class="行间" style="justify-content:space-between">
              <span style="color:var(--字次)">分辨率</span>
              <el-select v-model="分辨率" size="mini" style="width:120px">
                <el-option label="720p" value="720p" />
                <el-option label="1080p" value="1080p" />
                <el-option label="480p" value="480p" />
              </el-select>
            </div>
            <div class="行间" style="justify-content:space-between">
              <span style="color:var(--字次)">画面比例</span>
              <div class="行间">
                <span v-for="比 in ['9:16', '16:9', '1:1']" :key="比" class="chip" :class="{ 选中: 比例 === 比 }" @click="比例 = 比">{{ 比 }}</span>
              </div>
            </div>
            <div class="行间" style="justify-content:space-between">
              <span style="color:var(--字次)">字幕</span>
              <el-switch v-model="字幕"></el-switch>
            </div>
            <div class="行间" style="justify-content:space-between">
              <span style="color:var(--字次)">背景音乐</span>
              <el-switch v-model="配乐"></el-switch>
            </div>
            <el-button type="primary" style="width:100%;margin-top:4px" :loading="合成中" @click="合成全部()">合成全部</el-button>
            <div style="font-size:11px;color:var(--字弱);line-height:1.6">
              合成会把本集各镜「正式使用」视频按镜号顺序拼接转码；开启字幕会把各镜台词烧进画面。后台执行，完成后自动刷新列表。
            </div>
          </div>
        </div>

        <!-- 本集成片历史 -->
        <div class="卡片">
          <h2 class="区标题">本集成片</h2>
          <div v-if="成片们.length" style="display:flex;flex-direction:column;gap:10px">
            <div
              v-for="(片, 序) in 成片们"
              :key="片.文件名"
              style="border:1px solid var(--描边);border-radius:8px;padding:10px">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <span style="font-size:12px;color:var(--字)">{{ 序 === 0 ? '最新' : '历史' }} · {{ 片.时间 }}</span>
                <span style="font-size:11px;color:var(--字弱)">{{ (片.大小 / 1048576).toFixed(1) }} MB</span>
                <div style="flex:1"></div>
                <el-button type="text" size="mini" @click="下载成片(片)">下载</el-button>
              </div>
              <video
                :src="媒体地址(片.url)"
                controls
                preload="metadata"
                style="width:100%;border-radius:6px;background:#000"></video>
            </div>
          </div>
          <div v-else style="font-size:12px;color:var(--字弱);padding:12px 0;text-align:center">
            还没合成过成片，点上方「合成全部」
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="行间 右" style="margin-top:16px">
      <el-button @click="上一页()">上一步：单镜生成</el-button>
      <el-button type="primary" @click="$router.push('/video')">回到项目列表</el-button>
    </div>
      </div><!-- /剧集主体 -->
    </div><!-- /剧集布局 -->
  </div>
</template>

<script>
import 剧集侧栏 from '@/共用/剧集侧栏/index.vue'
import { 取, 发 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'

/* 方式键 → 展示名（与 导演台 的 方式表 口径一致） */
const 方式名表 = {
  'd-all': '导演台全能', i2v: '图生视频', t2v: '文生视频', fl2v: '首尾帧',
  r2v: '参考主体', v2v: '视频转视频', rv2v: '参考改视频',
  't8-ref2video': '参考生视频', 'd2-r2v': '多参考生视频', 't10-repaint': '二采重绘'
}

export default {
  name: 'FilmEdit',
  components: { 'ep-rail': 剧集侧栏 },
  data() {
    return {
      载入中: true,
      载入报错: '',
      /* 真库数据 */
      镜们: [],
      版本们: [],
      当前镜号: '',
      /* 成片合成 */
      合成中: false,
      合成轮询器: null,
      成片们: [],
      /* 导出设置（后续粗剪预留） */
      分辨率: '720p',
      比例: '9:16',
      字幕: true,
      配乐: false
    }
  },
  created() {
    this.载入()
  },
  watch: {
    /* 二级侧栏切集是同路由改 query，组件不重建，手动跟 */
    '$route.query.集'() {
      this.载入()
    }
  },
  beforeDestroy() {
    this.停轮询()
  },
  computed: {
    剧名() {
      return this.$route.query.name || ''
    },
    剧id() {
      return parseInt(this.$route.query.ep) || 0
    },
    集号() {
      return parseInt(this.$route.query.集) || 1
    },
    集标题() {
      return this.$route.query.标题 || ''
    },
    /* 片段 = 本集每个分镜一行，视频取该镜「正式使用」（选中=1 且有 url）的版本 */
    片段() {
      const 页 = this
      const 选中表 = {}
      页.版本们.forEach(function (版) {
        if (版.选中 && 版.url) 选中表[版.镜号] = 版
      })
      const 行们 = 页.镜们.map(function (镜) {
        const 版 = 选中表[镜.镜号]
        const 秒 = parseFloat(镜.时长) || 0
        return {
          镜号: 镜.镜号,
          画面: 镜.画面 || '',
          画面截断: (镜.画面 || '（无画面描述）').slice(0, 18),
          台词: 镜.台词 || '',
          url: 版 ? 版.url : '',
          方式名: 版 ? (方式名表[版.方式] || 版.方式 || '—') : '—',
          时长文本: 版 ? (秒 ? 秒 + 's' : '—') : '—',
          权重: Math.max(0.5, Math.min(3, 秒 / 5 || 1))
        }
      })
      return 行们
    },
    当前片段() {
      const 页 = this
      return 页.片段.filter(function (片) { return 片.镜号 === 页.当前镜号 })[0] || null
    },
    已生成数() {
      return this.片段.filter(function (片) { return !!片.url }).length
    },
    总时长文本() {
      const 总 = this.片段.reduce(function (和, 片) {
        const 秒 = parseFloat(片.时长文本) || 0
        return 和 + 秒
      }, 0)
      const 分 = Math.floor(总 / 60)
      const 秒 = Math.round(总 % 60)
      return (分 < 10 ? '0' + 分 : 分) + ':' + (秒 < 10 ? '0' + 秒 : 秒)
    }
  },
  methods: {
    /* 模板里用的媒体地址（带 token 的可播放地址） */
    媒体地址(路径) {
      return 媒体地址(路径)
    },
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.载入报错 = ''
      try {
        const 分镜数据 = await 取('/api/分镜/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.镜们 = (分镜数据 && 分镜数据.分镜们) || []
        const 版本数据 = await 取('/api/分镜/视频?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.版本们 = (版本数据 && 版本数据.版本们) || []
        页.拉成片列表()
        /* 默认选中第一个有正式版且 query 没指定的镜；query 镜 优先 */
        const 指定 = String(页.$route.query.镜 || '').trim()
        const 有 = 页.片段.filter(function (片) { return !!片.url })
        if (指定 && 页.片段.some(function (片) { return 片.镜号 === 指定 })) {
          页.当前镜号 = 指定
        } else if (有.length) {
          页.当前镜号 = 有[0].镜号
        } else if (页.片段.length) {
          页.当前镜号 = 页.片段[0].镜号
        } else {
          页.当前镜号 = ''
        }
      } catch (e) {
        页.载入报错 = '分镜/视频读取失败：' + ((e && e.message) || e)
      }
      页.载入中 = false
    },
    async 拉成片列表() {
      const 页 = this
      try {
        const 数据 = await 取('/api/成片/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.成片们 = (数据 && 数据.成片们) || []
      } catch (e) { /* 成片列表拉不到不阻塞页面 */ }
    },
    选片段(片) {
      this.当前镜号 = 片.镜号
    },
    上一页() {
      this.$router.push({ path: '/video/director', query: this.$route.query })
    },
    /* 异步合成（2026-11-04）：后端建「成片合成」任务后台跑 ffmpeg，这里轮询状态 */
    async 合成全部() {
      const 页 = this
      if (页.合成中) return
      if (!页.已生成数) {
        页.$message.warning('还没有任何「正式使用」的片段，先去 单镜生成 页出片')
        return
      }
      const 缺 = 页.片段.length - 页.已生成数
      try {
        await 页.$confirm(
          '本集 ' + 页.片段.length + ' 个镜头，正式使用 ' + 页.已生成数 + ' 个' +
          (缺 ? '；还有 ' + 缺 + ' 个镜头没有正式使用版，将无法合成（需先补齐）' : '') +
          (页.字幕 ? '；将按各镜台词烧录字幕' : '') +
          '。开始合成？', '合成全部', {
            confirmButtonText: '开始合成', cancelButtonText: '取消', type: 'info'
          })
      } catch (e) { return }
      页.合成中 = true
      try {
        const 数据 = await 发('/api/成片/合成', { 剧id: 页.剧id, 集号: 页.集号, 字幕: 页.字幕 })
        const 任务id = 数据 && 数据.任务id
        if (!任务id) throw new Error('后端未返回任务 id')
        页.$message.info('合成任务已创建，后台执行中…')
        页.轮询合成状态(任务id)
      } catch (e) {
        页.$message.error(((e && e.message) || '创建合成任务失败'))
        页.合成中 = false
      }
    },
    /* 每 2 秒查一次合成任务状态，终态后收尾 */
    轮询合成状态(任务id) {
      const 页 = this
      页.停轮询()
      页.合成轮询器 = setInterval(async function () {
        try {
          const 数据 = await 取('/api/成片/合成状态?任务id=' + 任务id)
          const 态 = 数据 && 数据.状态
          if (态 === '成功') {
            页.停轮询()
            页.合成中 = false
            页.$message.success('成片已合成完成')
            await 页.拉成片列表()
          } else if (态 === '失败' || 态 === '中断') {
            页.停轮询()
            页.合成中 = false
            页.$message.error('合成失败：' + ((数据 && 数据.错误信息) || '未知原因，可到任务页看日志'))
          } else if (态 === '已取消') {
            页.停轮询()
            页.合成中 = false
            页.$message.warning('合成任务已取消')
          }
        } catch (e) { /* 单次轮询失败继续等 */ }
      }, 2000)
    },
    停轮询() {
      if (this.合成轮询器) {
        clearInterval(this.合成轮询器)
        this.合成轮询器 = null
      }
    },
    /* 成片 mp4 拉成 blob 触发浏览器下载 */
    async 下载成片(片) {
      try {
        const 响应 = await fetch(媒体地址(片.url))
        if (!响应.ok) throw new Error('HTTP ' + 响应.status)
        const 地址 = URL.createObjectURL(await 响应.blob())
        const 链 = document.createElement('a')
        链.href = 地址
        链.download = 片.文件名 || '成片.mp4'
        document.body.appendChild(链)
        链.click()
        链.remove()
        URL.revokeObjectURL(地址)
      } catch (e) {
        this.$message.error('下载失败：' + ((e && e.message) || e))
      }
    }
  }
}
</script>
