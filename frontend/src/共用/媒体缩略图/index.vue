<template>
  <div class="媒体缩略图" v-if="媒体列表 && 媒体列表.length">
    <div
      v-for="(项, i) in 媒体列表"
      :key="i"
      class="缩略块"
      :class="{ '缩略块-大': 大号, '缩略块-自适应': 大号 && 项.类型 === 'image', '缩略块-显全': 显示全 && 项.类型 === 'image' }"
      :title="项.名称"
      @click="$emit('点击', i)"
    >
      <img v-if="项.类型 === 'image'" :src="项.地址" class="缩略图" alt="" />
      <video v-else-if="项.类型 === 'video'" :src="项.地址" class="缩略图" muted preload="metadata"></video>
      <div v-else class="缩略图 音频块">♪</div>
      <span class="缩略标签" v-if="项.角标">{{ 项.角标 }}</span>
      <span class="缩略角标">{{ 项.类型 === 'video' ? '▶' : '' }}</span>
      <!-- 逐条删除：点 × 只删这一条（emit 删除 + 下标），不触发整块点击的放大预览 -->
      <span v-if="可删除" class="缩略删除" title="删除这一条" @click.stop="$emit('删除', i)">×</span>
    </div>
  </div>
  <span v-else class="无媒体">—</span>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
