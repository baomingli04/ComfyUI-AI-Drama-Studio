<template>
  <!-- 一集剧本的完整卡片：目录合同 → 体检 → 合同对照 → 正文场次 → 五个档案块。
       纯展示，所有改动都靠 emit 交给页面处理。 -->
  <div class="剧本卡">
    <!-- ① 卡头：集号 / 标题 / 生成状态 / 幕 -->
    <div class="卡头">
      <div class="头左">
        <span class="集号">第 {{ 集.集 }} 集</span>
        <span class="标题">{{ 集.标题 || '（未命名）' }}</span>
        <span class="态" :class="态类">{{ 态文 }}</span>
        <span class="幕">{{ 集.幕 || '未分幕' }}</span>
      </div>
      <div class="头右">
        <el-button size="mini" @click="$emit('全文')">全文</el-button>
        <el-button size="mini" @click="只看正文 = !只看正文">{{ 只看正文 ? '看档案' : '只看正文' }}</el-button>
        <el-button v-if="剧 && 剧.状态 === '待复核'" size="mini" @click="$emit('复核')">标记已复核</el-button>
        <el-button size="mini" type="primary" plain @click="$emit('重写')">按技能重写本集</el-button>
      </div>
    </div>

    <!-- ② 目录合同：这一集在分集目录里承诺了什么 -->
    <div class="合同">
      <span class="合同签">目录合同</span>
      <span class="合同文">{{ 集.梗概 || '（目录里这一集还没写梗概）' }}</span>
      <span class="合同点">情绪 {{ 集.情绪分 || '—' }}/5</span>
      <span class="合同点">钩：{{ 集.钩子 || '—' }}</span>
    </div>

    <!-- ③ 体检：可演 / 对白 / 场数 / 字数 / 时长，全由正文算 -->
    <div v-if="剧" class="体检">
      <span class="检" :class="检.可演 ? '好' : '差'">可演 {{ 检.可演 ? '✓' : '✗' }}</span>
      <span class="检" :class="检.对白 ? '好' : '差'">对白 {{ 检.对白 ? '✓' : '✗' }}</span>
      <span class="检" :class="检.场数达标 ? '好' : '差'">
        场数 {{ 检.场数 }} 场（建议 {{ 检.建议.少 }}–{{ 检.建议.多 }}，最多 4）
      </span>
      <span class="检">本集 {{ 检.字数 }} 字 · 约 {{ 检.时长 }} 分钟</span>
      <span v-if="剧.缺 && 剧.缺.length" class="检 差">档案缺 {{ 剧.缺.length }} 块</span>
    </div>
    <div v-else class="体检">
      <span class="检">体检：生成后自动算（可演 / 对白 / 场数 / 字数 / 时长）</span>
    </div>

    <!-- ④ 合同对照 -->
    <div class="对照">
      <div class="对照行">
        <span class="k">本集关键词</span>
        <span class="v">{{ 关键词.length ? 关键词.join('、') : '—' }}</span>
      </div>
      <div class="对照行">
        <span class="k">本集卖点</span>
        <span class="v">{{ 卖点 || '—' }}</span>
      </div>
      <div class="对照行">
        <span class="k">前情提要</span>
        <span class="v">{{ 前情 || '—' }}</span>
      </div>
    </div>

    <!-- ⑤ 还没生成 -->
    <div v-if="!剧" class="未生成">
      <div class="未题">第 {{ 集.集 }} 集还没生成剧本</div>
      <div class="未文">上面的「目录合同」就是这一集必须兑现的东西。点右上「按技能重写本集」出一版，出来先给你看解析结果，你点写入才落库。</div>
    </div>

    <!-- ⑥ 正文 -->
    <div v-else class="正文区">
      <div class="区签">
        <span class="区名">正文</span>
        <span class="区注">{{ 检.场数 }} 场 · {{ 检.字数 }} 字</span>
        <div style="flex:1"></div>
        <el-button type="text" size="mini" @click="$emit('新增场')">新增一场</el-button>
      </div>

      <div v-for="(场, 序) in 剧.场们" :key="'场' + 序" class="场卡">
        <div class="场头">
          <span class="场号">{{ 场.场 }}</span>
          <span class="场地">{{ 场.地点 }}</span>
          <div style="flex:1"></div>
          <el-button type="text" size="mini" @click="$emit('编辑场', 场, 序)">编辑</el-button>
        </div>
        <div v-if="场.人物" class="场附"><span class="附k">出场人物</span>{{ 场.人物 }}</div>
        <div v-if="场.道具" class="场附"><span class="附k">出场道具</span>{{ 场.道具 }}</div>
        <div class="场文">
          <div
            v-for="(行, 行序) in 场.正文"
            :key="'行' + 行序"
            :class="{ 动: 是动作(行), 台: 是台词(行) }">{{ 行 }}</div>
        </div>
      </div>

      <!-- 场次没认出来（AI 没按「场次号 · 地点」写）时，正文原样摊开 -->
      <pre v-if="!剧.场们.length" class="原文本">{{ 剧.正文 || '（正文是空的）' }}</pre>
    </div>

    <!-- ⑦ 五个档案块 -->
    <div v-if="剧 && !只看正文" class="档案区">
      <div v-for="块 in 档案块们" :key="块.键" class="档案卡">
        <div class="档案头" @click="切块(块.键)">
          <span class="档案名">{{ 块.名 }}</span>
          <span class="档案注">{{ 块.注 }}</span>
          <span class="档案数">{{ 块数(块.键) }}</span>
          <div style="flex:1"></div>
          <i :class="是开(块.键) ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
        </div>

        <div v-if="是开(块.键)" class="档案体">
          <!-- 行动推荐：编号列表 -->
          <template v-if="块.型 === '列表'">
            <div v-for="(条, 序) in 档值表(块.键)" :key="'推' + 序" class="行动">
              <span class="序号">{{ 序 + 1 }}</span>
              <span class="行动文">{{ 条 }}</span>
            </div>
            <div v-if="!档值表(块.键).length" class="档案空">AI 这一版没给「{{ 块.名 }}」</div>
          </template>

          <!-- 键值块：按字段表顺序铺，两列 -->
          <template v-else>
            <div class="档格">
              <div v-for="k in 块.字段" :key="k" class="档项">
                <div class="档键">{{ k }}</div>
                <div class="档值" :class="{ 空: !档值(块.键, k) }">{{ 档值(块.键, k) || '—' }}</div>
              </div>
            </div>
            <div v-if="余文(块.键)" class="档案余">{{ 余文(块.键) }}</div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 档案块们, 体检剧本, 提关键词, 是动作行, 是台词行 } from '@/共用/剧本档案'

export default {
  name: '剧本卡',
  props: {
    集: { type: Object, required: true },
    剧: { type: Object, default: null },
    前情: { type: String, default: '' },
    卖点: { type: String, default: '' }
  },
  data() {
    return {
      档案块们: 档案块们,
      // 默认全展开：和策划案里贴的那份文档一样，从上到下读完就是这一集的全部信息
      开块: 档案块们.map(function (块) { return 块.键 }),
      只看正文: false
    }
  },
  computed: {
    检() {
      return 体检剧本(this.剧)
    },
    关键词() {
      return 提关键词(this.集)
    },
    态类() {
      if (!this.剧) return '未'
      return this.剧.状态 === '已复核' ? '复核' : '待'
    },
    态文() {
      if (!this.剧) return '未生成'
      const 头 = this.剧.状态 === '已复核' ? '已复核' : '已生成（待复核）'
      return this.剧.时间 ? 头 + ' ' + this.剧.时间 : 头
    }
  },
  methods: {
    是动作(行) { return 是动作行(行) },
    是台词(行) { return 是台词行(行) },
    是开(键) { return this.开块.indexOf(键) >= 0 },
    切块(键) {
      const 位 = this.开块.indexOf(键)
      if (位 >= 0) this.开块.splice(位, 1)
      else this.开块.push(键)
    },
    档值(块键, k) {
      const 块 = (this.剧 && this.剧.档案 && this.剧.档案[块键]) || {}
      return String(块[k] || '')
    },
    档值表(块键) {
      const 值 = (this.剧 && this.剧.档案 && this.剧.档案[块键]) || []
      return Array.isArray(值) ? 值 : []
    },
    余文(块键) {
      return (this.剧 && this.剧.余文 && this.剧.余文[块键]) || ''
    },
    块数(键) {
      const 块 = 档案块们.filter(function (项) { return 项.键 === 键 })[0]
      if (!块) return ''
      if (块.型 === '列表') return this.档值表(键).length + ' 条'
      let 有 = 0
      块.字段.forEach(k => { if (this.档值(键, k)) 有++ })
      return 有 + '/' + 块.字段.length
    }
  }
}
</script>

<style src="./index.css"></style>
