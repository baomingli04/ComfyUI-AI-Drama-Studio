<template>
  <!-- 情绪折线：纯手绘 SVG，不引图表库。
       纵轴 1–5 分，横轴集号，连续两集以上 ≤2 自动标红区（观众掉线警戒）。
       点任意一个点会 emit 点集，页面据此滚到那一集的集卡。 -->
  <div class="情绪折线">
    <svg :viewBox="'0 0 ' + 宽 + ' ' + 高" class="图">
      <!-- 横向网格 + 纵轴刻度 -->
      <g>
        <line
          v-for="刻 in 刻度"
          :key="'线' + 刻.值"
          :x1="内左"
          :y1="刻.y"
          :x2="宽 - 内右"
          :y2="刻.y"
          stroke="#1e293b"
          stroke-width="1"
          :stroke-dasharray="刻.值 === 2 ? '4 3' : '0'"></line>
        <text
          v-for="刻 in 刻度"
          :key="'刻' + 刻.值"
          :x="内左 - 8"
          :y="刻.y + 3.5"
          fill="#64748b"
          font-size="9"
          text-anchor="end">{{ 刻.值 }}</text>
      </g>

      <!-- 连续低谷警戒区 -->
      <rect
        v-for="(段, 序) in 低谷区"
        :key="'警' + 序"
        :x="段.x"
        :y="低谷上"
        :width="段.宽"
        :height="低谷高"
        fill="rgba(239,68,68,0.10)"></rect>

      <defs>
        <linearGradient id="情绪渐变" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#22c55e"></stop>
          <stop offset="100%" stop-color="#22c55e" stop-opacity="0"></stop>
        </linearGradient>
      </defs>
      <polygon :points="面积点" fill="url(#情绪渐变)" opacity="0.28"></polygon>
      <polyline :points="折线点" fill="none" stroke="#22c55e" stroke-width="2" stroke-linejoin="round"></polyline>

      <!-- 数据点：可点，点了滚到那一集。集数太多（>40）就不画点和集号，
           否则 1000 集会糊成一条，只保留趋势线。 -->
      <g v-if="!密集">
        <g
          v-for="(点, 序) in 点们"
          :key="'点' + 序"
          class="数据点"
          @click="$emit('点集', 点.集)">
          <circle :cx="点.x" :cy="点.y" r="11" fill="transparent"></circle>
          <circle :cx="点.x" :cy="点.y" r="4" :fill="点.色" stroke="#0f172a" stroke-width="1.6"></circle>
          <title>EP{{ 点.集 }} {{ 点.标题 }} · 情绪 {{ 点.分 }}</title>
        </g>
      </g>

      <!-- 集号 -->
      <g v-if="!密集">
        <text
          v-for="(点, 序) in 点们"
          :key="'号' + 序"
          :x="点.x"
          :y="高 - 8"
          fill="#64748b"
          font-size="9"
          text-anchor="middle">{{ 点.集 }}</text>
      </g>

      <text
        v-if="低谷区.length"
        :x="宽 - 内右"
        :y="低谷上 - 5"
        fill="#ef4444"
        font-size="9"
        text-anchor="end">连续低谷警戒 ≤2</text>
    </svg>
    <div v-if="!点们.length" class="折线空">还没有情绪分，先给每集打个 1–5 分</div>
  </div>
</template>

<script>
import { 情绪色, 连续低谷 } from '../节奏工具'

export default {
  name: '情绪折线',
  props: {
    集们: { type: Array, default: () => [] },
    宽: { type: Number, default: 680 },
    高: { type: Number, default: 180 }
  },
  data() {
    return {
      内左: 34,
      内右: 16,
      内上: 16,
      内下: 28
    }
  },
  computed: {
    // 只画有情绪分的集，缺分的不占横轴位置
    有效() {
      return (this.集们 || []).filter(集 => typeof 集.情绪分 === 'number')
    },
    // 集数一多就不画点和集号，只留趋势线（1000 集时点会糊成一片）
    密集() {
      return this.有效.length > 40
    },
    刻度() {
      const 表 = []
      for (let 值 = 5; 值 >= 1; 值--) 表.push({ 值: 值, y: this.Y(值) })
      return 表
    },
    点们() {
      const 页 = this
      return this.有效.map(function (集, 序) {
        return {
          x: 页.X(序),
          y: 页.Y(集.情绪分),
          色: 情绪色(集.情绪分),
          集: 集.集,
          分: 集.情绪分,
          标题: 集.标题 || ''
        }
      })
    },
    折线点() {
      return this.点们.map(点 => 点.x.toFixed(1) + ',' + 点.y.toFixed(1)).join(' ')
    },
    面积点() {
      if (!this.点们.length) return ''
      const 底线 = this.Y(1)
      const 尾 = this.点们[this.点们.length - 1].x.toFixed(1)
      return this.内左 + ',' + 底线 + ' ' + this.折线点 + ' ' + 尾 + ',' + 底线
    },
    低谷上() {
      return this.Y(2)
    },
    低谷高() {
      return this.Y(1) - this.Y(2)
    },
    低谷区() {
      const 段们 = 连续低谷(this.有效)
      const 页 = this
      const 序表 = {}
      this.有效.forEach(function (集, 序) { 序表[集.集] = 序 })
      return 段们.map(function (段) {
        const 起序 = 序表[段.起]
        const 止序 = 序表[段.止]
        const 左 = 页.X(起序) - 12
        const 右 = 页.X(止序) + 12
        return { x: 左, 宽: Math.max(右 - 左, 8) }
      })
    }
  },
  methods: {
    X(序) {
      const 内宽 = this.宽 - this.内左 - this.内右
      if (this.有效.length <= 1) return this.内左 + 内宽 / 2
      return this.内左 + 内宽 * 序 / (this.有效.length - 1)
    },
    Y(值) {
      const 内高 = this.高 - this.内上 - this.内下
      return this.内上 + 内高 * (5 - 值) / 4
    }
  }
}
</script>

<style src="./index.css"></style>
