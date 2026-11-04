<template>
  <div>
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/theater')">梦想剧场</span>
      <span> / </span>
      <span class="可点" @click="$router.push({ path:'/theater/director', query:$route.query })">{{ 剧名 }}</span>
      <span> / </span>
      <span style="color:var(--字次)">短片 · 成片剪辑</span>
    </div>

    <!-- 进度步骤 -->
    <div class="卡片" style="margin-bottom:16px">
      <div class="步骤条" style="margin:0">
        <div class="步 完成"><span class="圈"><i class="el-icon-check"></i></span><span class="字">剧本编辑</span></div>
        <span class="连"></span>
        <div class="步 完成"><span class="圈"><i class="el-icon-check"></i></span><span class="字">分镜与美术资产</span></div>
        <span class="连"></span>
        <div class="步 完成"><span class="圈"><i class="el-icon-check"></i></span><span class="字">导演台</span></div>
        <span class="连"></span>
        <div class="步 当前"><span class="圈">4</span><span class="字">短片</span></div>
      </div>
    </div>

    <div style="display:flex;gap:16px;align-items:flex-start">
      <!-- 左：预览 -->
      <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:16px">
        <div class="卡片 无内距">
          <div style="padding:16px;border-bottom:1px solid var(--描边);display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-size:12px;color:var(--字弱)">当前片段</div>
              <div style="font-size:14px;color:var(--字);font-weight:600">{{ 当前片段.名 }}</div>
            </div>
            <span class="小标签 灰">{{ 当前片段.起 }} - {{ 当前片段.止 }}</span>
          </div>

          <div class="占位图" style="height:320px;border-radius:0;background:linear-gradient(135deg,#2f3a4a,#0f172a)">
            <div style="text-align:center">
              <i class="el-icon-video-play" style="font-size:48px;display:block;margin-bottom:8px"></i>
              <span>原图：成片预览占位</span>
            </div>
          </div>

          <!-- 播放条 -->
          <div style="padding:16px;border-top:1px solid var(--描边);display:flex;align-items:center;gap:16px">
            <i class="el-icon-caret-right" style="font-size:20px;color:var(--字);cursor:pointer"></i>
            <span style="font-size:12px;color:var(--字次);font-family:monospace">{{ 当前片段.起 }} / {{ 当前片段.止 }}</span>
            <el-progress :percentage="进度" :show-text="false" style="flex:1"></el-progress>
            <i class="el-icon-headset" style="font-size:16px;color:var(--字次);cursor:pointer"></i>
          </div>
        </div>

        <!-- 时间线 -->
        <div class="卡片">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:12px;color:var(--字弱)">时间线 · 共 {{ 片段.length }} 个片段</span>
            <span style="font-size:12px;color:var(--字弱)">总时长 01:02</span>
          </div>
          <div style="display:flex;gap:4px">
            <div
              v-for="片 in 片段"
              :key="片.id"
              :style="{ flex: 1, height:'56px', cursor:'pointer', border: 当前片段.id === 片.id ? '2px solid var(--主)' : '1px solid var(--描边)', borderRadius:'6px', background:'linear-gradient(135deg,' + 片.色 + ',#0f172a)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'11px', color:'#64748b' }"
              @click="当前片段 = 片"
            >
              {{ 片.名 }}
            </div>
          </div>
        </div>
      </div>

      <!-- 右：片段列表 -->
      <div style="width:400px;flex:0 0 400px;display:flex;flex-direction:column;gap:16px">
        <div class="卡片">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
            <h2 class="区标题" style="margin:0">片段列表</h2>
            <el-button size="mini" type="primary" @click="合成全部()">合成全部</el-button>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px">
            <div
              v-for="片 in 片段"
              :key="片.id"
              style="display:flex;align-items:center;gap:12px;padding:10px;border:1px solid var(--描边);border-radius:8px;cursor:pointer"
              :style="{ borderColor: 当前片段.id === 片.id ? 'var(--主)' : 'var(--描边)' }"
              @click="当前片段 = 片"
            >
              <div class="占位图" :style="{ width:'64px', height:'40px', flex:'0 0 64px', background:'linear-gradient(135deg,' + 片.色 + ',#0f172a)' }">
                <span style="font-size:11px">封面</span>
              </div>
              <div style="flex:1;min-width:0">
                <div style="font-size:13px;color:var(--字)">{{ 片.名 }}</div>
                <div style="font-size:12px;color:var(--字弱);margin-top:2px">{{ 片.起 }} - {{ 片.止 }}</div>
              </div>
              <el-tag size="mini" :type="片.状态 === '已合成' ? 'success' : (片.状态 === '合成中' ? 'warning' : 'info')">
                {{ 片.状态 }}
              </el-tag>
            </div>
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
            <el-button type="primary" style="width:100%;margin-top:4px" @click="导出()">导出成片</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="行间 右" style="margin-top:16px">
      <el-button @click="上一页()">上一步：导演台</el-button>
      <el-button type="primary" @click="$router.push('/theater')">回到项目列表</el-button>
    </div>
  </div>
</template>

<script>
import { 成片片段 } from '../../假数据'

export default {
  name: 'FilmEdit',
  data() {
    return {
      片段: 成片片段.map(x => Object.assign({}, x)),
      当前片段: null,
      分辨率: '720p',
      比例: '9:16',
      字幕: true,
      配乐: false
    }
  },
  created() {
    this.当前片段 = this.片段[0]
  },
  computed: {
    剧名() {
      return this.$route.query.name || '火影之禁术教师'
    },
    进度() {
      return Math.round((this.片段.filter(x => x.状态 === '已合成').length / this.片段.length) * 100)
    }
  },
  methods: {
    上一页() {
      this.$router.push({ path: '/theater/director', query: this.$route.query })
    },
    合成全部() {
      this.片段.forEach(x => { x.状态 = '已合成' })
      this.$message.success('已提交合成任务，共 ' + this.片段.length + ' 个片段')
    },
    导出() {
      this.$message.success('纯前端演示：导出任务已提交（' + this.分辨率 + ' · ' + this.比例 + '）')
    }
  }
}
</script>
