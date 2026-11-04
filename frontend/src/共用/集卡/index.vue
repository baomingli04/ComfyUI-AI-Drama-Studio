<template>
  <!-- 一张集卡：左侧色条按情绪分着色，头部是旗帜（关键/卡点/低谷/未回收/状态），
       展开后是「出场 / 开场钩子 / 尾钩 / 中心句」四格，底部是钩子点位。
       编辑、打点位、展开收起都 emit 给页面处理，组件自己不存状态。 -->
  <div class="集卡" :class="{ 展开: 展开 }">
    <div class="色条" :style="{ background: 情绪色值 }"></div>
    <div class="卡身">
      <div class="行1">
        <span class="集号">EP{{ 集.集 }}</span>
        <span class="标题">{{ 集.标题 || '（未命名）' }}</span>
        <span v-if="集.关键" class="旗 关键">关键</span>
        <span v-if="集.卡点" class="旗 卡点">付费卡点</span>
        <span v-if="集.情绪分 <= 2" class="旗 卡点">低谷</span>
        <span v-if="未回收" class="旗 卡点" title="这一集有未回收的钩子">● 未回收</span>
        <span class="旗 状态" :class="状态类">{{ 集.状态 }}</span>
        <div class="右">
          <span class="数">{{ 集.字数 || 0 }} 字
            <span :style="{ color: 偏差色 }">{{ 偏差文 }}</span></span>
          <span class="数" :style="{ color: 情绪色值 }">情绪 {{ 集.情绪分 || '-' }}</span>
          <span class="展开钮" @click="$emit('切换')">{{ 展开 ? '收起' : '展开' }}</span>
        </div>
      </div>

      <div class="概">{{ 集.梗概 || '（还没有梗概）' }}</div>

      <div v-if="展开" class="四格">
        <div class="格">
          <div class="格键">出场</div>
          <div class="格值">{{ 出场文 }}</div>
        </div>
        <div class="格">
          <div class="格键">开场钩子</div>
          <div class="格值">{{ 集.钩子 || '—' }}</div>
        </div>
        <div class="格">
          <div class="格键">尾钩</div>
          <div class="格值">{{ 集.尾钩 || '—' }}</div>
        </div>
        <div class="格">
          <div class="格键">中心句</div>
          <div class="格值">{{ 集.中心句 || '—' }}</div>
        </div>
      </div>
      <div v-else class="摘要">
        出场 {{ 出场文 }}<span class="竖">|</span>尾钩「{{ 集.尾钩 || '—' }}」
      </div>

      <div class="点行">
        <span
          v-for="(点, 序) in 集.点位 || []"
          :key="'点' + 序"
          class="点"
          :class="'点-' + 点.类型"
          :title="点.点 + ' ' + 点.内容">{{ 点.类型 }} {{ 点.点 }}</span>
        <span class="点 加" @click="$emit('点位')">+ 打点位</span>
        <span class="点 加 靠右" @click="$emit('编辑')">编辑</span>
      </div>
    </div>
  </div>
</template>

<script>
import { 情绪色 } from '../节奏工具'

export default {
  name: '集卡',
  props: {
    集: { type: Object, required: true },
    展开: { type: Boolean, default: false },
    未回收: { type: Boolean, default: false }
  },
  computed: {
    情绪色值() {
      return 情绪色(this.集.情绪分)
    },
    出场文() {
      const 人 = this.集.出场 || []
      return 人.length ? 人.join(' · ') : '（未填出场）'
    },
    偏差文() {
      const 字数 = Number(this.集.字数) || 0
      const 目标 = Number(this.集.目标) || 0
      if (!目标 || !字数) return '无目标'
      const 比 = Math.round((字数 - 目标) / 目标 * 100)
      if (比 === 0) return '达标'
      return (比 > 0 ? '+' : '') + 比 + '%'
    },
    偏差色() {
      const 字数 = Number(this.集.字数) || 0
      const 目标 = Number(this.集.目标) || 0
      if (!目标 || !字数) return '#64748b'
      const 比 = Math.abs((字数 - 目标) / 目标)
      return 比 > 0.2 ? '#fca5a5' : '#64748b'
    },
    状态类() {
      if (this.集.状态 === '已完成') return '完'
      if (this.集.状态 === '进行中') return '进'
      return '待'
    }
  }
}
</script>

<style src="./index.css"></style>
